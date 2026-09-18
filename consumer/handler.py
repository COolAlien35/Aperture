"""
Aperture — Consumer DynamoDB Handler
Person C, Task 3.

For every UsageEvent consumed from Kafka, this module performs 3 DynamoDB writes:

  Write 1 — Idempotency marker (ConditionExpression: attribute_not_exists(PK))
    PK = PROCESSED#<request_id>  SK = MARKER
    → Prevents double-spend if Kafka replays the same event (at-least-once delivery)
    → If this write raises ConditionalCheckFailedException, event is a duplicate → skip

  Write 2 — Per-request usage log
    PK = KEY#<key_id>  SK = USAGE#<timestamp>
    → Raw event data for audit log and per-key time-series queries

  Write 3 — Team monthly spend aggregate (atomic ADD)
    PK = TEAM#<team_id>  SK = SPEND#<YYYY-MM>
    → Increments total_spend_usd, total_requests, total_tokens atomically
    → Uses ADD (not SET) so concurrent writes never race

All boto3 calls are synchronous; they run in a ThreadPoolExecutor so they don't
block the asyncio event loop.
"""

import asyncio
import logging
import os
import time
from datetime import datetime, timezone
from decimal import Decimal
from functools import partial

import boto3
from botocore.exceptions import ClientError

from gateway.models import UsageEvent

logger = logging.getLogger("consumer.handler")

# ── DynamoDB Config ───────────────────────────────────────────────────────────
DYNAMODB_ENDPOINT = os.getenv("DYNAMODB_ENDPOINT", "http://dynamodb-local:8000")
DYNAMODB_REGION = os.getenv("AWS_DEFAULT_REGION", "us-east-1")
DYNAMODB_TABLE = os.getenv("DYNAMODB_TABLE", "aperture_data")

# Idempotency marker TTL: 30 days from now
IDEMPOTENCY_TTL_SECONDS = 30 * 24 * 60 * 60

_dynamodb = None
_table = None


def _get_table():
    """Lazy singleton DynamoDB Table resource."""
    global _dynamodb, _table
    if _table is None:
        _dynamodb = boto3.resource(
            "dynamodb",
            endpoint_url=DYNAMODB_ENDPOINT,
            region_name=DYNAMODB_REGION,
            aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID", "local"),
            aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY", "local"),
        )
        _table = _dynamodb.Table(DYNAMODB_TABLE)
    return _table


# ── Main entry point ──────────────────────────────────────────────────────────


async def handle_event(event: UsageEvent) -> None:
    """
    Process a single UsageEvent: idempotency check → usage log → spend aggregate.
    Runs the synchronous boto3 calls in a thread pool executor.
    """
    loop = asyncio.get_running_loop()
    await loop.run_in_executor(None, partial(_handle_event_sync, event))


def _handle_event_sync(event: UsageEvent) -> None:
    """Synchronous implementation — runs in thread pool."""
    table = _get_table()

    # ── Write 1: Idempotency marker ───────────────────────────────────────────
    if not _write_idempotency_marker(table, event):
        # Already processed — skip remaining writes
        logger.info(
            "Duplicate event skipped (already processed): request_id=%s",
            event.request_id,
        )
        return

    # ── Write 2: Per-request usage log ────────────────────────────────────────
    _write_usage_log(table, event)

    # ── Write 3: Atomic team spend aggregate ─────────────────────────────────
    _update_team_spend(table, event)

    logger.info(
        "Event persisted | request_id=%s team=%s spend=$%.4f",
        event.request_id,
        event.team_id,
        event.actual_cost_usd,
    )


# ── Write 1: Idempotency marker ───────────────────────────────────────────────


def _write_idempotency_marker(table, event: UsageEvent) -> bool:
    """
    Write a PROCESSED#<request_id> marker with attribute_not_exists(PK) guard.

    Returns:
        True  → marker written successfully (event is new, proceed with writes)
        False → ConditionalCheckFailedException (event already processed, skip)
    """
    ttl = int(time.time()) + IDEMPOTENCY_TTL_SECONDS
    try:
        table.put_item(
            Item={
                "PK": f"PROCESSED#{event.request_id}",
                "SK": "MARKER",
                "request_id": event.request_id,
                "processed_at": datetime.now(timezone.utc).isoformat(),
                "TTL": ttl,
            },
            # Only write if this PK does not already exist
            ConditionExpression="attribute_not_exists(PK)",
        )
        return True
    except ClientError as exc:
        if exc.response["Error"]["Code"] == "ConditionalCheckFailedException":
            return False
        # Unexpected DynamoDB error — re-raise so the consumer can log it
        raise


# ── Write 2: Per-request usage log ───────────────────────────────────────────


def _write_usage_log(table, event: UsageEvent) -> None:
    """
    Write the raw UsageEvent to KEY#<key_id> / USAGE#<timestamp>.
    Includes GSI1 attributes so the team dashboard can range-query by team.
    """
    item = {
        "PK": f"KEY#{event.key_id}",
        "SK": f"USAGE#{event.timestamp}",
        "request_id": event.request_id,
        "key_id": event.key_id,
        "team_id": event.team_id,
        "model": event.model,
        "prompt_tokens": event.prompt_tokens,
        "completion_tokens": event.completion_tokens,
        "total_tokens": event.total_tokens,
        # Store as Decimal (DynamoDB Number type) for precision
        "actual_cost_usd": Decimal(str(event.actual_cost_usd)),
        "estimated_cost_usd": Decimal(str(event.estimated_cost_usd)),
        "status": event.status,
        "timestamp": event.timestamp,
        # GSI1 — allows querying all usage for a team
        "GSI1PK": event.team_id,
        "GSI1SK": f"USAGE#{event.timestamp}",
    }
    if event.error_message:
        item["error_message"] = event.error_message

    table.put_item(Item=item)
    logger.debug("Usage log written: KEY#%s / USAGE#%s", event.key_id, event.timestamp)


# ── Write 3: Atomic team spend aggregate ─────────────────────────────────────


def _update_team_spend(table, event: UsageEvent) -> None:
    """
    Atomically increment the TEAM#<team_id> / SPEND#<YYYY-MM> aggregate.

    Uses ADD (not SET) so concurrent writes from multiple consumer instances
    never overwrite each other — each increment is applied independently.

    Blocked requests (status == "blocked") increment requests_blocked instead
    of total_spend_usd, since no tokens were consumed.
    """
    month = event.timestamp[:7]  # "YYYY-MM"
    pk = f"TEAM#{event.team_id}"
    sk = f"SPEND#{month}"

    cost = Decimal(str(event.actual_cost_usd))
    is_blocked = event.status == "blocked"

    # Build the atomic expression dynamically based on event status
    update_expr = "ADD total_requests :one, total_tokens :tokens" + (
        ", total_spend_usd :cost" if not is_blocked else ", requests_blocked :one"
    )
    expr_values = {
        ":one": 1,
        ":tokens": event.total_tokens,
    }
    if not is_blocked:
        expr_values[":cost"] = cost

    # Also maintain a last_updated timestamp using SET alongside the ADD
    update_expr += " SET last_updated = :ts, team_id = :tid, #month = :month"
    expr_values[":ts"] = datetime.now(timezone.utc).isoformat()
    expr_values[":tid"] = event.team_id
    expr_values[":month"] = month

    table.update_item(
        Key={"PK": pk, "SK": sk},
        UpdateExpression=update_expr,
        ExpressionAttributeValues=expr_values,
        # 'month' is a DynamoDB reserved word, so alias it
        ExpressionAttributeNames={"#month": "month"},
    )
    logger.debug(
        "Spend aggregate updated: %s / %s  +$%.4f  +%d tokens",
        pk,
        sk,
        float(cost),
        event.total_tokens,
    )
