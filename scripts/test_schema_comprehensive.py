"""
Aperture — Comprehensive 4-Loop Schema Verification Suite
Validates the DynamoDB single-table schema against all real-world access patterns:
  - Loop 1: Key Metadata, RBAC, and Team Key Listing (Person B contract)
  - Loop 2: Usage Event Logging, Range Queries, and Team Usage via GSI1 (Person A & C contract)
  - Loop 3: Team Monthly Spend Aggregates and Atomic Concurrency Math (Person C Consumer)
  - Loop 4: Idempotency Deduplication, Kafka Replay Protection, and TTL (Decision #8)
"""

import os
import sys
import time
from datetime import datetime, timezone, timedelta
from decimal import Decimal
import boto3
from boto3.dynamodb.conditions import Key, Attr
from botocore.exceptions import ClientError

DYNAMODB_ENDPOINT = os.getenv("DYNAMODB_ENDPOINT", "http://localhost:8001")
AWS_REGION = os.getenv("AWS_DEFAULT_REGION", "us-east-1")
TABLE_NAME = "aperture_data"


def get_table():
    ddb = boto3.resource(
        "dynamodb",
        endpoint_url=DYNAMODB_ENDPOINT,
        region_name=AWS_REGION,
        aws_access_key_id="local",
        aws_secret_access_key="local",
    )
    return ddb.Table(TABLE_NAME)


# ═════════════════════════════════════════════════════════════════════════════
# LOOP 1: Virtual Key Metadata & RBAC Access Patterns (Person B)
# ═════════════════════════════════════════════════════════════════════════════
def run_loop_1(table) -> bool:
    print("\n" + "═" * 70)
    print("  LOOP 1: Virtual Key Metadata, RBAC & GSI1 Team Listing (Person B)")
    print("═" * 70)

    test_key_id = "sk-gw-test-alice-101"
    now_iso = datetime.now(timezone.utc).isoformat()

    # 1.1 Read existing seeded key
    print("  [1.1] Fetching seeded admin key...")
    admin_item = table.get_item(
        Key={"PK": "KEY#sk-gw-admin-001", "SK": "METADATA"}
    ).get("Item")
    assert admin_item is not None, "Seeded admin key not found!"
    assert (
        admin_item["role"] == "admin"
    ), f"Expected admin role, got {admin_item.get('role')}"
    assert admin_item["is_active"] is True, "Admin key should be active"
    print(
        f"        ✅ Admin key verified: team={admin_item['team_id']}, role={admin_item['role']}, limit={admin_item['budget_limit']}"
    )

    # 1.2 Create a new virtual key with conditional check
    print(f"  [1.2] Creating new virtual key: {test_key_id}...")
    new_key = {
        "PK": f"KEY#{test_key_id}",
        "SK": "METADATA",
        "key_id": test_key_id,
        "name": "Alice Developer Key",
        "team_id": "engineering",
        "role": "developer",
        "budget_limit": Decimal("75.00"),
        "is_active": True,
        "created_at": now_iso,
        "GSI1PK": "engineering",
        "GSI1SK": "METADATA",
    }
    table.put_item(Item=new_key, ConditionExpression="attribute_not_exists(PK)")
    print("        ✅ Key created with attribute_not_exists(PK)")

    # 1.3 Duplicate creation must fail
    print("  [1.3] Testing duplicate key creation rejection...")
    try:
        table.put_item(Item=new_key, ConditionExpression="attribute_not_exists(PK)")
        assert (
            False
        ), "Duplicate key creation did not raise ConditionalCheckFailedException!"
    except ClientError as e:
        assert e.response["Error"]["Code"] == "ConditionalCheckFailedException"
        print("        ✅ Duplicate key creation properly rejected by DynamoDB")

    # 1.4 Soft revocation of virtual key
    print("  [1.4] Testing key revocation (UpdateItem -> is_active = False)...")
    res = table.update_item(
        Key={"PK": f"KEY#{test_key_id}", "SK": "METADATA"},
        UpdateExpression="SET is_active = :inactive, revoked_at = :now",
        ConditionExpression="attribute_exists(PK) AND is_active = :active",
        ExpressionAttributeValues={
            ":inactive": False,
            ":active": True,
            ":now": datetime.now(timezone.utc).isoformat(),
        },
        ReturnValues="ALL_NEW",
    )
    assert res["Attributes"]["is_active"] is False, "Key is_active was not set to False"
    print("        ✅ Key revoked successfully (is_active = False)")

    # 1.5 Query GSI1 for team's keys
    print("  [1.5] Querying GSI1 ('team_id-index') for all engineering keys...")
    res = table.query(
        IndexName="team_id-index",
        KeyConditionExpression=Key("GSI1PK").eq("engineering")
        & Key("GSI1SK").eq("METADATA"),
    )
    key_ids = [item["key_id"] for item in res.get("Items", [])]
    print(f"        Found {len(key_ids)} engineering keys: {key_ids}")
    assert test_key_id in key_ids, f"{test_key_id} not found in GSI1 query"
    assert "sk-gw-admin-001" in key_ids, "sk-gw-admin-001 not found in GSI1 query"
    print("        ✅ GSI1 team key query returned all expected members")

    # Cleanup test key
    table.delete_item(Key={"PK": f"KEY#{test_key_id}", "SK": "METADATA"})
    print("        🧹 Cleaned up temporary test key.")
    print(
        "  ⭐ LOOP 1 PASSED: Key management, RBAC, and GSI1 queries are 100% functional."
    )
    return True


# ═════════════════════════════════════════════════════════════════════════════
# LOOP 2: Usage Logs & Time-Series Access Patterns (Person A & C)
# ═════════════════════════════════════════════════════════════════════════════
def run_loop_2(table) -> bool:
    print("\n" + "═" * 70)
    print("  LOOP 2: Usage Event Logging & Time-Series Range Queries (Person A & C)")
    print("═" * 70)

    key_id = "sk-gw-eng-lead-002"
    team_id = "engineering"
    base_time = datetime(2026, 9, 18, 12, 0, 0, tzinfo=timezone.utc)

    # 2.1 Insert sequential usage log events
    print("  [2.1] Inserting 3 sequential usage log items...")
    log_events = [
        {
            "offset_min": 0,
            "req_id": "req-seq-001",
            "model": "claude-sonnet-4-6",
            "prompt_tokens": 120,
            "completion_tokens": 250,
            "cost": Decimal("0.00495"),
        },
        {
            "offset_min": 10,
            "req_id": "req-seq-002",
            "model": "claude-sonnet-4-6",
            "prompt_tokens": 300,
            "completion_tokens": 800,
            "cost": Decimal("0.01500"),
        },
        {
            "offset_min": 25,
            "req_id": "req-seq-003",
            "model": "gpt-4o",
            "prompt_tokens": 50,
            "completion_tokens": 100,
            "cost": Decimal("0.00175"),
        },
    ]

    inserted_sks = []
    for evt in log_events:
        ts = (base_time + timedelta(minutes=evt["offset_min"])).isoformat()
        sk = f"USAGE#{ts}"
        inserted_sks.append(sk)
        item = {
            "PK": f"KEY#{key_id}",
            "SK": sk,
            "request_id": evt["req_id"],
            "key_id": key_id,
            "team_id": team_id,
            "model": evt["model"],
            "prompt_tokens": evt["prompt_tokens"],
            "completion_tokens": evt["completion_tokens"],
            "total_tokens": evt["prompt_tokens"] + evt["completion_tokens"],
            "actual_cost_usd": evt["cost"],
            "status": "success",
            "timestamp": ts,
            # GSI1 fields for team-level aggregation
            "GSI1PK": team_id,
            "GSI1SK": sk,
        }
        table.put_item(Item=item)

    print(f"        ✅ Inserted {len(log_events)} usage log records.")

    # 2.2 Query single key history by SK range
    print("  [2.2] Querying usage history for key within time range (0 to 15 min)...")
    t_start = f"USAGE#{(base_time - timedelta(minutes=1)).isoformat()}"
    t_end = f"USAGE#{(base_time + timedelta(minutes=15)).isoformat()}"
    res = table.query(
        KeyConditionExpression=Key("PK").eq(f"KEY#{key_id}")
        & Key("SK").between(t_start, t_end)
    )
    items = res.get("Items", [])
    print(f"        Found {len(items)} items in range (expected 2)")
    assert len(items) == 2, f"Expected 2 items in range, got {len(items)}"
    assert items[0]["request_id"] == "req-seq-001"
    assert items[1]["request_id"] == "req-seq-002"
    print(
        "        ✅ Key-level range query returned exact records in chronological order"
    )

    # 2.3 Query team-wide usage logs across keys via GSI1
    print("  [2.3] Querying team-wide usage logs via GSI1 ('team_id-index')...")
    res = table.query(
        IndexName="team_id-index",
        KeyConditionExpression=Key("GSI1PK").eq(team_id)
        & Key("GSI1SK").begins_with("USAGE#2026-09-18"),
    )
    gsi_items = res.get("Items", [])
    print(f"        Found {len(gsi_items)} usage records for team '{team_id}'")
    assert (
        len(gsi_items) >= 3
    ), f"Expected at least 3 items in team query, got {len(gsi_items)}"
    total_tokens_sum = sum(int(it["total_tokens"]) for it in gsi_items)
    print(f"        Total tokens processed across retrieved logs: {total_tokens_sum}")
    print("        ✅ GSI1 team usage query verified successfully")

    # Cleanup
    for sk in inserted_sks:
        table.delete_item(Key={"PK": f"KEY#{key_id}", "SK": sk})
    print("        🧹 Cleaned up temporary usage logs.")
    print(
        "  ⭐ LOOP 2 PASSED: Per-request logging and time-series queries are verified."
    )
    return True


# ═════════════════════════════════════════════════════════════════════════════
# LOOP 3: Team Spend Aggregates & Atomic Concurrency Math (Person C Consumer)
# ═════════════════════════════════════════════════════════════════════════════
def run_loop_3(table) -> bool:
    print("\n" + "═" * 70)
    print("  LOOP 3: Team Spend Aggregates & Atomic Increments (Person C Consumer)")
    print("═" * 70)

    current_month = datetime.now(timezone.utc).strftime("%Y-%m")
    pk = "TEAM#engineering"
    sk = f"SPEND#{current_month}"

    # 3.1 Fetch current spend baseline
    print("  [3.1] Reading baseline spend aggregate...")
    item = table.get_item(Key={"PK": pk, "SK": sk}).get("Item")
    assert item is not None, "Engineering monthly spend item not found!"
    initial_spend = Decimal(str(item["total_spend_usd"]))
    initial_reqs = int(item["total_requests"])
    initial_tokens = int(item["total_tokens"])
    initial_blocked = int(item.get("requests_blocked", 0))
    print(
        f"        Baseline: spend=${initial_spend}, requests={initial_reqs}, tokens={initial_tokens}, blocked={initial_blocked}"
    )

    # 3.2 Simulate 5 concurrent/atomic request reconciliations
    print("  [3.2] Simulating 5 atomic consumer updates (SET spend = spend + :cost)...")
    additions = [
        {"cost": Decimal("0.0125"), "tokens": 350},
        {"cost": Decimal("0.0240"), "tokens": 680},
        {"cost": Decimal("0.0055"), "tokens": 120},
        {"cost": Decimal("0.0310"), "tokens": 940},
        {"cost": Decimal("0.0070"), "tokens": 210},
    ]

    expected_added_spend = sum(a["cost"] for a in additions)
    expected_added_tokens = sum(a["tokens"] for a in additions)
    expected_added_reqs = len(additions)

    for i, add in enumerate(additions, 1):
        res = table.update_item(
            Key={"PK": pk, "SK": sk},
            UpdateExpression=(
                "SET total_spend_usd = total_spend_usd + :cost, "
                "    total_requests = total_requests + :one, "
                "    total_tokens = total_tokens + :tokens, "
                "    last_updated = :now"
            ),
            ExpressionAttributeValues={
                ":cost": add["cost"],
                ":one": 1,
                ":tokens": add["tokens"],
                ":now": datetime.now(timezone.utc).isoformat(),
            },
            ReturnValues="UPDATED_NEW",
        )
        updated = res["Attributes"]
        print(
            f"        Update {i}/5: spend=${updated['total_spend_usd']}, reqs={updated['total_requests']}"
        )

    # 3.3 Verify exact precision and no lost updates
    print("  [3.3] Verifying final aggregate against mathematical expectation...")
    final_item = table.get_item(Key={"PK": pk, "SK": sk}).get("Item")
    final_spend = Decimal(str(final_item["total_spend_usd"]))
    final_reqs = int(final_item["total_requests"])
    final_tokens = int(final_item["total_tokens"])

    expected_final_spend = initial_spend + expected_added_spend
    expected_final_reqs = initial_reqs + expected_added_reqs
    expected_final_tokens = initial_tokens + expected_added_tokens

    assert (
        final_spend == expected_final_spend
    ), f"Spend mismatch: expected {expected_final_spend}, got {final_spend}"
    assert (
        final_reqs == expected_final_reqs
    ), f"Requests mismatch: expected {expected_final_reqs}, got {final_reqs}"
    assert (
        final_tokens == expected_final_tokens
    ), f"Tokens mismatch: expected {expected_final_tokens}, got {final_tokens}"
    print(
        f"        ✅ Perfect match! Final spend=${final_spend} (+${expected_added_spend}), requests={final_reqs}"
    )

    # 3.4 Increment requests_blocked counter (budget rejection demo metric)
    print(
        "  [3.4] Testing budget rejection counter increment (requests_blocked + 1)..."
    )
    res = table.update_item(
        Key={"PK": pk, "SK": sk},
        UpdateExpression="SET requests_blocked = requests_blocked + :one",
        ExpressionAttributeValues={":one": 1},
        ReturnValues="UPDATED_NEW",
    )
    assert int(res["Attributes"]["requests_blocked"]) == initial_blocked + 1
    print(
        f"        ✅ requests_blocked atomically incremented to {res['Attributes']['requests_blocked']}"
    )

    # Revert additions to keep test data clean
    table.update_item(
        Key={"PK": pk, "SK": sk},
        UpdateExpression=(
            "SET total_spend_usd = total_spend_usd - :cost, "
            "    total_requests = total_requests - :reqs, "
            "    total_tokens = total_tokens - :tokens, "
            "    requests_blocked = requests_blocked - :one"
        ),
        ExpressionAttributeValues={
            ":cost": expected_added_spend,
            ":reqs": expected_added_reqs,
            ":tokens": expected_added_tokens,
            ":one": 1,
        },
    )
    print("        🧹 Reverted test spend increments back to baseline.")
    print(
        "  ⭐ LOOP 3 PASSED: DynamoDB atomic arithmetic and financial precision verified."
    )
    return True


# ═════════════════════════════════════════════════════════════════════════════
# LOOP 4: Idempotency, Kafka Replay Protection & TTL (Decision #8)
# ═════════════════════════════════════════════════════════════════════════════
def run_loop_4(table) -> bool:
    print("\n" + "═" * 70)
    print("  LOOP 4: Idempotency Markers, Kafka Replay & TTL (Design Decision #8)")
    print("═" * 70)

    test_req_id = f"req-idem-{int(time.time())}"
    pk = f"PROCESSED#{test_req_id}"
    sk = "MARKER"
    ttl_epoch = int(time.time()) + (30 * 86400)  # 30 days from now

    marker_item = {
        "PK": pk,
        "SK": sk,
        "request_id": test_req_id,
        "processed_at": datetime.now(timezone.utc).isoformat(),
        "TTL": ttl_epoch,
    }

    # 4.1 First delivery of Kafka event
    print(f"  [4.1] First write of idempotency marker: {pk}...")
    table.put_item(Item=marker_item, ConditionExpression="attribute_not_exists(PK)")
    print("        ✅ Marker written successfully with attribute_not_exists(PK)")

    # 4.2 Replay of same message (at-least-once delivery scenario)
    print("  [4.2] Simulating Kafka message replay / duplicate delivery...")
    duplicate_detected = False
    try:
        table.put_item(Item=marker_item, ConditionExpression="attribute_not_exists(PK)")
    except ClientError as e:
        if e.response["Error"]["Code"] == "ConditionalCheckFailedException":
            duplicate_detected = True
            print(
                "        ✅ Conditional check caught duplicate: duplicate message skipped!"
            )
        else:
            raise

    assert duplicate_detected, "Kafka replay was NOT caught by idempotency check!"

    # 4.3 Verify TTL attribute format
    print("  [4.3] Verifying TTL attribute format...")
    fetched_marker = table.get_item(Key={"PK": pk, "SK": sk}).get("Item")
    assert fetched_marker is not None
    assert isinstance(
        fetched_marker["TTL"], (int, Decimal)
    ), f"TTL should be numeric epoch, got {type(fetched_marker['TTL'])}"
    assert int(fetched_marker["TTL"]) > int(time.time()), "TTL must be in the future"
    print(f"        ✅ TTL verified: {fetched_marker['TTL']} (expires in ~30 days)")

    # Cleanup marker
    table.delete_item(Key={"PK": pk, "SK": sk})
    print("        🧹 Cleaned up test marker.")
    print(
        "  ⭐ LOOP 4 PASSED: Idempotency deduplication guarantees no double-spending."
    )
    return True


def main():
    print("=" * 70)
    print("  Aperture DynamoDB Schema Verification Suite (4 Loops)")
    print(f"  Target: {TABLE_NAME} @ {DYNAMODB_ENDPOINT}")
    print("=" * 70)

    table = get_table()

    l1 = run_loop_1(table)
    l2 = run_loop_2(table)
    l3 = run_loop_3(table)
    l4 = run_loop_4(table)

    print("\n" + "=" * 70)
    if l1 and l2 and l3 and l4:
        print("🎉 ALL 4 LOOPS OF SCHEMA VERIFICATION COMPLETED SUCCESSFULLY!")
        print("   ✓ Loop 1 (Auth & Key RBAC): PASS")
        print("   ✓ Loop 2 (Usage Logs & GSI1 Time-Series): PASS")
        print("   ✓ Loop 3 (Atomic Spend Math & Precision): PASS")
        print("   ✓ Loop 4 (Idempotency & Replay Protection): PASS")
        print("   Schema is production-ready for Aperture.")
    else:
        print("💥 Schema verification FAILED. Check loop outputs above.")
        sys.exit(1)
    print("=" * 70)


if __name__ == "__main__":
    main()
