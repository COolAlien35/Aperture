"""
Kafka usage event producer — STUB for Person C.

Person C: Replace this stub with real aiokafka producer logic.
This module is called by Person A's gateway after reconciliation completes.

Per design decision #7:
- Fire-and-forget, never blocks the client response
- acks=1 (not acks=all), short send timeout (~500ms)
- Wrapped in try/except — silently drops on failure
- Dropped events are accepted as lost (no local retry buffer for hackathon)
"""
import logging
from typing import Any

logger = logging.getLogger(__name__)


async def publish_usage_event(event: dict[str, Any]) -> None:
    """
    Publish a usage event to Kafka for downstream processing.

    Expected event shape (agree with Person A and B before implementing):
    {
        "request_id": str,          # from request.state.request_id
        "key_id": str,              # from request.state.key_id
        "team_id": str,             # from request.state.team_id
        "model": str,               # the model that was actually called
        "prompt_tokens": int,       # normalized OpenAI naming
        "completion_tokens": int,   # normalized OpenAI naming
        "total_tokens": int,
        "estimated_cost_usd": float,
        "actual_cost_usd": float,
        "status": str,              # "success" | "error" | "partial"
        "timestamp": str,           # ISO 8601
    }

    Person C will implement:
    - Initialize aiokafka producer (connect to KAFKA_BROKER)
    - Serialize event to JSON
    - Send to 'usage-events' topic
    - Handle errors silently (log + drop)

    Currently: logs the event and returns (no-op).
    """
    logger.info(f"[STUB] Would publish usage event: request_id={event.get('request_id')}")
