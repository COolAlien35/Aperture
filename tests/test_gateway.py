"""
Integration tests for the Aperture Gateway API.

Tests cover:
- Health check endpoint (/health)
- Request ID and latency headers middleware
- Request validation (bad schema, unknown model)
- Non-streaming chat completions flow with mock Anthropic
- Streaming chat completions flow with mock Anthropic SSE
- Circuit breaker fallback to OpenAI
- Error handling
"""

import json
from unittest.mock import patch, AsyncMock, MagicMock
import pytest
from starlette.testclient import TestClient


# We must mock the middlewares before importing `app` because they get registered
# or we can patch them in `gateway.main` directly.
@pytest.fixture(autouse=True)
def mock_middlewares():
    async def mock_pass_through(req):
        req.state.team_id = "test_team"
        req.state.key_id = "test_key"
        req.state.role = "admin"
        req.state.reserved = True
        return req

    with patch("gateway.main.auth_middleware", new=mock_pass_through), patch(
        "gateway.main.budget_check_middleware", new=mock_pass_through
    ):
        yield


from gateway.main import app
from gateway.routing.circuit_breaker import anthropic_breaker, CircuitState

client = TestClient(app)


def setup_function():
    """Reset circuit breaker state before each test."""
    anthropic_breaker.reset()


def test_health_endpoint():
    """Health check returns status ok and circuit breaker state."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["circuit_breaker"]["state"] == "closed"
    assert data["circuit_breaker"]["failure_count"] == 0


def test_request_id_and_latency_headers():
    """Every response contains X-Request-ID and X-Latency-Ms headers."""
    response = client.get("/health")
    assert "X-Request-ID" in response.headers
    assert "X-Latency-Ms" in response.headers
    assert float(response.headers["X-Latency-Ms"]) >= 0


def test_chat_completions_invalid_json():
    """Posting non-JSON body returns 400 with OpenAI-shaped error."""
    response = client.post(
        "/v1/chat/completions",
        content="not-json",
        headers={"Content-Type": "application/json"},
    )
    assert response.status_code == 400
    data = response.json()
    assert "error" in data
    assert data["error"]["type"] == "invalid_request_error"


def test_chat_completions_invalid_schema():
    """Missing required fields (e.g. messages) returns 400."""
    response = client.post(
        "/v1/chat/completions",
        json={"model": "gpt-4o"},
    )
    assert response.status_code == 400
    data = response.json()
    assert "error" in data
    assert data["error"]["type"] == "invalid_request_error"


def test_chat_completions_unknown_model():
    """Unknown model returns 400 invalid_model."""
    response = client.post(
        "/v1/chat/completions",
        json={
            "model": "nonexistent-model-123",
            "messages": [{"role": "user", "content": "hello"}],
        },
    )
    assert response.status_code == 400
    data = response.json()
    assert data["error"]["code"] == "invalid_model"


@pytest.mark.asyncio
async def test_chat_completions_non_streaming_success():
    """Successful non-streaming call translates correctly."""
    mock_anthropic_resp = {
        "id": "msg_01X",
        "type": "message",
        "role": "assistant",
        "content": [{"type": "text", "text": "Hello from mock Claude!"}],
        "model": "claude-sonnet-4-6",
        "stop_reason": "end_turn",
        "usage": {"input_tokens": 15, "output_tokens": 8},
    }

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = mock_anthropic_resp

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_resp

        response = client.post(
            "/v1/chat/completions",
            json={
                "model": "gpt-4o",
                "messages": [{"role": "user", "content": "Hi"}],
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["object"] == "chat.completion"
        assert data["choices"][0]["message"]["content"] == "Hello from mock Claude!"
        assert data["choices"][0]["finish_reason"] == "stop"
        assert data["usage"]["prompt_tokens"] == 15
        assert data["usage"]["completion_tokens"] == 8
        assert data["usage"]["total_tokens"] == 23
        assert "_aperture" in data


def test_circuit_breaker_routes_to_fallback():
    """When circuit breaker is open, requests route to OpenAI fallback."""
    # Force breaker to open
    anthropic_breaker.state = CircuitState.OPEN
    anthropic_breaker.failure_count = 3
    import time

    anthropic_breaker.last_failure_time = time.time()

    with patch(
        "gateway.main.call_openai_fallback", new_callable=AsyncMock
    ) as mock_fallback:
        from fastapi.responses import JSONResponse

        mock_fallback.return_value = JSONResponse(
            content={
                "id": "chatcmpl-fallback-test",
                "object": "chat.completion",
                "created": 123456,
                "model": "gpt-4o",
                "choices": [
                    {
                        "index": 0,
                        "message": {"role": "assistant", "content": "OpenAI fallback"},
                        "finish_reason": "stop",
                    }
                ],
                "usage": {
                    "prompt_tokens": 5,
                    "completion_tokens": 5,
                    "total_tokens": 10,
                },
            }
        )

        response = client.post(
            "/v1/chat/completions",
            json={
                "model": "gpt-4o",
                "messages": [{"role": "user", "content": "Hi"}],
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["choices"][0]["message"]["content"] == "OpenAI fallback"
        mock_fallback.assert_called_once()


def test_chat_completions_streaming_endpoint():
    """Streaming request delegates to call_anthropic_streaming."""
    from fastapi.responses import StreamingResponse

    async def dummy_generator():
        yield 'data: {"id":"chatcmpl-1","choices":[{"delta":{"content":"Hi"}}]}\n\n'
        yield "data: [DONE]\n\n"

    mock_streaming_resp = StreamingResponse(
        dummy_generator(),
        media_type="text/event-stream",
    )

    with patch(
        "gateway.main.call_anthropic_streaming", new_callable=AsyncMock
    ) as mock_stream:
        mock_stream.return_value = mock_streaming_resp

        response = client.post(
            "/v1/chat/completions",
            json={
                "model": "gpt-4o",
                "stream": True,
                "messages": [{"role": "user", "content": "Hi"}],
            },
        )

        assert response.status_code == 200
        assert "text/event-stream" in response.headers["content-type"]
        body = response.text
        assert "chatcmpl-1" in body
        assert "[DONE]" in body
        mock_stream.assert_called_once()


def test_models_endpoint():
    """GET /v1/models returns OpenAI-compatible model catalog."""
    response = client.get("/v1/models")
    assert response.status_code == 200
    data = response.json()
    assert data["object"] == "list"
    assert isinstance(data["data"], list)
    model_ids = [m["id"] for m in data["data"]]
    assert "gpt-4o" in model_ids
    assert "claude-sonnet-4-6" in model_ids


def test_cors_headers():
    """CORS preflight and responses include appropriate headers."""
    response = client.options(
        "/v1/chat/completions",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "POST",
        },
    )
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") in (
        "*",
        "http://localhost:3000",
    )
    assert "POST" in response.headers.get("access-control-allow-methods", "")
