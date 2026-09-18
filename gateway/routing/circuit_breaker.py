"""
Circuit breaker for provider fallback — Person A (YOU).

Implements a per-provider circuit breaker to automatically fail over
from Anthropic to OpenAI when the primary provider is unhealthy.

Per design decision #3:
- Trip after 3 consecutive failures (5xx or timeout)
- Stay open for 30 seconds
- Half-open: allow 1 test request, close on success, reopen on failure

See: Task 5 in PERSON_A_TASKS.md
"""
import enum
import time


class CircuitState(enum.Enum):
    CLOSED = "closed"        # Normal — routing to primary provider
    OPEN = "open"            # Failing over — routing to fallback provider
    HALF_OPEN = "half_open"  # Testing — allowing 1 test request to primary


class CircuitBreaker:
    """
    In-memory circuit breaker for a single provider.

    TODO (Task 5):
    - Track consecutive failure count
    - Implement state transitions (CLOSED->OPEN->HALF_OPEN->CLOSED)
    - Expose should_route_to_fallback() for the main routing logic
    - Record success/failure after each provider call
    """

    def __init__(
        self,
        failure_threshold: int = 3,
        recovery_timeout: float = 30.0,
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.last_failure_time: float | None = None

    def should_route_to_fallback(self) -> bool:
        """Return True if the breaker is open and requests should go to fallback."""
        raise NotImplementedError("Task 5 — implement circuit breaker logic")

    def record_success(self) -> None:
        """Record a successful provider call."""
        raise NotImplementedError("Task 5 — implement circuit breaker logic")

    def record_failure(self) -> None:
        """Record a failed provider call."""
        raise NotImplementedError("Task 5 — implement circuit breaker logic")
