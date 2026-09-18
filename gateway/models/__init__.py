"""
Shared Pydantic models — used by Person A, B, and C.

IMPORTANT: The `usage` field names (prompt_tokens / completion_tokens)
are a shared contract. Do NOT rename without team agreement.
"""

from __future__ import annotations

from pydantic import BaseModel, Field
from typing import Any

# ──────────────────────────────────────────────
# Request models (OpenAI-compatible public API)
# ──────────────────────────────────────────────


class ChatMessage(BaseModel):
    role: str  # "system" | "user" | "assistant"
    content: str | list[Any]  # string or content blocks


class ChatCompletionRequest(BaseModel):
    model: str
    messages: list[ChatMessage]
    max_tokens: int | None = None
    temperature: float | None = None
    top_p: float | None = None
    stream: bool = False
    stop: str | list[str] | None = None
    n: int = 1


# ──────────────────────────────────────────────
# Response models (OpenAI-compatible public API)
# ──────────────────────────────────────────────


class Usage(BaseModel):
    """
    Normalized usage — Anthropic's input_tokens/output_tokens are mapped
    to OpenAI's prompt_tokens/completion_tokens by the translator.

    SHARED CONTRACT: B's reconciliation and C's Kafka events both
    read these field names. Do NOT change without team agreement.
    """

    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0


class ChoiceMessage(BaseModel):
    role: str = "assistant"
    content: str = ""


class Choice(BaseModel):
    index: int = 0
    message: ChoiceMessage
    finish_reason: str | None = None  # "stop" | "length" | None


class ChatCompletionResponse(BaseModel):
    id: str = ""
    object: str = "chat.completion"
    created: int = 0
    model: str = ""
    choices: list[Choice] = []
    usage: Usage = Field(default_factory=Usage)


# ──────────────────────────────────────────────
# Streaming chunk models
# ──────────────────────────────────────────────


class DeltaContent(BaseModel):
    role: str | None = None
    content: str | None = None


class StreamChoice(BaseModel):
    index: int = 0
    delta: DeltaContent
    finish_reason: str | None = None


class ChatCompletionChunk(BaseModel):
    id: str = ""
    object: str = "chat.completion.chunk"
    created: int = 0
    model: str = ""
    choices: list[StreamChoice] = []


# ──────────────────────────────────────────────
# Error model (consistent shape for all providers)
# ──────────────────────────────────────────────


class GatewayError(BaseModel):
    """OpenAI-shaped error response. Used for both provider errors
    and gateway-generated errors (budget exceeded, auth failure, etc.)."""

    error: dict = Field(
        default_factory=lambda: {
            "message": "",
            "type": "gateway_error",
            "code": None,
        }
    )
