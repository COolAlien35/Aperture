"""
Unit tests for SSE streaming passthrough and non-streaming provider calls.

Tests cover:
- Token estimation heuristic (_estimate_tokens_from_text)
- Header construction (_get_anthropic_headers)
- Non-streaming call (success, 4xx/5xx error translation, network exceptions)
- Streaming call:
  - Clean completion (message_start -> content_block_delta -> message_delta -> message_stop)
  - Token tracking in request.state.tokens_streamed_so_far
  - Client disconnect handling (GeneratorExit / partial tokens)
  - Provider errors (initial non-200 status, ConnectError, TimeoutException)
- Safe event publishing (_publish_event_safe)
"""

import json
from unittest.mock import patch, AsyncMock, MagicMock
import pytest
import httpx
from starlette.requests import Request

from gateway.routing.streaming import (
    _estimate_tokens_from_text,
    _get_anthropic_headers,
    call_anthropic_non_streaming,
    call_anthropic_streaming,
    _publish_event_safe,
)
from gateway.routing.circuit_breaker import anthropic_breaker


def _make_dummy_request() -> Request:
    """Create a dummy starlette Request with mock state."""
    scope = {
        "type": "http",
        "method": "POST",
        "path": "/v1/chat/completions",
        "headers": [],
    }
    req = Request(scope)
    req.state.request_id = "test-req-123"
    req.state.key_id = "test-key"
    req.state.team_id = "test-team"
    req.state.role = "developer"
    return req


class TestTokenEstimation:
    def test_estimate_empty(self):
        assert _estimate_tokens_from_text("") == 0
        assert _estimate_tokens_from_text(None) == 0

    def test_estimate_short(self):
        # Even short text should be >= 1 token
        assert _estimate_tokens_from_text("hi") == 1

    def test_estimate_longer(self):
        text = "Hello world this is a test"
        assert _estimate_tokens_from_text(text) == len(text) // 4


class TestAnthropicHeaders:
    def test_headers_structure(self):
        headers = _get_anthropic_headers()
        assert "x-api-key" in headers
        assert "anthropic-version" in headers
        assert headers["content-type"] == "application/json"


class TestCallAnthropicNonStreaming:
    @pytest.mark.asyncio
    async def test_successful_call(self):
        req = _make_dummy_request()
        mock_resp_data = {
            "id": "msg_123",
            "type": "message",
            "role": "assistant",
            "content": [{"type": "text", "text": "Test reply"}],
            "model": "claude-sonnet-4-6",
            "stop_reason": "end_turn",
            "usage": {"input_tokens": 10, "output_tokens": 5},
        }
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = mock_resp_data

        with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post, \
             patch("gateway.routing.streaming.publish_usage_event", new_callable=AsyncMock) as mock_pub:
            mock_post.return_value = mock_resp

            res = await call_anthropic_non_streaming(
                req, {"model": "claude-sonnet-4-6", "messages": []}, "gpt-4o"
            )

            assert res.status_code == 200
            data = json.loads(res.body.decode("utf-8"))
            assert data["object"] == "chat.completion"
            assert data["choices"][0]["message"]["content"] == "Test reply"
            assert data["usage"]["prompt_tokens"] == 10
            assert data["usage"]["completion_tokens"] == 5
            assert data["_aperture"]["request_id"] == "test-req-123"
            mock_pub.assert_called_once()

    @pytest.mark.asyncio
    async def test_provider_error_status(self):
        req = _make_dummy_request()
        mock_resp_data = {
            "type": "error",
            "error": {"type": "rate_limit_error", "message": "Too many requests"},
        }
        mock_resp = MagicMock()
        mock_resp.status_code = 429
        mock_resp.json.return_value = mock_resp_data

        with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_resp

            res = await call_anthropic_non_streaming(
                req, {"model": "claude-sonnet-4-6", "messages": []}, "gpt-4o"
            )

            assert res.status_code == 429
            data = json.loads(res.body.decode("utf-8"))
            assert "error" in data
            assert data["error"]["type"] == "rate_limit_error"
            assert data["error"]["code"] == "rate_limit_error"

    @pytest.mark.asyncio
    async def test_connect_error(self):
        req = _make_dummy_request()
        with patch("httpx.AsyncClient.post", side_effect=httpx.ConnectError("Connection refused")):
            res = await call_anthropic_non_streaming(
                req, {"model": "claude-sonnet-4-6", "messages": []}, "gpt-4o"
            )
            assert res.status_code == 502
            data = json.loads(res.body.decode("utf-8"))
            assert data["error"]["code"] == "provider_unreachable"

    @pytest.mark.asyncio
    async def test_timeout_error(self):
        req = _make_dummy_request()
        with patch("httpx.AsyncClient.post", side_effect=httpx.TimeoutException("Timed out")):
            res = await call_anthropic_non_streaming(
                req, {"model": "claude-sonnet-4-6", "messages": []}, "gpt-4o"
            )
            assert res.status_code == 504
            data = json.loads(res.body.decode("utf-8"))
            assert data["error"]["code"] == "provider_timeout"


class TestCallAnthropicStreaming:
    @pytest.mark.asyncio
    async def test_clean_streaming_completion(self):
        req = _make_dummy_request()
        anthropic_breaker.reset()

        sse_lines = [
            "event: message_start\n",
            'data: {"type":"message_start","message":{"id":"msg_1","type":"message","role":"assistant","usage":{"input_tokens":12}}}\n',
            "\n",
            "event: content_block_delta\n",
            'data: {"type":"content_block_delta","index":0,"delta":{"type":"text_delta","text":"Hello "}}\n',
            "\n",
            "event: content_block_delta\n",
            'data: {"type":"content_block_delta","index":0,"delta":{"type":"text_delta","text":"World!"}}\n',
            "\n",
            "event: message_delta\n",
            'data: {"type":"message_delta","delta":{"stop_reason":"end_turn"},"usage":{"output_tokens":4}}\n',
            "\n",
            "event: message_stop\n",
            'data: {"type":"message_stop"}\n',
            "\n",
        ]

        async def mock_aiter_lines():
            for line in sse_lines:
                yield line

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.aiter_lines = mock_aiter_lines

        # Create async context manager mock for client.stream
        stream_context = AsyncMock()
        stream_context.__aenter__.return_value = mock_resp
        stream_context.__aexit__.return_value = None

        with patch("httpx.AsyncClient.stream", return_value=stream_context):
            streaming_resp = await call_anthropic_streaming(
                req, {"model": "claude-sonnet-4-6", "messages": []}, "gpt-4o"
            )

            assert streaming_resp.media_type == "text/event-stream"
            assert streaming_resp.headers["X-Request-ID"] == "test-req-123"

            # Consume the generator
            chunks = []
            async for chunk in streaming_resp.body_iterator:
                chunks.append(chunk)

            # Check chunks yielded
            full_stream = "".join(chunks)
            assert "data: [DONE]" in full_stream
            assert "Hello " in full_stream
            assert "World!" in full_stream
            assert req.state.prompt_tokens == 12
            assert req.state.tokens_streamed_so_far == 4
            assert anthropic_breaker.state.value == "closed"

    @pytest.mark.asyncio
    async def test_streaming_provider_500_error(self):
        req = _make_dummy_request()
        anthropic_breaker.reset()

        mock_resp = MagicMock()
        mock_resp.status_code = 500
        mock_resp.aread = AsyncMock(return_value=b'{"error":{"type":"api_error","message":"Overloaded"}}')

        stream_context = AsyncMock()
        stream_context.__aenter__.return_value = mock_resp
        stream_context.__aexit__.return_value = None

        with patch("httpx.AsyncClient.stream", return_value=stream_context):
            streaming_resp = await call_anthropic_streaming(
                req, {"model": "claude-sonnet-4-6", "messages": []}, "gpt-4o"
            )

            chunks = []
            async for chunk in streaming_resp.body_iterator:
                chunks.append(chunk)

            full_stream = "".join(chunks)
            assert "_error" in full_stream
            assert "data: [DONE]" in full_stream
            assert anthropic_breaker.failure_count == 1

    @pytest.mark.asyncio
    async def test_streaming_connect_error(self):
        req = _make_dummy_request()
        anthropic_breaker.reset()

        with patch("httpx.AsyncClient.stream", side_effect=httpx.ConnectError("Unreachable")):
            streaming_resp = await call_anthropic_streaming(
                req, {"model": "claude-sonnet-4-6", "messages": []}, "gpt-4o"
            )

            chunks = []
            async for chunk in streaming_resp.body_iterator:
                chunks.append(chunk)

            full_stream = "".join(chunks)
            assert "provider_unreachable" in full_stream
            assert "data: [DONE]" in full_stream
            assert anthropic_breaker.failure_count == 1

    @pytest.mark.asyncio
    async def test_streaming_client_disconnect(self):
        """When client disconnects (GeneratorExit), partial status is published."""
        req = _make_dummy_request()

        async def mock_aiter_lines():
            yield "event: content_block_delta\n"
            yield 'data: {"type":"content_block_delta","index":0,"delta":{"type":"text_delta","text":"Partial text"}}\n'
            # Client disconnects: generator is closed
            raise GeneratorExit()

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.aiter_lines = mock_aiter_lines

        stream_context = AsyncMock()
        stream_context.__aenter__.return_value = mock_resp
        stream_context.__aexit__.return_value = None

        with patch("httpx.AsyncClient.stream", return_value=stream_context), \
             patch("gateway.routing.streaming.publish_usage_event", new_callable=AsyncMock) as mock_pub:
            streaming_resp = await call_anthropic_streaming(
                req, {"model": "claude-sonnet-4-6", "messages": []}, "gpt-4o"
            )

            try:
                async for _ in streaming_resp.body_iterator:
                    pass
            except GeneratorExit:
                pass

            mock_pub.assert_called_once()
            event = mock_pub.call_args[0][0]
            assert event["status"] == "partial"
            assert event["completion_tokens"] > 0



class TestSafeEventPublishing:
    @pytest.mark.asyncio
    async def test_publish_event_safe_success(self):
        req = _make_dummy_request()
        with patch("gateway.routing.streaming.publish_usage_event", new_callable=AsyncMock) as mock_pub:
            await _publish_event_safe(
                request=req,
                original_model="gpt-4o",
                prompt_tokens=10,
                completion_tokens=20,
                status="success",
            )
            mock_pub.assert_called_once()
            called_event = mock_pub.call_args[0][0]
            assert called_event["request_id"] == "test-req-123"
            assert called_event["key_id"] == "test-key"
            assert called_event["team_id"] == "test-team"
            assert called_event["prompt_tokens"] == 10
            assert called_event["completion_tokens"] == 20
            assert called_event["total_tokens"] == 30
            assert called_event["status"] == "success"

    @pytest.mark.asyncio
    async def test_publish_event_safe_swallows_exception(self):
        req = _make_dummy_request()
        with patch("gateway.routing.streaming.publish_usage_event", side_effect=Exception("Kafka unavailable")):
            # Must not raise
            await _publish_event_safe(
                request=req,
                original_model="gpt-4o",
                prompt_tokens=5,
                completion_tokens=5,
                status="error",
            )
