"""
Unit tests for OpenAI fallback mechanism in gateway/routing/circuit_breaker.py.

Tests cover:
- Fallback when OPENAI_API_KEY is not set (503 Service Unavailable)
- Fallback when OPENAI_API_KEY is set and call succeeds (200 OK with _aperture metadata)
- Fallback when OpenAI returns an error (4xx/5xx status propagation)
- Fallback when network error occurs (502 provider_unreachable, 504 provider_timeout)
"""

import json
from unittest.mock import patch, AsyncMock, MagicMock
import pytest
import httpx
from starlette.requests import Request

from gateway.routing.circuit_breaker import call_openai_fallback


def _make_dummy_request() -> Request:
    scope = {
        "type": "http",
        "method": "POST",
        "path": "/v1/chat/completions",
        "headers": [],
    }
    req = Request(scope)
    req.state.request_id = "req-fallback-456"
    return req


@pytest.mark.asyncio
async def test_fallback_without_api_key():
    """When OPENAI_API_KEY is empty, fallback returns 503."""
    req = _make_dummy_request()
    with patch("gateway.routing.circuit_breaker.OPENAI_API_KEY", ""):
        res = await call_openai_fallback(req, {"model": "gpt-4o", "messages": []})
        assert res.status_code == 503
        data = json.loads(res.body.decode("utf-8"))
        assert data["error"]["code"] == "fallback_unavailable"


@pytest.mark.asyncio
async def test_fallback_success():
    """When OPENAI_API_KEY is set and call succeeds, returns 200 with _aperture metadata."""
    req = _make_dummy_request()
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "id": "chatcmpl-test",
        "object": "chat.completion",
        "choices": [{"index": 0, "message": {"role": "assistant", "content": "From OpenAI"}}],
        "usage": {"prompt_tokens": 10, "completion_tokens": 10, "total_tokens": 20},
    }

    with patch("gateway.routing.circuit_breaker.OPENAI_API_KEY", "sk-mock-key"), \
         patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_resp

        res = await call_openai_fallback(req, {"model": "gpt-4o", "messages": []})
        assert res.status_code == 200
        data = json.loads(res.body.decode("utf-8"))
        assert data["choices"][0]["message"]["content"] == "From OpenAI"
        assert data["_aperture"]["request_id"] == "req-fallback-456"
        assert data["_aperture"]["provider"] == "openai"
        assert data["_aperture"]["fallback"] is True


@pytest.mark.asyncio
async def test_fallback_upstream_error():
    """When OpenAI returns non-200, status and content are passed through."""
    req = _make_dummy_request()
    mock_resp = MagicMock()
    mock_resp.status_code = 401
    mock_resp.json.return_value = {"error": {"message": "Invalid API key", "type": "invalid_request_error"}}

    with patch("gateway.routing.circuit_breaker.OPENAI_API_KEY", "sk-mock-key"), \
         patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_resp

        res = await call_openai_fallback(req, {"model": "gpt-4o", "messages": []})
        assert res.status_code == 401
        data = json.loads(res.body.decode("utf-8"))
        assert data["error"]["message"] == "Invalid API key"


@pytest.mark.asyncio
async def test_fallback_connect_error():
    """When connecting to OpenAI fails, returns 502."""
    req = _make_dummy_request()
    with patch("gateway.routing.circuit_breaker.OPENAI_API_KEY", "sk-mock-key"), \
         patch("httpx.AsyncClient.post", side_effect=httpx.ConnectError("Connection refused")):
        res = await call_openai_fallback(req, {"model": "gpt-4o", "messages": []})
        assert res.status_code == 502
        data = json.loads(res.body.decode("utf-8"))
        assert data["error"]["code"] == "fallback_unreachable"


@pytest.mark.asyncio
async def test_fallback_timeout_error():
    """When OpenAI request times out, returns 504."""
    req = _make_dummy_request()
    with patch("gateway.routing.circuit_breaker.OPENAI_API_KEY", "sk-mock-key"), \
         patch("httpx.AsyncClient.post", side_effect=httpx.TimeoutException("Read timeout")):
        res = await call_openai_fallback(req, {"model": "gpt-4o", "messages": []})
        assert res.status_code == 504
        data = json.loads(res.body.decode("utf-8"))
        assert data["error"]["code"] == "fallback_timeout"
