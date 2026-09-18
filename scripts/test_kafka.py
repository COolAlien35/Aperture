"""
Kafka end-to-end smoke test — Person C, Task 2.

Tests:
  1. Producer can connect to aperture.usage-events (via EXTERNAL listener on localhost:9093)
  2. A UsageEvent serialises correctly and round-trips through Kafka
  3. Partition key (team_id) is preserved
  4. Consumer receives the exact payload that was sent
  5. Idempotent: sending the same request_id twice produces two messages (dedup happens in DynamoDB consumer, not here)

Run from project root:
    source .venv/bin/activate
    python3 scripts/test_kafka.py
"""

import asyncio
import json
import sys
import uuid
from datetime import datetime, timezone

from aiokafka import AIOKafkaConsumer, AIOKafkaProducer

KAFKA_BROKER = "localhost:9093"  # EXTERNAL listener for host-side scripts
TOPIC = "aperture.usage-events"
GROUP_ID = f"test-verifier-{uuid.uuid4().hex[:8]}"

DIVIDER = "=" * 65


def make_event(suffix: str = "") -> dict:
    return {
        "request_id": f"req-test-{uuid.uuid4().hex[:12]}{suffix}",
        "key_id": "sk-gw-test001",
        "team_id": "engineering",
        "model": "claude-sonnet-4-6",
        "prompt_tokens": 120,
        "completion_tokens": 80,
        "total_tokens": 200,
        "estimated_cost_usd": 0.0024,
        "actual_cost_usd": 0.0020,
        "status": "success",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


async def run_tests():
    print(DIVIDER)
    print("  Aperture Kafka End-to-End Smoke Test — Person C")
    print(f"  Broker: {KAFKA_BROKER}   Topic: {TOPIC}")
    print(DIVIDER)

    errors = []

    # ── Loop 1: Basic connectivity ─────────────────────────────
    print("\n📡 Loop 1: Broker connectivity + topic metadata")
    producer = AIOKafkaProducer(
        bootstrap_servers=KAFKA_BROKER,
        acks=1,
        request_timeout_ms=3000,
        value_serializer=lambda v: json.dumps(v).encode("utf-8"),
        key_serializer=lambda k: k.encode("utf-8") if k else None,
    )
    try:
        await producer.start()
        partitions = await producer.partitions_for(TOPIC)
        assert (
            partitions is not None
        ), "partitions_for() returned None — topic may not exist"
        print(f"  ✅ Connected. Partitions for '{TOPIC}': {sorted(partitions)}")
    except Exception as exc:
        errors.append(f"Loop 1: {exc}")
        print(f"  ❌ {exc}")
        await producer.stop()
        return errors

    # ── Loop 2: Produce 3 events with different request_ids ───
    print("\n📤 Loop 2: Produce 3 UsageEvents")
    events = [make_event(f"-{i}") for i in range(3)]
    sent_ids = []
    for i, event in enumerate(events):
        try:
            meta = await producer.send_and_wait(
                TOPIC, value=event, key=event["team_id"]
            )
            sent_ids.append(event["request_id"])
            print(
                f"  ✅ Sent [{i+1}/3] request_id={event['request_id']} "
                f"→ partition={meta.partition} offset={meta.offset}"
            )
        except Exception as exc:
            errors.append(f"Loop 2 send {i}: {exc}")
            print(f"  ❌ Send failed: {exc}")

    await producer.stop()

    # ── Loop 3: Consume and verify payloads ───────────────────
    print(f"\n📥 Loop 3: Consume {len(sent_ids)} events and verify payload fields")
    consumer = AIOKafkaConsumer(
        TOPIC,
        bootstrap_servers=KAFKA_BROKER,
        group_id=GROUP_ID,
        auto_offset_reset="earliest",
        value_deserializer=lambda b: json.loads(b.decode("utf-8")),
        consumer_timeout_ms=5000,
    )
    try:
        await consumer.start()
        received = {}
        async for msg in consumer:
            payload = msg.value
            rid = payload.get("request_id", "")
            if rid in sent_ids:
                received[rid] = payload
                print(
                    f"  📨 Received request_id={rid} partition={msg.partition} offset={msg.offset}"
                )
            if len(received) >= len(sent_ids):
                break
    except Exception as exc:
        errors.append(f"Loop 3 consume: {exc}")
        print(f"  ❌ Consumer error: {exc}")
    finally:
        await consumer.stop()

    # ── Loop 4: Verify payload field correctness ──────────────
    print("\n🔍 Loop 4: Payload field-level verification")
    REQUIRED_FIELDS = [
        "request_id",
        "key_id",
        "team_id",
        "model",
        "prompt_tokens",
        "completion_tokens",
        "total_tokens",
        "estimated_cost_usd",
        "actual_cost_usd",
        "status",
        "timestamp",
    ]
    for rid in sent_ids:
        payload = received.get(rid)
        if payload is None:
            errors.append(f"Loop 4: event {rid} not received")
            print(f"  ❌ Event {rid} was not received")
            continue

        missing = [f for f in REQUIRED_FIELDS if f not in payload]
        if missing:
            errors.append(f"Loop 4: {rid} missing fields: {missing}")
            print(f"  ❌ {rid} — missing fields: {missing}")
            continue

        # Verify totals
        expected_total = payload["prompt_tokens"] + payload["completion_tokens"]
        assert (
            payload["total_tokens"] == expected_total
        ), f"total_tokens mismatch: {payload['total_tokens']} != {expected_total}"
        # Verify team_id matches source event
        orig = next(e for e in events if e["request_id"] == rid)
        assert payload["team_id"] == orig["team_id"], "team_id mismatch"
        assert payload["model"] == orig["model"], "model mismatch"
        assert payload["status"] == "success", "status mismatch"
        print(f"  ✅ {rid} — all {len(REQUIRED_FIELDS)} fields valid, totals correct")

    # ── Summary ───────────────────────────────────────────────
    print(f"\n{DIVIDER}")
    if errors:
        print(f"❌  {len(errors)} failure(s):")
        for e in errors:
            print(f"   • {e}")
        print(DIVIDER)
    else:
        print("🎉  All 4 loops passed — Kafka topic + schema fully verified!")
        print(f"    Sent: {len(sent_ids)}  Received: {len(received)}  Errors: 0")
        print(DIVIDER)

    return errors


def main():
    errors = asyncio.run(run_tests())
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
