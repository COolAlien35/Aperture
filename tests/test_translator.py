"""
Unit tests for the OpenAI <-> Anthropic translator.

Tests cover:
- Request translation (system messages, model mapping, max_tokens, stop sequences)
- Response translation (content, usage, finish_reason)
- Error translation (all Anthropic error types)
- Edge cases (multiple system messages, unknown models, empty content)
"""

import pytest
from gateway.routing.translator import (
    translate_request_to_anthropic,
    translate_response_from_anthropic,
    translate_error_from_anthropic,
    resolve_model,
    MODEL_MAP,
)
from gateway.config import DEFAULT_MAX_TOKENS


# ──────────────────────────────────────────────
# Request translation tests
# ──────────────────────────────────────────────


class TestTranslateRequestToAnthropic:
    """Tests for translate_request_to_anthropic()."""

    def test_basic_request(self):
        """Basic request with user message translates correctly."""
        payload = {
            "model": "gpt-4o",
            "messages": [
                {"role": "user", "content": "Hello, world!"}
            ],
        }
        result = translate_request_to_anthropic(payload)

        assert result["model"] == "claude-sonnet-4-6"
        assert len(result["messages"]) == 1
        assert result["messages"][0]["role"] == "user"
        assert result["messages"][0]["content"] == "Hello, world!"
        assert result["max_tokens"] == DEFAULT_MAX_TOKENS
        assert "system" not in result

    def test_system_message_extraction(self):
        """System messages are extracted to top-level 'system' field."""
        payload = {
            "model": "gpt-4o",
            "messages": [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Hi there"},
            ],
        }
        result = translate_request_to_anthropic(payload)

        assert result["system"] == "You are a helpful assistant."
        assert len(result["messages"]) == 1
        assert result["messages"][0]["role"] == "user"

    def test_multiple_system_messages_concatenated(self):
        """Multiple system messages are concatenated with double newlines."""
        payload = {
            "model": "gpt-4o",
            "messages": [
                {"role": "system", "content": "Be concise."},
                {"role": "system", "content": "Respond in JSON."},
                {"role": "user", "content": "What is 2+2?"},
            ],
        }
        result = translate_request_to_anthropic(payload)

        assert result["system"] == "Be concise.\n\nRespond in JSON."
        assert len(result["messages"]) == 1

    def test_max_tokens_passthrough(self):
        """Client-specified max_tokens is passed through."""
        payload = {
            "model": "gpt-4o",
            "messages": [{"role": "user", "content": "Hi"}],
            "max_tokens": 500,
        }
        result = translate_request_to_anthropic(payload)
        assert result["max_tokens"] == 500

    def test_max_tokens_default_when_missing(self):
        """max_tokens defaults to DEFAULT_MAX_TOKENS when not set."""
        payload = {
            "model": "gpt-4o",
            "messages": [{"role": "user", "content": "Hi"}],
        }
        result = translate_request_to_anthropic(payload)
        assert result["max_tokens"] == DEFAULT_MAX_TOKENS

    def test_max_tokens_default_when_none(self):
        """max_tokens defaults when explicitly set to None."""
        payload = {
            "model": "gpt-4o",
            "messages": [{"role": "user", "content": "Hi"}],
            "max_tokens": None,
        }
        result = translate_request_to_anthropic(payload)
        assert result["max_tokens"] == DEFAULT_MAX_TOKENS

    def test_stream_passthrough(self):
        """Stream flag is passed through directly."""
        payload = {
            "model": "gpt-4o",
            "messages": [{"role": "user", "content": "Hi"}],
            "stream": True,
        }
        result = translate_request_to_anthropic(payload)
        assert result["stream"] is True

    def test_temperature_passthrough(self):
        """Temperature is passed through when set."""
        payload = {
            "model": "gpt-4o",
            "messages": [{"role": "user", "content": "Hi"}],
            "temperature": 0.7,
        }
        result = translate_request_to_anthropic(payload)
        assert result["temperature"] == 0.7

    def test_top_p_passthrough(self):
        """top_p is passed through when set."""
        payload = {
            "model": "gpt-4o",
            "messages": [{"role": "user", "content": "Hi"}],
            "top_p": 0.9,
        }
        result = translate_request_to_anthropic(payload)
        assert result["top_p"] == 0.9

    def test_stop_string_to_list(self):
        """Single stop string is converted to stop_sequences list."""
        payload = {
            "model": "gpt-4o",
            "messages": [{"role": "user", "content": "Hi"}],
            "stop": "END",
        }
        result = translate_request_to_anthropic(payload)
        assert result["stop_sequences"] == ["END"]

    def test_stop_list_passthrough(self):
        """Stop list is passed as stop_sequences."""
        payload = {
            "model": "gpt-4o",
            "messages": [{"role": "user", "content": "Hi"}],
            "stop": ["END", "STOP"],
        }
        result = translate_request_to_anthropic(payload)
        assert result["stop_sequences"] == ["END", "STOP"]

    def test_no_optional_fields_when_not_set(self):
        """Optional fields are not included when not set."""
        payload = {
            "model": "gpt-4o",
            "messages": [{"role": "user", "content": "Hi"}],
        }
        result = translate_request_to_anthropic(payload)
        assert "temperature" not in result
        assert "top_p" not in result
        assert "stop_sequences" not in result
        assert "stream" not in result

    def test_conversation_with_assistant(self):
        """Multi-turn conversation with assistant messages."""
        payload = {
            "model": "gpt-4o",
            "messages": [
                {"role": "system", "content": "You are helpful."},
                {"role": "user", "content": "Hi"},
                {"role": "assistant", "content": "Hello!"},
                {"role": "user", "content": "How are you?"},
            ],
        }
        result = translate_request_to_anthropic(payload)

        assert result["system"] == "You are helpful."
        assert len(result["messages"]) == 3
        assert result["messages"][0]["role"] == "user"
        assert result["messages"][1]["role"] == "assistant"
        assert result["messages"][2]["role"] == "user"


# ──────────────────────────────────────────────
# Model resolution tests
# ──────────────────────────────────────────────


class TestResolveModel:
    """Tests for resolve_model()."""

    def test_all_aliases_resolve(self):
        """All MODEL_MAP aliases resolve correctly."""
        for openai_name, anthropic_name in MODEL_MAP.items():
            assert resolve_model(openai_name) == anthropic_name

    def test_native_anthropic_passthrough(self):
        """Native Anthropic model names pass through unchanged."""
        assert resolve_model("claude-sonnet-4-6") == "claude-sonnet-4-6"
        assert resolve_model("claude-haiku-4") == "claude-haiku-4"
        assert resolve_model("claude-3-opus-20240229") == "claude-3-opus-20240229"

    def test_unknown_model_raises(self):
        """Unknown, non-Anthropic model names raise ValueError."""
        with pytest.raises(ValueError, match="Unknown model"):
            resolve_model("totally-fake-model")


# ──────────────────────────────────────────────
# Response translation tests
# ──────────────────────────────────────────────


class TestTranslateResponseFromAnthropic:
    """Tests for translate_response_from_anthropic()."""

    def test_basic_response(self):
        """Basic Anthropic response translates correctly."""
        anthropic_resp = {
            "id": "msg_123",
            "type": "message",
            "role": "assistant",
            "model": "claude-sonnet-4-6",
            "content": [
                {"type": "text", "text": "Hello! How can I help?"}
            ],
            "stop_reason": "end_turn",
            "usage": {
                "input_tokens": 15,
                "output_tokens": 8,
            },
        }
        result = translate_response_from_anthropic(anthropic_resp, "gpt-4o")

        assert result["id"].startswith("chatcmpl-")
        assert result["object"] == "chat.completion"
        assert result["model"] == "gpt-4o"
        assert result["choices"][0]["message"]["role"] == "assistant"
        assert result["choices"][0]["message"]["content"] == "Hello! How can I help?"
        assert result["choices"][0]["finish_reason"] == "stop"
        assert result["usage"]["prompt_tokens"] == 15
        assert result["usage"]["completion_tokens"] == 8
        assert result["usage"]["total_tokens"] == 23

    def test_max_tokens_finish_reason(self):
        """max_tokens stop_reason maps to 'length' finish_reason."""
        anthropic_resp = {
            "content": [{"type": "text", "text": "partial..."}],
            "stop_reason": "max_tokens",
            "usage": {"input_tokens": 10, "output_tokens": 100},
        }
        result = translate_response_from_anthropic(anthropic_resp)
        assert result["choices"][0]["finish_reason"] == "length"

    def test_stop_sequence_finish_reason(self):
        """stop_sequence stop_reason maps to 'stop' finish_reason."""
        anthropic_resp = {
            "content": [{"type": "text", "text": "done"}],
            "stop_reason": "stop_sequence",
            "usage": {"input_tokens": 5, "output_tokens": 3},
        }
        result = translate_response_from_anthropic(anthropic_resp)
        assert result["choices"][0]["finish_reason"] == "stop"

    def test_multiple_content_blocks(self):
        """Multiple text content blocks are concatenated."""
        anthropic_resp = {
            "content": [
                {"type": "text", "text": "First part. "},
                {"type": "text", "text": "Second part."},
            ],
            "stop_reason": "end_turn",
            "usage": {"input_tokens": 5, "output_tokens": 10},
        }
        result = translate_response_from_anthropic(anthropic_resp)
        assert (
            result["choices"][0]["message"]["content"]
            == "First part. Second part."
        )

    def test_empty_content(self):
        """Empty content blocks produce empty content string."""
        anthropic_resp = {
            "content": [],
            "stop_reason": "end_turn",
            "usage": {"input_tokens": 5, "output_tokens": 0},
        }
        result = translate_response_from_anthropic(anthropic_resp)
        assert result["choices"][0]["message"]["content"] == ""

    def test_usage_total_calculated(self):
        """total_tokens is calculated as prompt + completion."""
        anthropic_resp = {
            "content": [{"type": "text", "text": "ok"}],
            "stop_reason": "end_turn",
            "usage": {"input_tokens": 100, "output_tokens": 50},
        }
        result = translate_response_from_anthropic(anthropic_resp)
        assert result["usage"]["total_tokens"] == 150

    def test_original_model_preserved(self):
        """original_model parameter is used in response."""
        anthropic_resp = {
            "model": "claude-sonnet-4-6",
            "content": [{"type": "text", "text": "hi"}],
            "stop_reason": "end_turn",
            "usage": {"input_tokens": 5, "output_tokens": 2},
        }
        result = translate_response_from_anthropic(
            anthropic_resp, "gpt-4o-mini"
        )
        assert result["model"] == "gpt-4o-mini"


# ──────────────────────────────────────────────
# Error translation tests
# ──────────────────────────────────────────────


class TestTranslateErrorFromAnthropic:
    """Tests for translate_error_from_anthropic()."""

    def test_authentication_error(self):
        """Authentication error maps correctly."""
        error = {
            "type": "error",
            "error": {
                "type": "authentication_error",
                "message": "invalid x-api-key",
            },
        }
        result, status = translate_error_from_anthropic(error)
        assert status == 401
        assert result["error"]["type"] == "authentication_error"
        assert result["error"]["message"] == "invalid x-api-key"
        assert result["error"]["code"] == "authentication_error"

    def test_rate_limit_error(self):
        """Rate limit error maps to 429."""
        error = {
            "type": "error",
            "error": {
                "type": "rate_limit_error",
                "message": "Rate limit exceeded",
            },
        }
        result, status = translate_error_from_anthropic(error)
        assert status == 429
        assert result["error"]["type"] == "rate_limit_error"

    def test_overloaded_error(self):
        """Overloaded error maps to 503."""
        error = {
            "type": "error",
            "error": {
                "type": "overloaded_error",
                "message": "Overloaded",
            },
        }
        result, status = translate_error_from_anthropic(error)
        assert status == 503
        assert result["error"]["type"] == "server_error"

    def test_invalid_request_error(self):
        """Invalid request error maps to 400."""
        error = {
            "type": "error",
            "error": {
                "type": "invalid_request_error",
                "message": "max_tokens is required",
            },
        }
        result, status = translate_error_from_anthropic(error)
        assert status == 400
        assert result["error"]["type"] == "invalid_request_error"

    def test_unknown_error_type(self):
        """Unknown error types get a safe default."""
        error = {
            "type": "error",
            "error": {
                "type": "some_new_error",
                "message": "Something new",
            },
        }
        result, status = translate_error_from_anthropic(error, 500)
        assert status == 500
        assert result["error"]["type"] == "server_error"


class TestEdgeCaseTranslations:
    """Tests for tricky edge cases in translate_request_to_anthropic."""

    def test_developer_role_extracted_as_system(self):
        """OpenAI 'developer' role is extracted to top-level 'system'."""
        payload = {
            "model": "gpt-4o",
            "messages": [
                {"role": "developer", "content": "Formatting rules."},
                {"role": "user", "content": "Hi"},
            ],
        }
        result = translate_request_to_anthropic(payload)
        assert result["system"] == "Formatting rules."
        assert len(result["messages"]) == 1
        assert result["messages"][0]["role"] == "user"

    def test_tool_role_mapped_to_user(self):
        """OpenAI 'tool' role is safely mapped to 'user' for Anthropic."""
        payload = {
            "model": "gpt-4o",
            "messages": [
                {"role": "user", "content": "What is the weather?"},
                {"role": "assistant", "content": "Checking..."},
                {"role": "tool", "content": "Sunny, 72F"},
            ],
        }
        result = translate_request_to_anthropic(payload)
        assert result["messages"][2]["role"] == "user"
        assert "[Tool output]: Sunny, 72F" in result["messages"][2]["content"]

    def test_consecutive_same_role_messages_consolidated(self):
        """Consecutive messages of same role are merged to satisfy Anthropic."""
        payload = {
            "model": "gpt-4o",
            "messages": [
                {"role": "user", "content": "Part 1."},
                {"role": "user", "content": "Part 2."},
            ],
        }
        result = translate_request_to_anthropic(payload)
        assert len(result["messages"]) == 1
        assert result["messages"][0]["role"] == "user"
        assert "Part 1.\n\nPart 2." in result["messages"][0]["content"]

    def test_first_message_assistant_prepends_user(self):
        """If conversation starts with assistant, a user message is prepended."""
        payload = {
            "model": "gpt-4o",
            "messages": [
                {"role": "assistant", "content": "How can I help?"},
                {"role": "user", "content": "I need help with python."},
            ],
        }
        result = translate_request_to_anthropic(payload)
        assert result["messages"][0]["role"] == "user"
        assert result["messages"][1]["role"] == "assistant"
        assert result["messages"][2]["role"] == "user"

    def test_system_only_messages_adds_user_turn(self):
        """If only system messages are passed, a default user turn is provided."""
        payload = {
            "model": "gpt-4o",
            "messages": [
                {"role": "system", "content": "You are a calculator."},
            ],
        }
        result = translate_request_to_anthropic(payload)
        assert result["system"] == "You are a calculator."
        assert len(result["messages"]) == 1
        assert result["messages"][0]["role"] == "user"

    def test_max_completion_tokens_honored(self):
        """OpenAI's modern max_completion_tokens is supported."""
        payload = {
            "model": "gpt-4o",
            "messages": [{"role": "user", "content": "Hi"}],
            "max_completion_tokens": 1234,
        }
        result = translate_request_to_anthropic(payload)
        assert result["max_tokens"] == 1234

