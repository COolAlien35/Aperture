import uuid
from datetime import datetime, timezone
import logging
from typing import Optional, List

from gateway.models.governance import BudgetRequestItem

logger = logging.getLogger(__name__)


async def create_budget_request(
    dynamo_client,
    table_name: str,
    team_id: str,
    requester_id: str,
    current_limit: float,
    requested_limit: float,
    reason: str,
) -> BudgetRequestItem:
    request_id = str(uuid.uuid4())
    timestamp = datetime.now(timezone.utc).isoformat()

    item = BudgetRequestItem(
        request_id=request_id,
        team_id=team_id,
        requester_id=requester_id,
        current_limit=current_limit,
        requested_limit=requested_limit,
        reason=reason,
        status="pending",
        created_at=timestamp,
    )

    # DynamoDB Single Table Design
    # PK: TEAM#<team_id>
    # SK: REQUEST#<timestamp>
    dynamo_item = {
        "PK": {"S": f"TEAM#{team_id}"},
        "SK": {"S": f"REQUEST#{timestamp}"},
        "request_id": {"S": request_id},
        "team_id": {"S": team_id},
        "requester_id": {"S": requester_id},
        "current_limit": {"N": str(current_limit)},
        "requested_limit": {"N": str(requested_limit)},
        "reason": {"S": reason},
        "status": {"S": "pending"},
        "created_at": {"S": timestamp},
        "GSI1PK": {"S": "BUDGET_REQUESTS"},
        "GSI1SK": {"S": f"STATUS#pending#{timestamp}"},
    }

    dynamo_client.put_item(TableName=table_name, Item=dynamo_item)

    return item


async def list_budget_requests(
    dynamo_client,
    table_name: str,
    status: Optional[str] = None,
    team_id: Optional[str] = None,
) -> List[BudgetRequestItem]:
    items = []

    if team_id:
        # Query by PK=TEAM#<team_id> and SK begins_with REQUEST#
        # Optional: filter by status
        response = dynamo_client.query(
            TableName=table_name,
            KeyConditionExpression="PK = :pk AND begins_with(SK, :sk)",
            ExpressionAttributeValues={
                ":pk": {"S": f"TEAM#{team_id}"},
                ":sk": {"S": "REQUEST#"},
            },
        )
        for i in response.get("Items", []):
            if status and i.get("status", {}).get("S") != status:
                continue
            items.append(_parse_budget_item(i))
    else:
        # Query via GSI1 for pending requests globally
        if status:
            response = dynamo_client.query(
                TableName=table_name,
                IndexName="team_id-index",  # Assuming GSI1 is named team_id-index
                KeyConditionExpression="GSI1PK = :pk AND begins_with(GSI1SK, :sk)",
                ExpressionAttributeValues={
                    ":pk": {"S": "BUDGET_REQUESTS"},
                    ":sk": {"S": f"STATUS#{status}#"},
                },
            )
            for i in response.get("Items", []):
                items.append(_parse_budget_item(i))

    return items


async def approve_budget_request(
    dynamo_client,
    redis_client,
    table_name: str,
    team_id: str,
    timestamp_sk: str,
    approver_id: str,
    decision_reason: Optional[str] = None,
) -> BudgetRequestItem:
    now = datetime.now(timezone.utc).isoformat()

    # Get current item
    response = dynamo_client.get_item(
        TableName=table_name,
        Key={"PK": {"S": f"TEAM#{team_id}"}, "SK": {"S": timestamp_sk}},
    )

    item = response.get("Item")
    if not item:
        raise ValueError("Budget request not found")

    requested_limit = item.get("requested_limit", {}).get("N")
    if not requested_limit:
        raise ValueError("Invalid requested limit")

    # Update DynamoDB
    update_expr = "SET #st = :status, approver_id = :approver, decided_at = :decided, GSI1SK = :gsisk"
    expr_attr_values = {
        ":status": {"S": "approved"},
        ":approver": {"S": approver_id},
        ":decided": {"S": now},
        ":gsisk": {"S": f"STATUS#approved#{timestamp_sk.replace('REQUEST#', '')}"},
    }
    expr_attr_names = {"#st": "status"}

    if decision_reason:
        update_expr += ", decision_reason = :dr"
        expr_attr_values[":dr"] = {"S": decision_reason}

    updated = dynamo_client.update_item(
        TableName=table_name,
        Key={"PK": {"S": f"TEAM#{team_id}"}, "SK": {"S": timestamp_sk}},
        UpdateExpression=update_expr,
        ExpressionAttributeValues=expr_attr_values,
        ExpressionAttributeNames=expr_attr_names,
        ReturnValues="ALL_NEW",
    )

    parsed = _parse_budget_item(updated.get("Attributes", {}))

    # Phase 2.1 Core Magic: dynamically update live limit in Redis!
    try:
        await redis_client.set(f"budget:limit:{team_id}", requested_limit)
        logger.info(
            f"Updated live budget limit in Redis for {team_id} to {requested_limit}"
        )
    except Exception as e:
        logger.error(f"Failed to update Redis budget limit: {e}")

    return parsed


async def deny_budget_request(
    dynamo_client,
    table_name: str,
    team_id: str,
    timestamp_sk: str,
    approver_id: str,
    decision_reason: Optional[str] = None,
) -> BudgetRequestItem:
    now = datetime.now(timezone.utc).isoformat()

    # Update DynamoDB
    update_expr = "SET #st = :status, approver_id = :approver, decided_at = :decided, GSI1SK = :gsisk"
    expr_attr_values = {
        ":status": {"S": "denied"},
        ":approver": {"S": approver_id},
        ":decided": {"S": now},
        ":gsisk": {"S": f"STATUS#denied#{timestamp_sk.replace('REQUEST#', '')}"},
    }
    expr_attr_names = {"#st": "status"}

    if decision_reason:
        update_expr += ", decision_reason = :dr"
        expr_attr_values[":dr"] = {"S": decision_reason}

    updated = dynamo_client.update_item(
        TableName=table_name,
        Key={"PK": {"S": f"TEAM#{team_id}"}, "SK": {"S": timestamp_sk}},
        UpdateExpression=update_expr,
        ExpressionAttributeValues=expr_attr_values,
        ExpressionAttributeNames=expr_attr_names,
        ReturnValues="ALL_NEW",
    )

    return _parse_budget_item(updated.get("Attributes", {}))


def _parse_budget_item(item: dict) -> BudgetRequestItem:
    return BudgetRequestItem(
        request_id=item.get("request_id", {}).get("S", ""),
        team_id=item.get("team_id", {}).get("S", ""),
        requester_id=item.get("requester_id", {}).get("S", ""),
        current_limit=float(item.get("current_limit", {}).get("N", "0")),
        requested_limit=float(item.get("requested_limit", {}).get("N", "0")),
        reason=item.get("reason", {}).get("S", ""),
        status=item.get("status", {}).get("S", "pending"),
        created_at=item.get("created_at", {}).get("S", ""),
        approver_id=item.get("approver_id", {}).get("S"),
        decision_reason=item.get("decision_reason", {}).get("S"),
        decided_at=item.get("decided_at", {}).get("S"),
    )
