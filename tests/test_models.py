"""
Unit tests for Pydantic models in gateway/models/__init__.py.

Tests cover:
- ChatMessage (text content, content block list, None content)
- ChatCompletionRequest (defaults, max_tokens, temperature, stream)
- Usage normalization contract (prompt_tokens, completion_tokens, total_tokens)
- Choice and ChoiceMessage
- ChatCompletionResponse
- StreamChoice, DeltaContent, and ChatCompletionChunk
- GatewayError
"""

import pytest
from gateway.models import (
    ChatMessage,
    ChatCompletionRequest,
    Usage,
    Choice,
    ChoiceMessage,
    ChatCompletionResponse,
    DeltaContent,
    StreamChoice,
    ChatCompletionChunk,
    GatewayError,
)


class TestModels:
    def test_chat_message_string(self):
        msg = ChatMessage(role="user", content="hello")
        assert msg.role == "user"
        assert msg.content == "hello"

    def test_chat_message_list_blocks(self):
        msg = ChatMessage(role="user", content=[{"type": "text", "text": "block"}])
        assert isinstance(msg.content, list)
        assert msg.content[0]["text"] == "block"

    def test_chat_message_none_content(self):
        msg = ChatMessage(role="assistant", content=None)
        assert msg.content is None or msg.content == ""

    def test_chat_completion_request_defaults(self):
        req = ChatCompletionRequest(
            model="gpt-4o",
            messages=[ChatMessage(role="user", content="hi")],
        )
        assert req.model == "gpt-4o"
        assert req.stream is False
        assert req.n == 1
        assert req.max_tokens is None
        assert req.temperature is None
        assert req.top_p is None

    def test_usage_normalization_contract(self):
        usage = Usage(prompt_tokens=15, completion_tokens=25, total_tokens=40)
        assert usage.prompt_tokens == 15
        assert usage.completion_tokens == 25
        assert usage.total_tokens == 40
        dumped = usage.model_dump()
        assert "prompt_tokens" in dumped
        assert "completion_tokens" in dumped
        assert "total_tokens" in dumped

    def test_chat_completion_response(self):
        resp = ChatCompletionResponse(
            id="chatcmpl-123",
            created=1700000000,
            model="claude-sonnet-4-6",
            choices=[
                Choice(
                    index=0,
                    message=ChoiceMessage(role="assistant", content="hello"),
                    finish_reason="stop",
                )
            ],
            usage=Usage(prompt_tokens=10, completion_tokens=5, total_tokens=15),
        )
        assert resp.id == "chatcmpl-123"
        assert resp.object == "chat.completion"
        assert resp.choices[0].message.content == "hello"
        assert resp.usage.total_tokens == 15

    def test_chat_completion_chunk(self):
        chunk = ChatCompletionChunk(
            id="chatcmpl-chunk-1",
            model="gpt-4o",
            choices=[
                StreamChoice(
                    index=0,
                    delta=DeltaContent(role="assistant", content="world"),
                    finish_reason=None,
                )
            ],
        )
        assert chunk.object == "chat.completion.chunk"
        assert chunk.choices[0].delta.content == "world"

    def test_gateway_error(self):
        err = GatewayError(
            error={
                "message": "Quota exceeded",
                "type": "insufficient_quota",
                "code": "budget_exceeded",
            }
        )
        assert err.error["code"] == "budget_exceeded"

    def test_request_allows_extra_parameters(self):
        """Requests with custom fields (user, seed, response_format) don't error."""
        req = ChatCompletionRequest(
            model="gpt-4o",
            messages=[ChatMessage(role="user", content="Hi", custom_metadata="test")],
            user="org-user-99",
            seed=42,
            max_completion_tokens=2048,
        )
        assert req.max_completion_tokens == 2048
        assert req.model_extra.get("user") == "org-user-99"
        assert req.model_extra.get("seed") == 42

