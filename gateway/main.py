"""
Aperture Gateway — FastAPI application entrypoint.

This is the universal AI gateway that accepts OpenAI-compatible requests
and routes them to upstream LLM providers (Anthropic, OpenAI).

Request pipeline order:
1. request_id generation (here, before any middleware)
2. auth_middleware (Person B)
3. budget_check_middleware (Person B)
4. translator + router (Person A)
5. Reconciliation (Person B hook)
6. Kafka usage event (Person C, fire-and-forget)

See: PRD section 5.1, architecture diagram
"""

import uuid
import time
import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from gateway.middleware.auth import auth_middleware
from gateway.middleware.budget import budget_check_middleware
from gateway.models import ChatCompletionRequest
from gateway.routing.translator import (
    translate_request_to_anthropic,
    translate_error_from_anthropic,
)
from gateway.routing.streaming import (
    call_anthropic_non_streaming,
    call_anthropic_streaming,
)
from gateway.routing.circuit_breaker import (
    anthropic_breaker,
    call_openai_fallback,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Aperture AI Gateway",
    description="Enterprise AI Gateway & Spend Management Platform",
    version="0.1.0",
)


# ──────────────────────────────────────────────
# Middleware: request_id generation
# Per design decision #8 — generated ONCE at request start,
# before auth or budget middleware, so retries/reconciliation
# share the same ID.
#
# B and C: read this from request.state.request_id
# ──────────────────────────────────────────────
@app.middleware("http")
async def add_request_id(request: Request, call_next):
    request.state.request_id = str(uuid.uuid4())
    request.state.start_time = time.time()
    response = await call_next(request)
    response.headers["X-Request-ID"] = request.state.request_id

    # Add latency header for observability
    latency_ms = (time.time() - request.state.start_time) * 1000
    response.headers["X-Latency-Ms"] = f"{latency_ms:.1f}"

    return response


# ──────────────────────────────────────────────
# Health check — for Docker healthchecks and manual testing
# ──────────────────────────────────────────────
@app.get("/health")
async def health():
    return {
        "status": "ok",
        "circuit_breaker": anthropic_breaker.get_status(),
    }


# ──────────────────────────────────────────────
# Main endpoint — OpenAI-compatible chat completions
# PRD 5.1: Universal API Endpoint
# ──────────────────────────────────────────────
@app.post("/v1/chat/completions")
async def chat_completions(request: Request):
    """
    OpenAI-compatible chat completions endpoint.

    Full pipeline:
    1. request_id already set by middleware above
    2. Auth middleware (Person B) — resolves identity
    3. Budget check middleware (Person B) — reserves estimated cost
    4. Circuit breaker check — route to Anthropic or OpenAI fallback
    5. Translate to provider format, call provider, translate response
    6. Reconciliation (Person B hook, in streaming.py finally block)
    7. Publish usage event to Kafka (Person C) — fire-and-forget
    """
    # ── Step 2: Auth (Person B's stub — always passes for now) ──
    request = await auth_middleware(request)

    # ── Step 3: Budget check (Person B's stub — always allows for now) ──
    request = await budget_check_middleware(request)

    # ── Step 4: Parse and validate the request body ──
    try:
        body = await request.json()
        chat_request = ChatCompletionRequest(**body)
    except Exception as e:
        logger.warning(f"Invalid request body: {e}")
        return JSONResponse(
            content={
                "error": {
                    "message": f"Invalid request: {str(e)}",
                    "type": "invalid_request_error",
                    "code": "invalid_request",
                }
            },
            status_code=400,
        )

    original_model = chat_request.model
    is_streaming = chat_request.stream

    # ── Step 5: Circuit breaker check ──
    if anthropic_breaker.should_route_to_fallback():
        logger.info(
            f"Circuit breaker OPEN — routing to OpenAI fallback "
            f"(request_id={request.state.request_id})"
        )
        # OpenAI fallback: the request is already in OpenAI format,
        # so we pass it through directly.
        response = await call_openai_fallback(request, body)

        # Record success/failure for the fallback too
        # (though we don't circuit-break OpenAI in this version)
        return response

    # ── Step 6: Translate to Anthropic format ──
    try:
        anthropic_payload = translate_request_to_anthropic(body)
    except ValueError as e:
        logger.warning(f"Translation error: {e}")
        return JSONResponse(
            content={
                "error": {
                    "message": str(e),
                    "type": "invalid_request_error",
                    "code": "invalid_model",
                }
            },
            status_code=400,
        )

    # ── Step 7: Call Anthropic (streaming or non-streaming) ──
    try:
        if is_streaming:
            response = await call_anthropic_streaming(
                request, anthropic_payload, original_model
            )
            return response
        else:
            response = await call_anthropic_non_streaming(
                request, anthropic_payload, original_model
            )

            # Record success/failure based on response status
            if response.status_code == 200:
                anthropic_breaker.record_success()
            elif response.status_code >= 500:
                anthropic_breaker.record_failure()
                logger.warning(
                    f"Anthropic returned {response.status_code}, "
                    f"failure count: {anthropic_breaker.failure_count}"
                )

            return response

    except Exception as e:
        # Provider call failed entirely — record failure
        anthropic_breaker.record_failure()
        logger.exception(
            f"Provider call failed: {e}. "
            f"Circuit breaker failure count: {anthropic_breaker.failure_count}"
        )
        return JSONResponse(
            content={
                "error": {
                    "message": "Internal gateway error.",
                    "type": "server_error",
                    "code": "internal_error",
                }
            },
            status_code=500,
        )
