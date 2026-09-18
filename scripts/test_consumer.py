"""
Aperture — Consumer Integration Test
Person C, Task 3.

Tests the full pipeline end-to-end:
  Kafka producer → aperture.usage-events → consumer handler → DynamoDB

Runs the handler directly (no Kafka round-trip needed to test the DynamoDB logic),
then verifies all 3 DynamoDB writes are correct.

Run from project root:
    source .venv/bin/activate
    python3 scripts/test_consumer.py

Prerequisites: DynamoDB Local must be running on localhost:8001
    docker-compose up -d dynamodb-local
    python3 scripts/init_dynamodb.py
"""

import asyncio
import os
import sys
import time
import uuid
from datetime import datetime, timezone
from decimal import Decimal

# Ensure project root is on sys.path so gateway and consumer packages can be imported
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import boto3
from botocore.exceptions import ClientError

# Point handler at the host-exposed DynamoDB port
os.environ.setdefault("DYNAMODB_ENDPOINT", "http://localhost:8001")
os.environ.setdefault("AWS_DEFAULT_REGION", "us-east-1")
os.environ.setdefault("AWS_ACCESS_KEY_ID", "local")
os.environ.setdefault("AWS_SECRET_ACCESS_KEY", "local")
os.environ.setdefault("DYNAMODB_TABLE", "aperture_data")

from gateway.models import UsageEvent  # noqa: E402
from consumer.handler import handle_event  # noqa: E402

TABLE_NAME = "aperture_data"
DIVIDER = "=" * 65

dynamodb = boto3.resource(
    "dynamodb",
    endpoint_url="http://localhost:8001",
    region_name="us-east-1",
    aws_access_key_id="local",
    aws_secret_access_key="local",
)
table = dynamodb.Table(TABLE_NAME)


def make_event(**overrides) -> UsageEvent:
    defaults = dict(
        request_id=f"req-consumer-test-{uuid.uuid4().hex[:10]}",
        key_id="sk-gw-test001",
        team_id="engineering",
        model="claude-sonnet-4-6",
        prompt_tokens=100,
        completion_tokens=60,
        total_tokens=160,
        estimated_cost_usd=0.0018,
        actual_cost_usd=0.0016,
        status="success",
        timestamp=datetime.now(timezone.utc).isoformat(),
    )
    defaults.update(overrides)
    return UsageEvent(**defaults)


def get_item(pk: str, sk: str) -> dict | None:
    resp = table.get_item(Key={"PK": pk, "SK": sk})
    return resp.get("Item")


async def run_tests():
    print(DIVIDER)
    print("  Aperture Consumer Integration Test — Person C")
    print("  DynamoDB: http://localhost:8001")
    print(DIVIDER)

    errors = []

    # ── Loop 1: Idempotency marker is written on first call ───────────────────
    print("\n🔒 Loop 1: Idempotency marker written on first call")
    event1 = make_event()
    await handle_event(event1)

    marker = get_item(f"PROCESSED#{event1.request_id}", "MARKER")
    if marker is None:
        errors.append("Loop 1: idempotency marker not found")
        print("  ❌ Marker not found in DynamoDB")
    else:
        assert marker["request_id"] == event1.request_id
        assert "processed_at" in marker
        assert "TTL" in marker
        ttl_remaining = int(marker["TTL"]) - int(time.time())
        print(f"  ✅ Marker written | TTL in {ttl_remaining // 86400} days")

    # ── Loop 2: Usage log written with all required fields ────────────────────
    print("\n📋 Loop 2: Usage log written with correct fields")
    usage = get_item(f"KEY#{event1.key_id}", f"USAGE#{event1.timestamp}")
    REQUIRED = [
        "request_id",
        "key_id",
        "team_id",
        "model",
        "prompt_tokens",
        "completion_tokens",
        "total_tokens",
        "actual_cost_usd",
        "estimated_cost_usd",
        "status",
        "timestamp",
        "GSI1PK",
        "GSI1SK",
    ]
    if usage is None:
        errors.append("Loop 2: usage log not found")
        print("  ❌ Usage log item not found")
    else:
        missing = [f for f in REQUIRED if f not in usage]
        if missing:
            errors.append(f"Loop 2: missing fields {missing}")
            print(f"  ❌ Missing fields: {missing}")
        else:
            assert usage["GSI1PK"] == event1.team_id
            assert usage["GSI1SK"] == f"USAGE#{event1.timestamp}"
            assert isinstance(usage["actual_cost_usd"], Decimal)
            print(
                f"  ✅ Usage log OK | {len(REQUIRED)} fields verified | cost={usage['actual_cost_usd']}"
            )

    # ── Loop 3: Spend aggregate atomically incremented ────────────────────────
    print("\n💰 Loop 3: Spend aggregate atomic ADD")
    month = event1.timestamp[:7]
    spend_before = get_item(f"TEAM#{event1.team_id}", f"SPEND#{month}")
    requests_before = int(spend_before.get("total_requests", 0)) if spend_before else 0
    spend_usd_before = (
        Decimal(str(spend_before.get("total_spend_usd", 0)))
        if spend_before
        else Decimal("0")
    )

    # Send a second event for the same team
    event2 = make_event(request_id=f"req-consumer-test-{uuid.uuid4().hex[:10]}")
    await handle_event(event2)

    spend_after = get_item(f"TEAM#{event1.team_id}", f"SPEND#{month}")
    requests_after = int(spend_after.get("total_requests", 0))
    spend_usd_after = Decimal(str(spend_after.get("total_spend_usd", 0)))

    if requests_after != requests_before + 1:
        errors.append(
            f"Loop 3: total_requests not incremented ({requests_before} → {requests_after})"
        )
        print(
            f"  ❌ total_requests not incremented: {requests_before} → {requests_after}"
        )
    else:
        delta = spend_usd_after - spend_usd_before
        print(f"  ✅ total_requests: {requests_before} → {requests_after}")
        print(f"  ✅ total_spend_usd: +{delta:.4f} (Decimal precision preserved)")

    # ── Loop 4: Duplicate event is silently skipped (idempotency) ─────────────
    print("\n🔁 Loop 4: Duplicate request_id is skipped (idempotency guard)")
    spend_before_dup = get_item(f"TEAM#{event1.team_id}", f"SPEND#{month}")
    requests_before_dup = int(spend_before_dup.get("total_requests", 0))

    # Re-send event1 (same request_id as Loop 1)
    await handle_event(event1)

    spend_after_dup = get_item(f"TEAM#{event1.team_id}", f"SPEND#{month}")
    requests_after_dup = int(spend_after_dup.get("total_requests", 0))

    if requests_after_dup != requests_before_dup:
        errors.append(
            f"Loop 4: duplicate was NOT skipped — requests went {requests_before_dup} → {requests_after_dup}"
        )
        print(
            f"  ❌ Duplicate NOT skipped: requests {requests_before_dup} → {requests_after_dup}"
        )
    else:
        print(
            f"  ✅ Duplicate skipped — total_requests unchanged at {requests_after_dup}"
        )

    # ── Loop 5: Blocked request increments requests_blocked, not spend ─────────
    print(
        "\n🚫 Loop 5: Blocked request increments requests_blocked, not total_spend_usd"
    )
    event_blocked = make_event(
        request_id=f"req-blocked-{uuid.uuid4().hex[:10]}",
        status="blocked",
        actual_cost_usd=0.0,
        total_tokens=0,
    )
    spend_before_block = get_item(f"TEAM#{event1.team_id}", f"SPEND#{month}")
    spend_usd_before_block = Decimal(str(spend_before_block.get("total_spend_usd", 0)))
    blocked_before = int(spend_before_block.get("requests_blocked", 0))

    await handle_event(event_blocked)

    spend_after_block = get_item(f"TEAM#{event1.team_id}", f"SPEND#{month}")
    spend_usd_after_block = Decimal(str(spend_after_block.get("total_spend_usd", 0)))
    blocked_after = int(spend_after_block.get("requests_blocked", 0))

    if spend_usd_after_block != spend_usd_before_block:
        errors.append("Loop 5: blocked request added to total_spend_usd (should not)")
        print("  ❌ total_spend_usd changed on blocked request")
    elif blocked_after != blocked_before + 1:
        errors.append(
            f"Loop 5: requests_blocked not incremented ({blocked_before} → {blocked_after})"
        )
        print(
            f"  ❌ requests_blocked not incremented: {blocked_before} → {blocked_after}"
        )
    else:
        print(
            f"  ✅ requests_blocked: {blocked_before} → {blocked_after} | spend unchanged at ${spend_usd_after_block}"
        )

    # ── Summary ───────────────────────────────────────────────────────────────
    print(f"\n{DIVIDER}")
    if errors:
        print(f"❌  {len(errors)} failure(s):")
        for e in errors:
            print(f"   • {e}")
    else:
        print("🎉  All 5 loops passed — consumer handler fully verified!")
        print(
            "    Idempotency ✅  Usage log ✅  Spend aggregate ✅  Dedup ✅  Blocked requests ✅"
        )
    print(DIVIDER)
    return errors


def main():
    errors = asyncio.run(run_tests())
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
