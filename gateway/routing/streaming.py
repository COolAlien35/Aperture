"""
SSE streaming passthrough — Person A.

Handles both streaming and non-streaming calls to Anthropic's API.
Translates Anthropic SSE chunks to OpenAI's streaming format in real-time.

Tracks running token count for partial-disconnect reconciliation
(design decision #6).

Streaming event mapping (Anthropic → OpenAI):
  - message_start     → chat.completion.chunk with role
  - content_block_delta → chat.completion.chunk with content delta
  - message_delta     → chat.completion.chunk with finish_reason
  - message_stop      → [DONE]

See: Task 4 in PERSON_A_TASKS.md
"""

import json
import time
import uuid
import logging
from typing import Any, AsyncGenerator

import httpx
from fastapi import Request
from fastapi.responses import StreamingResponse, JSONResponse

from gateway.config import ANTHROPIC_API_KEY
from gateway.routing.translator import (
    translate_response_from_anthropic,
    translate_error_from_anthropic,
)
from gateway.events.producer import publish_usage_event

logger = logging.getLogger(__name__)

# Anthropic API base URL
ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages"
ANTHROPIC_VERSION = "2023-06-01"

# Timeout settings for httpx
CONNECT_TIMEOUT = 10.0      # seconds to establish connection
READ_TIMEOUT = 120.0        # seconds to wait for streaming data
WRITE_TIMEOUT = 10.0        # seconds for sending request


def _get_anthropic_headers() -> dict[str, str]:
    """Build the required headers for the Anthropic API."""
    return {
        "x-api-key": ANTHROPIC_API_KEY,
        "anthropic-version": ANTHROPIC_VERSION,
        "content-type": "application/json",
    }


def _estimate_tokens_from_text(text: str) -> int:
    """
    Rough token estimation from text.

    Uses a simple heuristic: ~4 characters per token on average for English.
    This is a conservative estimate used for partial-disconnect reconciliation
    when we don't have an accurate count from the provider.

    For production, use tiktoken for accurate counts.
    """
    if not text:
        return 0
    return max(1, len(text) // 4)


async def call_anthropic_non_streaming(
    request: Request,
    anthropic_payload: dict,
    original_model: str,
) -> JSONResponse:
    """
    Make a non-streaming call to Anthropic and return an OpenAI-format response.

    Args:
        request: The FastAPI request (for reading request.state).
        anthropic_payload: The translated Anthropic-format request body.
        original_model: The model name the client originally requested.

    Returns:
        JSONResponse with OpenAI-format chat.completion body.
    """
    # Ensure stream is False
    anthropic_payload["stream"] = False

    timeout = httpx.Timeout(
        connect=CONNECT_TIMEOUT,
        read=READ_TIMEOUT,
        write=WRITE_TIMEOUT,
        pool=10.0,
    )

    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(
                ANTHROPIC_API_URL,
                headers=_get_anthropic_headers(),
                json=anthropic_payload,
            )

            response_data = response.json()

            # ── Handle Anthropic errors ──
            if response.status_code != 200:
                logger.warning(
                    f"Anthropic API error: status={response.status_code} "
                    f"body={response_data}"
                )
                error_body, error_status = translate_error_from_anthropic(
                    response_data, response.status_code
                )

                # Fire usage event with error status
                await _publish_event_safe(
                    request=request,
                    original_model=original_model,
                    prompt_tokens=0,
                    completion_tokens=0,
                    status="error",
                )

                return JSONResponse(
                    content=error_body,
                    status_code=error_status,
                )

            # ── Translate successful response ──
            openai_response = translate_response_from_anthropic(
                response_data, original_model
            )

            # Include request_id in response
            openai_response["_aperture"] = {
                "request_id": getattr(request.state, "request_id", "unknown"),
            }

            # Fire usage event — fire-and-forget (design decision #7)
            usage = openai_response.get("usage", {})
            await _publish_event_safe(
                request=request,
                original_model=original_model,
                prompt_tokens=usage.get("prompt_tokens", 0),
                completion_tokens=usage.get("completion_tokens", 0),
                status="success",
            )

            return JSONResponse(content=openai_response)

    except httpx.ConnectError as e:
        logger.error(f"Failed to connect to Anthropic: {e}")
        return JSONResponse(
            content={
                "error": {
                    "message": "Failed to connect to LLM provider.",
                    "type": "server_error",
                    "code": "provider_unreachable",
                }
            },
            status_code=502,
        )
    except httpx.TimeoutException as e:
        logger.error(f"Timeout calling Anthropic: {e}")
        return JSONResponse(
            content={
                "error": {
                    "message": "LLM provider request timed out.",
                    "type": "server_error",
                    "code": "provider_timeout",
                }
            },
            status_code=504,
        )
    except Exception as e:
        logger.exception(f"Unexpected error calling Anthropic: {e}")
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


async def call_anthropic_streaming(
    request: Request,
    anthropic_payload: dict,
    original_model: str,
) -> StreamingResponse:
    """
    Make a streaming call to Anthropic and return an OpenAI-format SSE stream.

    Translates Anthropic SSE events to OpenAI streaming chunk format in
    real-time. Tracks a running token count on request.state for
    partial-disconnect reconciliation (design decision #6).

    Args:
        request: The FastAPI request (for reading/writing request.state).
        anthropic_payload: The translated Anthropic-format request body.
        original_model: The model name the client originally requested.

    Returns:
        StreamingResponse that yields OpenAI-format SSE events.
    """
    # Ensure stream is True
    anthropic_payload["stream"] = True

    # Initialize running token counter on request state
    request.state.tokens_streamed_so_far = 0
    request.state.prompt_tokens = 0

    response_id = f"chatcmpl-{uuid.uuid4().hex[:12]}"

    async def event_generator() -> AsyncGenerator[str, None]:
        """
        Async generator that:
        1. Opens a streaming connection to Anthropic
        2. Translates each SSE event to OpenAI format
        3. Tracks running token count
        4. Handles all three termination cases
        """
        completion_tokens = 0
        prompt_tokens = 0
        finish_reason = None
        stream_status = "success"

        try:
            timeout = httpx.Timeout(
                connect=CONNECT_TIMEOUT,
                read=READ_TIMEOUT,
                write=WRITE_TIMEOUT,
                pool=10.0,
            )

            async with httpx.AsyncClient(timeout=timeout) as client:
                async with client.stream(
                    "POST",
                    ANTHROPIC_API_URL,
                    headers=_get_anthropic_headers(),
                    json=anthropic_payload,
                ) as response:

                    # ── Handle non-200 responses ──
                    if response.status_code != 200:
                        if response.status_code >= 500:
                            from gateway.routing.circuit_breaker import anthropic_breaker
                            anthropic_breaker.record_failure()
                        body = await response.aread()
                        try:
                            error_data = json.loads(body)
                        except json.JSONDecodeError:
                            error_data = {
                                "error": {
                                    "type": "api_error",
                                    "message": body.decode("utf-8", errors="replace"),
                                }
                            }

                        error_body, _ = translate_error_from_anthropic(
                            error_data, response.status_code
                        )

                        # Yield error as SSE event
                        error_chunk = {
                            "id": response_id,
                            "object": "chat.completion.chunk",
                            "created": int(time.time()),
                            "model": original_model,
                            "choices": [
                                {
                                    "index": 0,
                                    "delta": {},
                                    "finish_reason": "error",
                                }
                            ],
                            "_error": error_body.get("error", {}),
                        }
                        yield f"data: {json.dumps(error_chunk)}\n\n"
                        yield "data: [DONE]\n\n"
                        stream_status = "error"
                        return

                    # ── Process SSE events ──
                    current_event_type = None
                    async for line in response.aiter_lines():
                        line = line.strip()

                        # SSE event type line
                        if line.startswith("event:"):
                            current_event_type = line[6:].strip()
                            continue

                        # SSE data line
                        if not line.startswith("data:"):
                            continue

                        data_str = line[5:].strip()
                        if not data_str:
                            continue

                        try:
                            data = json.loads(data_str)
                        except json.JSONDecodeError:
                            logger.warning(
                                f"Failed to parse SSE data: {data_str[:100]}"
                            )
                            continue

                        event_type = (
                            data.get("type") or current_event_type or ""
                        )

                        # ── message_start ──
                        # First event: contains role and usage info
                        if event_type == "message_start":
                            message = data.get("message", {})
                            usage = message.get("usage", {})
                            prompt_tokens = usage.get("input_tokens", 0)
                            request.state.prompt_tokens = prompt_tokens

                            chunk = {
                                "id": response_id,
                                "object": "chat.completion.chunk",
                                "created": int(time.time()),
                                "model": original_model,
                                "choices": [
                                    {
                                        "index": 0,
                                        "delta": {"role": "assistant"},
                                        "finish_reason": None,
                                    }
                                ],
                            }
                            yield f"data: {json.dumps(chunk)}\n\n"

                        # ── content_block_delta ──
                        # Content chunks — the actual streamed text
                        elif event_type == "content_block_delta":
                            delta = data.get("delta", {})
                            text = delta.get("text", "")

                            if text:
                                # Track running token count
                                estimated = _estimate_tokens_from_text(text)
                                completion_tokens += estimated
                                request.state.tokens_streamed_so_far = (
                                    completion_tokens
                                )

                                chunk = {
                                    "id": response_id,
                                    "object": "chat.completion.chunk",
                                    "created": int(time.time()),
                                    "model": original_model,
                                    "choices": [
                                        {
                                            "index": 0,
                                            "delta": {"content": text},
                                            "finish_reason": None,
                                        }
                                    ],
                                }
                                yield f"data: {json.dumps(chunk)}\n\n"

                        # ── message_delta ──
                        # Final message update with stop reason and usage
                        elif event_type == "message_delta":
                            delta = data.get("delta", {})
                            usage = data.get("usage", {})

                            stop_reason = delta.get("stop_reason", "end_turn")
                            from gateway.routing.translator import (
                                STOP_REASON_MAP,
                            )
                            finish_reason = STOP_REASON_MAP.get(
                                stop_reason, "stop"
                            )

                            # Use accurate output tokens from the final event
                            if usage.get("output_tokens"):
                                completion_tokens = usage["output_tokens"]
                                request.state.tokens_streamed_so_far = (
                                    completion_tokens
                                )

                            chunk = {
                                "id": response_id,
                                "object": "chat.completion.chunk",
                                "created": int(time.time()),
                                "model": original_model,
                                "choices": [
                                    {
                                        "index": 0,
                                        "delta": {},
                                        "finish_reason": finish_reason,
                                    }
                                ],
                                "usage": {
                                    "prompt_tokens": prompt_tokens,
                                    "completion_tokens": completion_tokens,
                                    "total_tokens": (
                                        prompt_tokens + completion_tokens
                                    ),
                                },
                            }
                            yield f"data: {json.dumps(chunk)}\n\n"

                        # ── message_stop ──
                        # Stream is done
                        elif event_type == "message_stop":
                            yield "data: [DONE]\n\n"
                            stream_status = "success"
                            from gateway.routing.circuit_breaker import anthropic_breaker
                            anthropic_breaker.record_success()

        except httpx.ConnectError as e:
            logger.error(f"Failed to connect to Anthropic (streaming): {e}")
            from gateway.routing.circuit_breaker import anthropic_breaker
            anthropic_breaker.record_failure()
            error_chunk = {
                "id": response_id,
                "object": "chat.completion.chunk",
                "created": int(time.time()),
                "model": original_model,
                "choices": [
                    {
                        "index": 0,
                        "delta": {},
                        "finish_reason": "error",
                    }
                ],
                "_error": {
                    "message": "Failed to connect to LLM provider.",
                    "type": "server_error",
                    "code": "provider_unreachable",
                },
            }
            yield f"data: {json.dumps(error_chunk)}\n\n"
            yield "data: [DONE]\n\n"
            stream_status = "error"

        except httpx.TimeoutException as e:
            logger.error(f"Timeout streaming from Anthropic: {e}")
            from gateway.routing.circuit_breaker import anthropic_breaker
            anthropic_breaker.record_failure()
            stream_status = "error"
            yield "data: [DONE]\n\n"

        except GeneratorExit:
            # ── Case 2: Client disconnect ──
            # Client closed the connection mid-stream.
            # Use tokens_streamed_so_far for reconciliation.
            logger.info(
                f"Client disconnected mid-stream. "
                f"Tokens streamed so far: {completion_tokens}"
            )
            stream_status = "partial"

        except Exception as e:
            # ── Case 3: Provider error mid-stream ──
            logger.exception(
                f"Error during streaming: {e}. "
                f"Tokens streamed so far: {completion_tokens}"
            )
            stream_status = "error"
            yield "data: [DONE]\n\n"

        finally:
            # ── Reconciliation hook ──
            # Fire-and-forget: publish usage event regardless of how
            # the stream terminated. This is the integration point
            # with Person B's reconciliation (design decision #6).
            #
            # Person B: your reconciliation code should also hook here.
            # Option (b): we call a function you expose, passing the
            # final token count. Add your call here when ready.
            await _publish_event_safe(
                request=request,
                original_model=original_model,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                status=stream_status,
            )

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Request-ID": getattr(request.state, "request_id", "unknown"),
        },
    )


async def _publish_event_safe(
    request: Request,
    original_model: str,
    prompt_tokens: int,
    completion_tokens: int,
    status: str,
) -> None:
    """
    Fire-and-forget usage event publication.

    Per design decision #7:
    - Never blocks the client response
    - Silently drops on failure (logs warning)
    - This is the integration point with Person C's Kafka consumer

    Args:
        request: The FastAPI request (to read request.state).
        original_model: The model name the client originally requested.
        prompt_tokens: Number of prompt/input tokens used.
        completion_tokens: Number of completion/output tokens used.
        status: One of "success", "error", "partial".
    """
    try:
        event = {
            "request_id": getattr(request.state, "request_id", "unknown"),
            "key_id": getattr(request.state, "key_id", "unknown"),
            "team_id": getattr(request.state, "team_id", "unknown"),
            "model": original_model,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": prompt_tokens + completion_tokens,
            "estimated_cost_usd": 0.0,  # TODO: compute from pricing table
            "actual_cost_usd": 0.0,     # TODO: compute from pricing table
            "status": status,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }
        await publish_usage_event(event)
    except Exception as e:
        # Per decision #7: silently drop, never block the response
        logger.warning(f"Failed to publish usage event: {e}")
