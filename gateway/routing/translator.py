"""
OpenAI <-> Anthropic request/response translator — Person A.

Translates incoming OpenAI-format requests to Anthropic's API format,
and translates Anthropic responses back to OpenAI-compatible format.

Key mappings:
  - System messages: extracted from messages list → top-level `system` field
  - Model names: aliased via MODEL_MAP (e.g. gpt-4o → claude-sonnet-4-6)
  - Usage: input_tokens/output_tokens → prompt_tokens/completion_tokens
  - Finish reason: end_turn → stop, max_tokens → length
  - Errors: Anthropic error shapes → OpenAI-compatible error shapes

See: Task 3 in PERSON_A_TASKS.md, design decisions #1, #6
"""

import time
import uuid
import logging
from typing import Any

from gateway.config import DEFAULT_MAX_TOKENS

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────
# Model alias mapping
# Public API exposes OpenAI-style names; we translate to Anthropic models.
# Agree with the team before changing these.
# ──────────────────────────────────────────────
MODEL_MAP: dict[str, str] = {
    "gpt-4o": "claude-sonnet-4-6",
    "gpt-4o-mini": "claude-haiku-4",
    "gpt-4-turbo": "claude-sonnet-4-6",
    "gpt-3.5-turbo": "claude-haiku-4",
    # Direct Anthropic model names pass through unchanged
}

# Reverse map for translating responses back
REVERSE_MODEL_MAP: dict[str, str] = {v: k for k, v in MODEL_MAP.items()}

# ──────────────────────────────────────────────
# Anthropic stop_reason → OpenAI finish_reason
# ──────────────────────────────────────────────
STOP_REASON_MAP: dict[str, str] = {
    "end_turn": "stop",
    "max_tokens": "length",
    "stop_sequence": "stop",
    "tool_use": "tool_calls",
}

# ──────────────────────────────────────────────
# Anthropic error type → OpenAI-compatible error type + HTTP status
# ──────────────────────────────────────────────
ANTHROPIC_ERROR_MAP: dict[str, dict[str, Any]] = {
    "authentication_error": {
        "type": "authentication_error",
        "http_status": 401,
    },
    "invalid_request_error": {
        "type": "invalid_request_error",
        "http_status": 400,
    },
    "rate_limit_error": {
        "type": "rate_limit_error",
        "http_status": 429,
    },
    "overloaded_error": {
        "type": "server_error",
        "http_status": 503,
    },
    "api_error": {
        "type": "server_error",
        "http_status": 500,
    },
    "not_found_error": {
        "type": "invalid_request_error",
        "http_status": 404,
    },
}


def resolve_model(model_name: str) -> str:
    """
    Resolve a public-facing model name to the Anthropic model identifier.

    If the model name is already a valid Anthropic model (e.g. starts with
    'claude-'), pass it through unchanged. Otherwise look it up in MODEL_MAP.

    Raises ValueError if the model is not found in the map and doesn't look
    like a native Anthropic model name.
    """
    # Direct Anthropic model names pass through
    if model_name.startswith("claude-"):
        return model_name

    mapped = MODEL_MAP.get(model_name)
    if mapped is None:
        raise ValueError(
            f"Unknown model '{model_name}'. "
            f"Supported aliases: {list(MODEL_MAP.keys())} "
            f"or use a native Anthropic model name (claude-*)."
        )
    return mapped


def translate_request_to_anthropic(openai_payload: dict) -> dict:
    """
    Translate an OpenAI-format chat completion request to Anthropic's format.

    Handles:
    - Extract system messages → top-level 'system' field (Anthropic requires this)
    - Map model name via MODEL_MAP
    - Default max_tokens to 4096 if not set (design decision #1, Option B)
    - Pass stream field through directly
    - Map temperature and top_p if present

    Args:
        openai_payload: OpenAI-format request dict with keys like
            model, messages, max_tokens, stream, temperature, etc.

    Returns:
        Anthropic-format request dict ready to POST to /v1/messages.

    Raises:
        ValueError: If the model name is not recognized.
    """
    messages = openai_payload.get("messages", [])

    # ── Extract system messages ──
    # Anthropic requires system as a top-level field, not in the messages list.
    # If multiple system messages exist, concatenate them.
    system_parts: list[str] = []
    non_system_messages: list[dict] = []

    for msg in messages:
        role = msg.get("role", "")
        content = msg.get("content", "")

        if role in ("system", "developer"):
            # Handle both string content and list content blocks
            if isinstance(content, str):
                system_parts.append(content)
            elif isinstance(content, list):
                # Extract text from content blocks
                for block in content:
                    if isinstance(block, dict) and block.get("type") == "text":
                        system_parts.append(block.get("text", ""))
                    elif isinstance(block, str):
                        system_parts.append(block)
        else:
            # Ensure content is a string for Anthropic
            if isinstance(content, list):
                # Convert content blocks to string
                text_parts = []
                for block in content:
                    if isinstance(block, dict) and block.get("type") == "text":
                        text_parts.append(block.get("text", ""))
                    elif isinstance(block, str):
                        text_parts.append(block)
                formatted_content = " ".join(text_parts) if text_parts else ""
            else:
                formatted_content = content if content is not None else ""

            # Map tool/function roles to user for Anthropic compatibility
            msg_role = role
            if msg_role in ("tool", "function"):
                msg_role = "user"
                formatted_content = f"[Tool output]: {formatted_content}"

            non_system_messages.append({
                "role": msg_role,
                "content": formatted_content,
            })

    # ── Normalize messages for Anthropic API requirements ──
    # 1. Anthropic requires the first message to have role: 'user'
    # 2. Roles must strictly alternate between 'user' and 'assistant'
    # 3. At least one message must be present
    consolidated_messages: list[dict[str, str]] = []
    for msg in non_system_messages:
        r = msg["role"]
        c = msg["content"]
        if not consolidated_messages:
            if r == "assistant":
                # Prepend a user prompt if conversation starts with assistant
                consolidated_messages.append({"role": "user", "content": "Hello"})
            consolidated_messages.append({"role": r, "content": c})
        else:
            prev = consolidated_messages[-1]
            if prev["role"] == r:
                # Merge consecutive turns of the same role
                prev["content"] = f"{prev['content']}\n\n{c}" if prev["content"] else c
            else:
                consolidated_messages.append({"role": r, "content": c})

    if not consolidated_messages:
        consolidated_messages.append({"role": "user", "content": "Hello"})

    # ── Resolve model name ──
    model_name = openai_payload.get("model", "")
    anthropic_model = resolve_model(model_name)

    # Max tokens: check max_tokens first, then modern max_completion_tokens
    max_tokens = (
        openai_payload.get("max_tokens")
        or openai_payload.get("max_completion_tokens")
        or DEFAULT_MAX_TOKENS
    )

    # ── Build Anthropic payload ──
    anthropic_payload: dict[str, Any] = {
        "model": anthropic_model,
        "messages": consolidated_messages,
        "max_tokens": max_tokens,
    }

    # Add system prompt if present
    if system_parts:
        anthropic_payload["system"] = "\n\n".join(system_parts)

    # Pass through stream flag
    if openai_payload.get("stream") is not None:
        anthropic_payload["stream"] = openai_payload["stream"]

    # Pass through temperature if set
    if openai_payload.get("temperature") is not None:
        anthropic_payload["temperature"] = openai_payload["temperature"]

    # Pass through top_p if set
    if openai_payload.get("top_p") is not None:
        anthropic_payload["top_p"] = openai_payload["top_p"]

    # Pass through stop sequences if set
    if openai_payload.get("stop") is not None:
        stop = openai_payload["stop"]
        if isinstance(stop, str):
            anthropic_payload["stop_sequences"] = [stop]
        elif isinstance(stop, list):
            anthropic_payload["stop_sequences"] = stop

    return anthropic_payload


def translate_response_from_anthropic(
    anthropic_response: dict,
    original_model: str | None = None,
) -> dict:
    """
    Translate an Anthropic response back to OpenAI's chat.completion format.

    Handles:
    - content[0].text → choices[0].message.content
    - usage.input_tokens → usage.prompt_tokens
    - usage.output_tokens → usage.completion_tokens
    - stop_reason → finish_reason mapping
    - Generates chatcmpl-xxx style response ID

    Args:
        anthropic_response: Raw response dict from Anthropic's /v1/messages API.
        original_model: The model name the client originally requested (for the
            response's `model` field). If None, uses the Anthropic model name.

    Returns:
        OpenAI-format chat.completion response dict.
    """
    # ── Extract content ──
    content_blocks = anthropic_response.get("content", [])
    response_text = ""
    for block in content_blocks:
        if isinstance(block, dict):
            if block.get("type") == "text":
                response_text += block.get("text", "")
        elif isinstance(block, str):
            response_text += block

    # ── Map usage ──
    anthropic_usage = anthropic_response.get("usage", {})
    prompt_tokens = anthropic_usage.get("input_tokens", 0)
    completion_tokens = anthropic_usage.get("output_tokens", 0)

    # ── Map finish reason ──
    stop_reason = anthropic_response.get("stop_reason", "end_turn")
    finish_reason = STOP_REASON_MAP.get(stop_reason, "stop")

    # ── Determine model name for response ──
    anthropic_model = anthropic_response.get("model", "")
    response_model = original_model or REVERSE_MODEL_MAP.get(
        anthropic_model, anthropic_model
    )

    # ── Build OpenAI-format response ──
    return {
        "id": f"chatcmpl-{uuid.uuid4().hex[:12]}",
        "object": "chat.completion",
        "created": int(time.time()),
        "model": response_model,
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": response_text,
                },
                "finish_reason": finish_reason,
            }
        ],
        "usage": {
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": prompt_tokens + completion_tokens,
        },
    }


def translate_error_from_anthropic(
    anthropic_error: dict,
    http_status: int = 500,
) -> tuple[dict, int]:
    """
    Translate an Anthropic error response to an OpenAI-shaped error response.

    Anthropic errors look like:
    {
        "type": "error",
        "error": {
            "type": "authentication_error",
            "message": "invalid x-api-key"
        }
    }

    We translate to OpenAI-shaped:
    {
        "error": {
            "message": "...",
            "type": "...",
            "code": null
        }
    }

    Args:
        anthropic_error: The error response dict from Anthropic.
        http_status: The HTTP status code from the Anthropic response.

    Returns:
        Tuple of (OpenAI-shaped error dict, HTTP status code to return).
    """
    error_body = anthropic_error.get("error", {})
    error_type = error_body.get("type", "api_error")
    error_message = error_body.get("message", "Unknown error from provider")

    # Look up the mapped error type and status
    mapped = ANTHROPIC_ERROR_MAP.get(error_type, {
        "type": "server_error",
        "http_status": http_status,
    })

    openai_error = {
        "error": {
            "message": error_message,
            "type": mapped["type"],
            "code": error_type,
        }
    }

    return openai_error, mapped["http_status"]
