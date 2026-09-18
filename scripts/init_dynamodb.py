"""
Aperture — DynamoDB Single-Table Schema Initialisation Script
Person C: Run this once to create the table and seed test data.

Usage (local, DynamoDB running via docker-compose):
    python scripts/init_dynamodb.py

Requirements:
    pip install boto3

The single table is named: aperture_data
Primary Key:
    PK (String) — Partition Key
    SK (String) — Sort Key

── Access Patterns & Key Patterns ────────────────────────────────────────────

  Entity              PK                    SK                    Purpose
  ──────────────────────────────────────────────────────────────────────────
  Key Metadata        KEY#<key_id>          METADATA              Virtual key details (role, team, budget)
  Key Usage Log       KEY#<key_id>          USAGE#<iso_timestamp> Per-request usage record
  Team Spend Agg.     TEAM#<team_id>        SPEND#<YYYY-MM>       Running monthly spend aggregate
  Idempotency Marker  PROCESSED#<req_id>    MARKER                Prevents double-spend on Kafka replay

── GSIs ──────────────────────────────────────────────────────────────────────

  GSI1: team_id-index
    GSI1PK = team_id, GSI1SK = SK
    Purpose: "give me all keys belonging to team X" — used by dashboard
             and for team-level budget enforcement fallback

── Attribute Reference ──────────────────────────────────────────────────────

  KEY METADATA item:
    key_id        str   sk-gw-<random>  — the virtual key value
    team_id       str   e.g. "engineering"
    role          str   "admin" | "team_lead" | "developer"
    budget_limit  str   monthly limit in USD, e.g. "100.00"  (stored as str for DynamoDB precision)
    is_active     bool  False = revoked key
    created_at    str   ISO 8601
    name          str   human-readable label, e.g. "Alice's cursor key"
    GSI1PK        str   = team_id  (for team-level queries)
    GSI1SK        str   = SK (METADATA)

  USAGE LOG item:
    request_id       str
    model            str   e.g. "claude-sonnet-4-6"
    prompt_tokens    int
    completion_tokens int
    total_tokens     int
    actual_cost_usd  str   e.g. "0.0120"
    status           str   "success" | "error" | "partial"
    timestamp        str   ISO 8601
    GSI1PK           str   = team_id (for team-level usage queries)
    GSI1SK           str   = SK (USAGE#<ts>)

  TEAM SPEND item:
    team_id              str
    month                str   "YYYY-MM"
    total_spend_usd      str   running sum, e.g. "12.3400"
    total_requests       int
    total_tokens         int
    requests_blocked     int   count of budget-rejected requests (great demo metric!)
    last_updated         str   ISO 8601

  PROCESSED MARKER item:
    request_id    str
    processed_at  str   ISO 8601
    TTL           int   Unix timestamp — expires in 30 days (DynamoDB TTL attribute)
"""

import boto3
import json
import os
import sys
import time
from datetime import datetime, timezone, timedelta
from decimal import Decimal

# ─── Config ────────────────────────────────────────────────────────────────
DYNAMODB_ENDPOINT = os.getenv("DYNAMODB_ENDPOINT", "http://localhost:8001")
AWS_REGION = os.getenv("AWS_DEFAULT_REGION", "us-east-1")
TABLE_NAME = "aperture_data"


# ─── Client ────────────────────────────────────────────────────────────────
def get_dynamodb_client():
    """Return a boto3 DynamoDB resource pointed at DynamoDB Local."""
    return boto3.resource(
        "dynamodb",
        endpoint_url=DYNAMODB_ENDPOINT,
        region_name=AWS_REGION,
        # DynamoDB Local accepts any credentials — these are just placeholders
        aws_access_key_id="local",
        aws_secret_access_key="local",
    )


# ─── Table Creation ─────────────────────────────────────────────────────────
def create_table(dynamodb) -> None:
    """
    Create the aperture_data single table with:
      - Composite primary key: PK (hash) + SK (range)
      - GSI1: team_id-index for cross-team queries (dashboard, bulk budget ops)
    """
    existing = [t.name for t in dynamodb.tables.all()]
    if TABLE_NAME in existing:
        print(f"✅  Table '{TABLE_NAME}' already exists — skipping creation.")
        return

    print(f"🔨  Creating table '{TABLE_NAME}'...")
    table = dynamodb.create_table(
        TableName=TABLE_NAME,
        # ── Primary Key ───────────────────────────────────────────────────
        KeySchema=[
            {"AttributeName": "PK", "KeyType": "HASH"},  # Partition Key
            {"AttributeName": "SK", "KeyType": "RANGE"},  # Sort Key
        ],
        AttributeDefinitions=[
            {"AttributeName": "PK", "AttributeType": "S"},  # String
            {"AttributeName": "SK", "AttributeType": "S"},  # String
            {"AttributeName": "GSI1PK", "AttributeType": "S"},  # GSI Partition Key
            {"AttributeName": "GSI1SK", "AttributeType": "S"},  # GSI Sort Key
        ],
        # ── Global Secondary Indexes ──────────────────────────────────────
        GlobalSecondaryIndexes=[
            {
                "IndexName": "team_id-index",
                "KeySchema": [
                    {"AttributeName": "GSI1PK", "KeyType": "HASH"},
                    {"AttributeName": "GSI1SK", "KeyType": "RANGE"},
                ],
                "Projection": {"ProjectionType": "ALL"},
                "ProvisionedThroughput": {
                    "ReadCapacityUnits": 5,
                    "WriteCapacityUnits": 5,
                },
            }
        ],
        # ── Throughput (DynamoDB Local ignores this, but required by API) ─
        ProvisionedThroughput={
            "ReadCapacityUnits": 5,
            "WriteCapacityUnits": 5,
        },
    )

    # Wait for table to be active — use manual poll because DynamoDB Local
    # doesn't reliably implement the boto3 table_exists waiter
    client = dynamodb.meta.client
    for attempt in range(10):
        try:
            status = client.describe_table(TableName=TABLE_NAME)["Table"]["TableStatus"]
            if status == "ACTIVE":
                break
        except client.exceptions.ResourceNotFoundException:
            pass
        print(
            f"   ⏳  Waiting for table to become ACTIVE (attempt {attempt + 1}/10)..."
        )
        time.sleep(1)
    else:
        raise RuntimeError("Table did not become ACTIVE within 10 seconds")
    print(f"✅  Table '{TABLE_NAME}' created and ACTIVE.")

    # Enable TTL on 'TTL' attribute
    try:
        client.update_time_to_live(
            TableName=TABLE_NAME,
            TimeToLiveSpecification={"Enabled": True, "AttributeName": "TTL"},
        )
        print("✅  TTL enabled on attribute 'TTL'.")
    except Exception as e:
        print(f"   ⚠️  Could not enable TTL: {e}")


# ─── Seed Data ─────────────────────────────────────────────────────────────
def seed_test_data(dynamodb, force: bool = False) -> None:
    """
    Insert realistic seed data for local development and demo.
    This lets Person B and the dashboard work immediately without having to
    manually create keys via API.

    Seed data:
      - 2 teams: engineering, marketing
      - 3 virtual keys: 1 admin, 1 team_lead, 1 developer
      - 2 spend aggregates (engineering & marketing, current month)
    """
    table = dynamodb.Table(TABLE_NAME)
    now = datetime.now(timezone.utc).isoformat()
    current_month = datetime.now(timezone.utc).strftime("%Y-%m")

    print("🌱  Seeding test data...")

    items = [
        # ── Key 1: Admin key (engineering team) ─────────────────────────
        {
            "PK": "KEY#sk-gw-admin-001",
            "SK": "METADATA",
            "key_id": "sk-gw-admin-001",
            "name": "Admin Master Key",
            "team_id": "engineering",
            "role": "admin",
            "budget_limit": Decimal("500.00"),  # $500/month
            "is_active": True,
            "created_at": now,
            # GSI attributes — enables "list all keys for team X"
            "GSI1PK": "engineering",
            "GSI1SK": "METADATA",
        },
        # ── Key 2: Team Lead key (engineering) ──────────────────────────
        {
            "PK": "KEY#sk-gw-eng-lead-002",
            "SK": "METADATA",
            "key_id": "sk-gw-eng-lead-002",
            "name": "Engineering Lead Key",
            "team_id": "engineering",
            "role": "team_lead",
            "budget_limit": Decimal("200.00"),
            "is_active": True,
            "created_at": now,
            "GSI1PK": "engineering",
            "GSI1SK": "METADATA",
        },
        # ── Key 3: Developer key (marketing team) ───────────────────────
        {
            "PK": "KEY#sk-gw-mktg-dev-003",
            "SK": "METADATA",
            "key_id": "sk-gw-mktg-dev-003",
            "name": "Marketing Dev Key",
            "team_id": "marketing",
            "role": "developer",
            "budget_limit": Decimal("50.00"),  # low limit for marketing
            "is_active": True,
            "created_at": now,
            "GSI1PK": "marketing",
            "GSI1SK": "METADATA",
        },
        # ── Team Spend Aggregate — engineering (current month) ───────────
        {
            "PK": "TEAM#engineering",
            "SK": f"SPEND#{current_month}",
            "team_id": "engineering",
            "month": current_month,
            "total_spend_usd": Decimal(
                "12.3400"
            ),  # Decimal for native DynamoDB atomic increments
            "total_requests": 48,
            "total_tokens": 125000,
            "requests_blocked": 2,  # how many requests were killed by budget
            "last_updated": now,
        },
        # ── Team Spend Aggregate — marketing (current month) ─────────────
        {
            "PK": "TEAM#marketing",
            "SK": f"SPEND#{current_month}",
            "team_id": "marketing",
            "month": current_month,
            "total_spend_usd": Decimal("3.8700"),
            "total_requests": 14,
            "total_tokens": 31500,
            "requests_blocked": 1,
            "last_updated": now,
        },
    ]

    for item in items:
        try:
            if force:
                table.put_item(Item=item)
                print(f"   ➕  Updated (forced): {item['PK']} / {item['SK']}")
            else:
                table.put_item(
                    Item=item,
                    ConditionExpression="attribute_not_exists(PK)",
                )
                print(f"   ➕  Inserted: {item['PK']} / {item['SK']}")
        except dynamodb.meta.client.exceptions.ConditionalCheckFailedException:
            # Overwrite item with Decimal precision
            table.put_item(Item=item)
            print(
                f"   🔄  Refreshed with Decimal precision: {item['PK']} / {item['SK']}"
            )

    print("✅  Seed data complete.")


# ─── Schema Verification ────────────────────────────────────────────────────
def verify_schema(dynamodb) -> bool:
    """
    Post-creation verification: reads back the table definition and a few
    seed items to confirm everything is correct.
    Returns True if all checks pass.
    """
    print("\n🔍  Verifying schema...")
    all_passed = True
    client = dynamodb.meta.client

    # Check 1: Table exists and is active
    try:
        desc = client.describe_table(TableName=TABLE_NAME)["Table"]
        status = desc["TableStatus"]
        if status == "ACTIVE":
            print(f"   ✅  Table status: {status}")
        else:
            print(f"   ❌  Table status unexpected: {status}")
            all_passed = False
    except Exception as e:
        print(f"   ❌  Could not describe table: {e}")
        return False

    # Check 2: Primary key schema correct
    ks = {k["AttributeName"]: k["KeyType"] for k in desc["KeySchema"]}
    if ks.get("PK") == "HASH" and ks.get("SK") == "RANGE":
        print("   ✅  Primary key schema: PK (HASH) + SK (RANGE)")
    else:
        print(f"   ❌  Key schema wrong: {ks}")
        all_passed = False

    # Check 3: GSI exists
    gsi_names = [g["IndexName"] for g in desc.get("GlobalSecondaryIndexes", [])]
    if "team_id-index" in gsi_names:
        print("   ✅  GSI 'team_id-index' present")
    else:
        print(f"   ❌  GSI 'team_id-index' missing. Found: {gsi_names}")
        all_passed = False

    # Check 4: Read back seed items
    table = dynamodb.Table(TABLE_NAME)
    checks = [
        {"PK": "KEY#sk-gw-admin-001", "SK": "METADATA", "label": "Admin key metadata"},
        {
            "PK": "KEY#sk-gw-mktg-dev-003",
            "SK": "METADATA",
            "label": "Marketing dev key",
        },
        {
            "PK": "TEAM#engineering",
            "SK": f"SPEND#{datetime.now(timezone.utc).strftime('%Y-%m')}",
            "label": "Engineering spend aggregate",
        },
    ]
    for check in checks:
        resp = table.get_item(Key={"PK": check["PK"], "SK": check["SK"]})
        if "Item" in resp:
            print(f"   ✅  {check['label']}: readable")
        else:
            print(f"   ❌  {check['label']}: NOT FOUND")
            all_passed = False

    # Check 5: Confirm budget_limit and role fields present on a key item
    resp = table.get_item(Key={"PK": "KEY#sk-gw-admin-001", "SK": "METADATA"})
    item = resp.get("Item", {})
    required_fields = [
        "key_id",
        "team_id",
        "role",
        "budget_limit",
        "is_active",
        "GSI1PK",
    ]
    missing = [f for f in required_fields if f not in item]
    if not missing:
        print(f"   ✅  Key metadata has all required fields: {required_fields}")
    else:
        print(f"   ❌  Key metadata missing fields: {missing}")
        all_passed = False

    return all_passed


# ─── Describe Schema (for documentation / sharing with Person B) ─────────────
def print_schema_summary() -> None:
    print("""
╔══════════════════════════════════════════════════════════════════════╗
║       APERTURE — DynamoDB Single-Table Schema (aperture_data)       ║
╠══════════════════════════════════════════════════════════════════════╣
║  PRIMARY KEY: PK (String, Partition) + SK (String, Sort)            ║
║  GSI1: team_id-index  →  GSI1PK (team_id) + GSI1SK                 ║
╠════════════════════════════════╦═════════════════════╦══════════════╣
║  Entity                        ║  PK                 ║  SK          ║
╠════════════════════════════════╬═════════════════════╬══════════════╣
║  Virtual Key Metadata          ║  KEY#<key_id>        ║  METADATA    ║
║  Per-request Usage Log         ║  KEY#<key_id>        ║  USAGE#<ts>  ║
║  Team Monthly Spend Aggregate  ║  TEAM#<team_id>      ║  SPEND#YYYY-MM║
║  Idempotency Marker            ║  PROCESSED#<req_id>  ║  MARKER      ║
╚════════════════════════════════╩═════════════════════╩══════════════╝

SHARED WITH PERSON B:
  - Read key metadata: GetItem(PK=KEY#<key_id>, SK=METADATA)
  - Create key: PutItem with all fields above
  - Revoke key: UpdateItem → set is_active = False

SHARED WITH PERSON A:
  - request_id field in USAGE items must match request.state.request_id
""")


# ─── Main ────────────────────────────────────────────────────────────────────
def main():
    print("=" * 60)
    print("  Aperture DynamoDB Init — Person C")
    print(f"  Endpoint: {DYNAMODB_ENDPOINT}")
    print("=" * 60)

    print_schema_summary()

    dynamodb = get_dynamodb_client()

    # Step 1: Create table
    create_table(dynamodb)

    # Step 2: Seed test data
    seed_test_data(dynamodb)

    # Step 3: Verify schema
    passed = verify_schema(dynamodb)

    print("\n" + "=" * 60)
    if passed:
        print("🎉  All checks PASSED — DynamoDB schema is ready!")
        print(f"    Table: {TABLE_NAME} @ {DYNAMODB_ENDPOINT}")
        print("    Person B can now read key metadata via GetItem.")
        print("    Consumer can now write usage events and aggregates.")
    else:
        print("💥  Some checks FAILED — review errors above.")
        sys.exit(1)
    print("=" * 60)


if __name__ == "__main__":
    main()
