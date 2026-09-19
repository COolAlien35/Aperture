"""
Shared Pydantic models — used by Person A, B, and C.

IMPORTANT: The `usage` field names (prompt_tokens / completion_tokens)
are a shared contract. Do NOT rename without team agreement.
"""

from __future__ import annotations

from pydantic import BaseModel, Field, ConfigDict
from typing import Any

# ──────────────────────────────────────────────
# Request models (OpenAI-compatible public API)
# ──────────────────────────────────────────────


class ChatMessage(BaseModel):
    model_config = ConfigDict(extra="allow")
    role: str  # "system" | "user" | "assistant" | "developer" | "tool"
    content: str | list[Any] | None = ""  # string, content blocks, or None


class ChatCompletionRequest(BaseModel):
    model_config = ConfigDict(extra="allow")
    model: str
    messages: list[ChatMessage]
    max_tokens: int | None = None
    max_completion_tokens: int | None = None
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


# ──────────────────────────────────────────────
# Usage event model (Person C: Kafka streaming & DynamoDB logging)
# ──────────────────────────────────────────────


class UsageEvent(BaseModel):
    """
    Kafka usage event schema — Person C contract.
    Published by gateway/events/producer.py after request reconciliation.
    Consumed by consumer service for DynamoDB writes and spend aggregation.

    Per PRD and Design Decisions #7 and #8:
      - request_id generated at request start in main.py
      - Token counts normalized to OpenAI format (prompt_tokens / completion_tokens)
      - Idempotency key for DynamoDB consumer deduplication: PROCESSED#<request_id>
    """

    request_id: str
    key_id: str
    team_id: str
    model: str
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    estimated_cost_usd: float = 0.0
    actual_cost_usd: float = 0.0
    status: str = "success"  # "success" | "error" | "partial"
    timestamp: str  # ISO 8601 UTC
    error_message: str | None = None
    session_id: str | None = None

    def model_post_init(self, __context: Any) -> None:
        if self.total_tokens == 0 and (self.prompt_tokens or self.completion_tokens):
            self.total_tokens = self.prompt_tokens + self.completion_tokens

    def to_dynamodb_usage_item(self) -> dict[str, Any]:
        """Convert usage event to DynamoDB single-table item for KEY#<key_id> / USAGE#<timestamp>."""
        from decimal import Decimal

        item: dict[str, Any] = {
            "PK": f"KEY#{self.key_id}",
            "SK": f"USAGE#{self.timestamp}",
            "request_id": self.request_id,
            "key_id": self.key_id,
            "team_id": self.team_id,
            "model": self.model,
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "total_tokens": self.total_tokens,
            "actual_cost_usd": Decimal(str(self.actual_cost_usd)),
            "estimated_cost_usd": Decimal(str(self.estimated_cost_usd)),
            "status": self.status,
            "timestamp": self.timestamp,
            "GSI1PK": self.team_id,
            "GSI1SK": f"USAGE#{self.timestamp}",
        }
        if self.error_message:
            item["error_message"] = self.error_message
        if self.session_id:
            item["session_id"] = self.session_id
        return item

