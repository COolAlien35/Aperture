"""
Unit tests for the circuit breaker state machine.

Tests cover:
- CLOSED → OPEN transition after N failures
- OPEN → HALF_OPEN transition after recovery timeout
- HALF_OPEN → CLOSED on success
- HALF_OPEN → OPEN on failure
- Success resets failure count
- Diagnostics/status reporting
"""

import time
from unittest.mock import patch

import pytest
from gateway.routing.circuit_breaker import CircuitBreaker, CircuitState


class TestCircuitBreakerTransitions:
    """Tests for the circuit breaker state machine."""

    def test_starts_closed(self):
        """New circuit breaker starts in CLOSED state."""
        cb = CircuitBreaker()
        assert cb.state == CircuitState.CLOSED
        assert cb.failure_count == 0
        assert cb.should_route_to_fallback() is False

    def test_closed_to_open_after_threshold(self):
        """Breaker trips to OPEN after failure_threshold consecutive failures."""
        cb = CircuitBreaker(failure_threshold=3)

        cb.record_failure()
        assert cb.state == CircuitState.CLOSED
        assert cb.failure_count == 1

        cb.record_failure()
        assert cb.state == CircuitState.CLOSED
        assert cb.failure_count == 2

        cb.record_failure()
        assert cb.state == CircuitState.OPEN
        assert cb.failure_count == 3
        assert cb.should_route_to_fallback() is True

    def test_success_resets_failure_count(self):
        """A success in CLOSED state resets the consecutive failure count."""
        cb = CircuitBreaker(failure_threshold=3)

        cb.record_failure()
        cb.record_failure()
        assert cb.failure_count == 2

        cb.record_success()
        assert cb.failure_count == 0
        assert cb.state == CircuitState.CLOSED

    def test_open_routes_to_fallback(self):
        """OPEN state always routes to fallback."""
        cb = CircuitBreaker(failure_threshold=1, recovery_timeout=30.0)
        cb.record_failure()  # Trip to OPEN
        assert cb.state == CircuitState.OPEN
        assert cb.should_route_to_fallback() is True

    def test_open_to_half_open_after_timeout(self):
        """OPEN → HALF_OPEN after recovery_timeout elapses."""
        cb = CircuitBreaker(failure_threshold=1, recovery_timeout=1.0)
        cb.record_failure()  # Trip to OPEN
        assert cb.state == CircuitState.OPEN

        # Simulate time passing beyond recovery timeout
        cb.last_failure_time = time.time() - 2.0  # 2s ago, timeout is 1s

        assert cb.should_route_to_fallback() is False  # Triggers transition
        assert cb.state == CircuitState.HALF_OPEN

    def test_half_open_allows_one_test_request(self):
        """HALF_OPEN allows exactly one test request, then routes to fallback."""
        cb = CircuitBreaker(failure_threshold=1, recovery_timeout=60.0)
        cb.record_failure()  # Trip to OPEN
        assert cb.state == CircuitState.OPEN

        # Force into HALF_OPEN by simulating timeout expiry
        cb.last_failure_time = time.time() - 61.0  # 61s ago, timeout is 60s

        # First call: should transition to HALF_OPEN and allow
        assert cb.should_route_to_fallback() is False
        assert cb.state == CircuitState.HALF_OPEN

        # Second call while test is in progress: route to fallback
        assert cb.should_route_to_fallback() is True

    def test_half_open_to_closed_on_success(self):
        """HALF_OPEN → CLOSED when the test request succeeds."""
        cb = CircuitBreaker(failure_threshold=1, recovery_timeout=0.0)
        cb.record_failure()

        # Force into HALF_OPEN
        cb.last_failure_time = time.time() - 1.0
        cb.should_route_to_fallback()  # Transition to HALF_OPEN
        assert cb.state == CircuitState.HALF_OPEN

        cb.record_success()
        assert cb.state == CircuitState.CLOSED
        assert cb.failure_count == 0
        assert cb.should_route_to_fallback() is False

    def test_half_open_to_open_on_failure(self):
        """HALF_OPEN → OPEN when the test request fails."""
        cb = CircuitBreaker(failure_threshold=1, recovery_timeout=0.0)
        cb.record_failure()

        # Force into HALF_OPEN
        cb.last_failure_time = time.time() - 1.0
        cb.should_route_to_fallback()  # Transition to HALF_OPEN
        assert cb.state == CircuitState.HALF_OPEN

        cb.record_failure()
        assert cb.state == CircuitState.OPEN

    def test_custom_thresholds(self):
        """Custom failure_threshold and recovery_timeout work correctly."""
        cb = CircuitBreaker(failure_threshold=5, recovery_timeout=60.0)

        for i in range(4):
            cb.record_failure()
            assert cb.state == CircuitState.CLOSED

        cb.record_failure()
        assert cb.state == CircuitState.OPEN

    def test_get_status(self):
        """get_status returns correct diagnostics."""
        cb = CircuitBreaker(failure_threshold=3, recovery_timeout=30.0)
        status = cb.get_status()

        assert status["state"] == "closed"
        assert status["failure_count"] == 0
        assert status["failure_threshold"] == 3
        assert status["recovery_timeout"] == 30.0
        assert status["last_failure_time"] is None

    def test_get_status_after_failure(self):
        """get_status reflects failures."""
        cb = CircuitBreaker(failure_threshold=3)
        cb.record_failure()
        status = cb.get_status()

        assert status["failure_count"] == 1
        assert status["last_failure_time"] is not None


class TestCircuitBreakerIntegration:
    """Integration-style tests for realistic circuit breaker scenarios."""

    def test_full_lifecycle(self):
        """
        Full lifecycle: CLOSED → fail 3x → OPEN → wait → HALF_OPEN
        → success → CLOSED.
        """
        cb = CircuitBreaker(failure_threshold=3, recovery_timeout=0.0)

        # Normal operation
        assert cb.state == CircuitState.CLOSED
        cb.record_success()
        cb.record_success()

        # Start failing
        cb.record_failure()
        cb.record_failure()
        cb.record_failure()
        assert cb.state == CircuitState.OPEN

        # Wait for recovery
        cb.last_failure_time = time.time() - 1.0
        assert cb.should_route_to_fallback() is False  # → HALF_OPEN
        assert cb.state == CircuitState.HALF_OPEN

        # Test request succeeds
        cb.record_success()
        assert cb.state == CircuitState.CLOSED

        # Normal operation resumes
        assert cb.should_route_to_fallback() is False

    def test_intermittent_failures_dont_trip(self):
        """Non-consecutive failures don't trip the breaker."""
        cb = CircuitBreaker(failure_threshold=3)

        cb.record_failure()
        cb.record_failure()
        cb.record_success()  # Resets count
        cb.record_failure()
        cb.record_failure()
        cb.record_success()  # Resets count

        assert cb.state == CircuitState.CLOSED
        assert cb.failure_count == 0
