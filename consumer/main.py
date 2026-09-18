"""
Aperture — Kafka Consumer Service
Person C, Task 3.

Entry point. Run as a standalone process:
    python -m consumer.main

Or via Docker Compose (see docker-compose.yml consumer service).

Lifecycle:
  1. Connect AIOKafkaConsumer to aperture.usage-events (all 3 partitions)
  2. For each message: deserialise → idempotency check → DynamoDB writes
  3. On SIGTERM/SIGINT: commit offsets, stop consumer cleanly
"""

import asyncio
import json
import logging
import os
import signal

from aiokafka import AIOKafkaConsumer
from aiokafka.errors import KafkaError

from gateway.models import UsageEvent
from consumer.handler import handle_event

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
)
logger = logging.getLogger("consumer.main")

# ── Config ────────────────────────────────────────────────────────────────────
# Inside Docker: use INTERNAL listener (kafka:9092)
# Running locally: set KAFKA_BROKER=localhost:9093
KAFKA_BROKER = os.getenv("KAFKA_BROKER", "kafka:9092")
KAFKA_TOPIC = os.getenv("KAFKA_USAGE_TOPIC", "aperture.usage-events")
KAFKA_GROUP_ID = os.getenv("KAFKA_GROUP_ID", "aperture-consumer-group")

# How many messages to process before committing offsets
COMMIT_BATCH_SIZE = int(os.getenv("CONSUMER_COMMIT_BATCH", "10"))


async def _consume_batch(
    consumer: AIOKafkaConsumer, shutdown_event: asyncio.Event
) -> None:
    """Consume messages in batches and commit offsets periodically."""
    batch_count = 0
    while not shutdown_event.is_set():
        try:
            async for msg in consumer:
                if shutdown_event.is_set():
                    break

                await _process_message(msg)
                batch_count += 1

                # Commit offsets every COMMIT_BATCH_SIZE messages
                if batch_count >= COMMIT_BATCH_SIZE:
                    await consumer.commit()
                    logger.debug("Offsets committed after %d messages.", batch_count)
                    batch_count = 0

        except KafkaError as exc:
            logger.error("Kafka error in consumer loop: %s — retrying in 5s", exc)
            await asyncio.sleep(5)

    # Drain: commit any remaining uncommitted offsets before exit
    if batch_count > 0:
        await consumer.commit()
        logger.info("Final offset commit (%d messages).", batch_count)


async def consume() -> None:
    """Main consumer lifecycle. Runs until SIGTERM/SIGINT."""
    consumer = AIOKafkaConsumer(
        KAFKA_TOPIC,
        bootstrap_servers=KAFKA_BROKER,
        group_id=KAFKA_GROUP_ID,
        # Start from earliest unprocessed offset for the group
        auto_offset_reset="earliest",
        # Manual commit so we only ack after successful DynamoDB writes
        enable_auto_commit=False,
        value_deserializer=lambda b: json.loads(b.decode("utf-8")),
        # How long to wait for new messages before the loop iterates
        consumer_timeout_ms=1000,
    )

    shutdown_event = asyncio.Event()

    def _signal_handler():
        logger.info("Shutdown signal received — draining consumer...")
        shutdown_event.set()

    loop = asyncio.get_running_loop()
    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(sig, _signal_handler)

    logger.info(
        "Starting consumer | broker=%s topic=%s group=%s",
        KAFKA_BROKER,
        KAFKA_TOPIC,
        KAFKA_GROUP_ID,
    )

    try:
        await consumer.start()
        logger.info("Consumer connected. Waiting for events...")
        await _consume_batch(consumer, shutdown_event)
    finally:
        await consumer.stop()
        logger.info("Consumer stopped cleanly.")


async def _process_message(msg) -> None:
    """Parse one Kafka message and hand it to the DynamoDB handler."""
    try:
        payload = msg.value
        event = UsageEvent(**payload)

        logger.info(
            "Processing | request_id=%s key_id=%s team=%s model=%s tokens=%d cost=$%.4f",
            event.request_id,
            event.key_id,
            event.team_id,
            event.model,
            event.total_tokens,
            event.actual_cost_usd,
        )

        await handle_event(event)

    except Exception as exc:  # noqa: BLE001
        # Log bad messages but never crash the consumer loop
        logger.error(
            "Failed to process message at partition=%d offset=%d: %s",
            msg.partition,
            msg.offset,
            exc,
            exc_info=True,
        )


def main() -> None:
    asyncio.run(consume())


if __name__ == "__main__":
    main()
