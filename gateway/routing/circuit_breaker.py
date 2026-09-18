"""
Circuit breaker for provider fallback — Person A.

Implements a per-provider circuit breaker to automatically fail over
from Anthropic to OpenAI when the primary provider is unhealthy.

State machine (per design decision #3):
  CLOSED  ─(3 consecutive failures)──→  OPEN
  OPEN    ─(30 seconds elapsed)──────→  HALF_OPEN
  HALF_OPEN ─(test request succeeds)──→ CLOSED
  HALF_OPEN ─(test request fails)────→  OPEN (another 30s)

When the breaker is OPEN, route requests to OpenAI instead of Anthropic.
When HALF_OPEN, allow exactly 1 test request to Anthropic.

See: Task 5 in PERSON_A_TASKS.md, design decision #3
"""

import enum
import time
import logging
from typing import Any

import httpx
from fastapi import Request
from fastapi.responses import JSONResponse

from gateway.config import OPENAI_API_KEY

logger = logging.getLogger(__name__)


class CircuitState(enum.Enum):
    CLOSED = "closed"  # Normal — routing to primary provider (Anthropic)
    OPEN = "open"  # Failing over — routing to fallback (OpenAI)
    HALF_OPEN = "half_open"  # Testing — allowing 1 test request to primary


class CircuitBreaker:
    """
    In-memory circuit breaker for a single provider.

    Thread-safe for single-process async usage (Python GIL).
    In a multi-worker deployment, each worker has its own breaker state.
    This is acceptable for hackathon scope (design decision #3 note).
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
        self._half_open_in_progress = False

    def should_route_to_fallback(self) -> bool:
        """
        Determine if requests should be routed to the fallback provider.

        Returns True when:
        - Breaker is OPEN (always route to fallback)
        - Breaker is HALF_OPEN but a test request is already in progress

        Returns False when:
        - Breaker is CLOSED (route to primary)
        - Breaker is HALF_OPEN and no test request is in progress (allow one)

        Also handles the OPEN → HALF_OPEN transition when the recovery
        timeout has elapsed.
        """
        if self.state == CircuitState.CLOSED:
            return False

        if self.state == CircuitState.OPEN:
            # Check if recovery timeout has elapsed → transition to HALF_OPEN
            if self.last_failure_time is not None:
                elapsed = time.time() - self.last_failure_time
                if elapsed >= self.recovery_timeout:
                    logger.info(
                        f"Circuit breaker: OPEN → HALF_OPEN "
                        f"(recovery timeout {self.recovery_timeout}s elapsed)"
                    )
                    self.state = CircuitState.HALF_OPEN
                    self._half_open_in_progress = True
                    return False  # Allow the test request
            return True  # Still in OPEN, route to fallback

        if self.state == CircuitState.HALF_OPEN:
            if self._half_open_in_progress:
                # Another test request is already in flight
                return True
            # Allow this one test request through
            self._half_open_in_progress = True
            return False

        return False  # Default: route to primary

    def record_success(self) -> None:
        """
        Record a successful provider call.

        Transitions:
        - HALF_OPEN → CLOSED (test passed, resume normal routing)
        - CLOSED → stays CLOSED (reset failure count)
        """
        if self.state == CircuitState.HALF_OPEN:
            logger.info("Circuit breaker: HALF_OPEN → CLOSED (test succeeded)")
            self.state = CircuitState.CLOSED
            self.failure_count = 0
            self.last_failure_time = None
            self._half_open_in_progress = False
        elif self.state == CircuitState.CLOSED:
            # Reset consecutive failure count on success
            self.failure_count = 0

    def record_failure(self) -> None:
        """
        Record a failed provider call (5xx or timeout).

        Transitions:
        - CLOSED → OPEN (after reaching failure_threshold)
        - HALF_OPEN → OPEN (test failed, reopen for another recovery_timeout)
        """
        self.failure_count += 1
        self.last_failure_time = time.time()

        if self.state == CircuitState.HALF_OPEN:
            logger.warning("Circuit breaker: HALF_OPEN → OPEN (test request failed)")
            self.state = CircuitState.OPEN
            self._half_open_in_progress = False
            return

        if self.state == CircuitState.CLOSED:
            if self.failure_count >= self.failure_threshold:
                logger.warning(
                    f"Circuit breaker: CLOSED → OPEN "
                    f"({self.failure_count} consecutive failures)"
                )
                self.state = CircuitState.OPEN

    def reset(self) -> None:
        """Reset the circuit breaker back to initial CLOSED state."""
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.last_failure_time = None
        self._half_open_in_progress = False

    def get_status(self) -> dict[str, Any]:
        """Return the current circuit breaker state for diagnostics."""
        return {
            "state": self.state.value,
            "failure_count": self.failure_count,
            "failure_threshold": self.failure_threshold,
            "recovery_timeout": self.recovery_timeout,
            "last_failure_time": self.last_failure_time,
        }


# ──────────────────────────────────────────────
# Global circuit breaker instance for Anthropic
# ──────────────────────────────────────────────
anthropic_breaker = CircuitBreaker(failure_threshold=3, recovery_timeout=30.0)


# ──────────────────────────────────────────────
# OpenAI passthrough for fallback
# ──────────────────────────────────────────────

OPENAI_API_URL = "https://api.openai.com/v1/chat/completions"


async def call_openai_fallback(
    request: Request,
    openai_payload: dict,
) -> JSONResponse:
    """
    Passthrough to OpenAI when the Anthropic circuit breaker is OPEN.

    Since our gateway's public API is already OpenAI-shaped, this is
    mostly a passthrough — we forward the request as-is and return
    the response as-is.

    Args:
        request: The FastAPI request.
        openai_payload: The original OpenAI-format request from the client.

    Returns:
        JSONResponse with the OpenAI response.
    """
    if not OPENAI_API_KEY:
        logger.error("OpenAI fallback requested but OPENAI_API_KEY is not configured")
        return JSONResponse(
            content={
                "error": {
                    "message": (
                        "Primary provider is unavailable and fallback "
                        "provider is not configured."
                    ),
                    "type": "server_error",
                    "code": "fallback_unavailable",
                }
            },
            status_code=503,
        )

    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json",
    }

    # Ensure stream is False for non-streaming fallback
    openai_payload["stream"] = False

    timeout = httpx.Timeout(connect=10.0, read=120.0, write=10.0, pool=10.0)

    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(
                OPENAI_API_URL,
                headers=headers,
                json=openai_payload,
            )

            response_data = response.json()

            if response.status_code != 200:
                logger.warning(f"OpenAI fallback error: status={response.status_code}")
                return JSONResponse(
                    content=response_data,
                    status_code=response.status_code,
                )

            # Add aperture metadata
            response_data["_aperture"] = {
                "request_id": getattr(request.state, "request_id", "unknown"),
                "provider": "openai",
                "fallback": True,
            }

            return JSONResponse(content=response_data)

    except httpx.ConnectError:
        logger.error("Failed to connect to OpenAI (fallback)")
        return JSONResponse(
            content={
                "error": {
                    "message": "Failed to connect to fallback provider.",
                    "type": "server_error",
                    "code": "fallback_unreachable",
                }
            },
            status_code=502,
        )
    except httpx.TimeoutException:
        logger.error("Timeout calling OpenAI (fallback)")
        return JSONResponse(
            content={
                "error": {
                    "message": "Fallback provider request timed out.",
                    "type": "server_error",
                    "code": "fallback_timeout",
                }
            },
            status_code=504,
        )
    except Exception as e:
        logger.exception(f"Unexpected error calling OpenAI fallback: {e}")
        return JSONResponse(
            content={
                "error": {
                    "message": "Internal gateway error during fallback.",
                    "type": "server_error",
                    "code": "internal_error",
                }
            },
            status_code=500,
        )
