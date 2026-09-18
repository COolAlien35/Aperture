"""
Kafka usage event producer — Person C.

Design Decision #7: Fire-and-forget.
  - Never blocks the client response.
  - acks=1, short request_timeout_ms (500ms).
  - All errors are caught, logged, and silently dropped.
  - Dropped events are accepted as lost (no local retry buffer for hackathon scope).

Design Decision #8:
  - request_id is generated upstream in main.py at request start.
  - This module reads it from the UsageEvent; never generates it.

Usage (from Person A's gateway after reconciliation):
  from gateway.events.producer import publish_usage_event
  from gateway.models import UsageEvent

  event = UsageEvent(
      request_id=request.state.request_id,
      key_id=request.state.key_id,
      team_id=request.state.team_id,
      model="claude-sonnet-4-6",
      prompt_tokens=120,
      completion_tokens=80,
      actual_cost_usd=0.0024,
      estimated_cost_usd=0.0025,
      status="success",
      timestamp=datetime.utcnow().isoformat() + "Z",
  )
  asyncio.create_task(publish_usage_event(event))  # fire-and-forget
"""

import asyncio
import json
import logging
import os
from datetime import datetime, timezone

from aiokafka import AIOKafkaProducer
from aiokafka.errors import KafkaConnectionError, KafkaError

from gateway.models import UsageEvent

logger = logging.getLogger(__name__)

# ── Config ────────────────────────────────────────────────────────────────────
# Inside Docker: gateway container reaches Kafka via the INTERNAL listener.
# If running the gateway locally (outside Docker), set KAFKA_BROKER=localhost:9093.
KAFKA_BROKER = os.getenv("KAFKA_BROKER", "kafka:9092")
KAFKA_TOPIC = os.getenv("KAFKA_USAGE_TOPIC", "aperture.usage-events")

# ── Module-level singleton producer ──────────────────────────────────────────
_producer: AIOKafkaProducer | None = None
_producer_lock = asyncio.Lock()


async def get_producer() -> AIOKafkaProducer | None:
    """
    Lazily initialise and cache the AIOKafkaProducer singleton.
    Returns None if Kafka is unreachable (gateway continues without it).
    """
    global _producer
    if _producer is not None:
        return _producer

    async with _producer_lock:
        # Double-check inside lock
        if _producer is not None:
            return _producer
        try:
            producer = AIOKafkaProducer(
                bootstrap_servers=KAFKA_BROKER,
                # Fire-and-forget: acks=1 means leader-acknowledged only
                acks=1,
                # Fail fast so we never block the response path
                request_timeout_ms=500,
                # JSON serialiser
                value_serializer=lambda v: json.dumps(v).encode("utf-8"),
                # Partition key serialiser (routes by team_id for ordering)
                key_serializer=lambda k: k.encode("utf-8") if k else None,
            )
            await producer.start()
            _producer = producer
            logger.info(
                "[Kafka] Producer connected to %s → topic: %s",
                KAFKA_BROKER,
                KAFKA_TOPIC,
            )
        except (KafkaConnectionError, KafkaError, Exception) as exc:
            logger.warning("[Kafka] Producer init failed — events will be dropped: %s", exc)
            _producer = None

    return _producer


async def close_producer() -> None:
    """
    Gracefully stop the producer. Call from the app lifespan shutdown hook.
    e.g. in main.py:
        @app.on_event("shutdown")
        async def shutdown_event():
            await close_producer()
    """
    global _producer
    if _producer is not None:
        try:
            await _producer.stop()
            logger.info("[Kafka] Producer stopped cleanly.")
        except Exception as exc:  # noqa: BLE001
            logger.warning("[Kafka] Error stopping producer: %s", exc)
        finally:
            _producer = None


async def publish_usage_event(event: UsageEvent) -> None:
    """
    Publish a UsageEvent to aperture.usage-events.

    Partitioning: keyed by team_id so all events for a team land in
    the same partition — preserving intra-team ordering for the consumer's
    spend aggregation.

    This is a fire-and-forget call:
      - asyncio.create_task(publish_usage_event(event))  ← recommended
      - await publish_usage_event(event)                 ← also fine; returns fast

    Failure modes:
      - Kafka unreachable at startup  → producer is None, event logged & dropped
      - Send timeout / network error  → caught, warning logged, event dropped
    """
    producer = await get_producer()
    if producer is None:
        logger.warning(
            "[Kafka] No producer available — dropping event request_id=%s",
            event.request_id,
        )
        return

    payload = {
        "request_id": event.request_id,
        "key_id": event.key_id,
        "team_id": event.team_id,
        "model": event.model,
        "prompt_tokens": event.prompt_tokens,
        "completion_tokens": event.completion_tokens,
        "total_tokens": event.total_tokens,
        "estimated_cost_usd": event.estimated_cost_usd,
        "actual_cost_usd": event.actual_cost_usd,
        "status": event.status,
        "timestamp": event.timestamp,
        # Include error message only when present (saves space in the happy path)
        **({"error_message": event.error_message} if event.error_message else {}),
    }

    try:
        await producer.send_and_wait(
            KAFKA_TOPIC,
            value=payload,
            # Partition key: team_id ensures all events for a team stay ordered
            key=event.team_id,
        )
        logger.debug(
            "[Kafka] Published event request_id=%s team_id=%s model=%s tokens=%d",
            event.request_id,
            event.team_id,
            event.model,
            event.total_tokens,
        )
    except asyncio.TimeoutError:
        logger.warning(
            "[Kafka] Send timed out (>500ms) — dropping event request_id=%s",
            event.request_id,
        )
    except (KafkaError, Exception) as exc:  # noqa: BLE001
        logger.warning(
            "[Kafka] Send failed — dropping event request_id=%s: %s",
            event.request_id,
            exc,
        )
