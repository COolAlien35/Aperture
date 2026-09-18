import pytest
from unittest.mock import MagicMock, AsyncMock
from gateway.budget.governance import (
    create_budget_request,
    list_budget_requests,
    approve_budget_request,
    deny_budget_request,
)


@pytest.fixture
def dynamo_client_mock():
    return MagicMock()


@pytest.fixture
def redis_client_mock():
    return AsyncMock()


@pytest.mark.asyncio
async def test_create_budget_request(dynamo_client_mock):
    item = await create_budget_request(
        dynamo_client_mock,
        "test_table",
        "team1",
        "user1",
        50.0,
        100.0,
        "Need more budget for testing",
    )

    assert item.team_id == "team1"
    assert item.requester_id == "user1"
    assert item.current_limit == 50.0
    assert item.requested_limit == 100.0
    assert item.status == "pending"

    dynamo_client_mock.put_item.assert_called_once()
    called_args = dynamo_client_mock.put_item.call_args[1]
    assert called_args["TableName"] == "test_table"
    assert called_args["Item"]["PK"]["S"] == "TEAM#team1"
    assert called_args["Item"]["GSI1PK"]["S"] == "BUDGET_REQUESTS"


@pytest.mark.asyncio
async def test_list_budget_requests(dynamo_client_mock):
    # Setup mock response
    dynamo_client_mock.query.return_value = {
        "Items": [
            {
                "request_id": {"S": "req1"},
                "team_id": {"S": "team1"},
                "status": {"S": "pending"},
            }
        ]
    }

    items = await list_budget_requests(
        dynamo_client_mock, "test_table", status="pending", team_id="team1"
    )

    assert len(items) == 1
    assert items[0].request_id == "req1"

    dynamo_client_mock.query.assert_called_once()


@pytest.mark.asyncio
async def test_approve_budget_request(dynamo_client_mock, redis_client_mock):
    dynamo_client_mock.get_item.return_value = {
        "Item": {"requested_limit": {"N": "150.0"}}
    }

    dynamo_client_mock.update_item.return_value = {
        "Attributes": {
            "request_id": {"S": "req2"},
            "team_id": {"S": "team1"},
            "status": {"S": "approved"},
            "requested_limit": {"N": "150.0"},
        }
    }

    item = await approve_budget_request(
        dynamo_client_mock,
        redis_client_mock,
        "test_table",
        "team1",
        "REQUEST#ts1",
        "admin1",
        "Approved for Q3",
    )

    assert item.status == "approved"

    dynamo_client_mock.update_item.assert_called_once()
    redis_client_mock.set.assert_called_once_with("budget:limit:team1", "150.0")


@pytest.mark.asyncio
async def test_deny_budget_request(dynamo_client_mock):
    dynamo_client_mock.update_item.return_value = {
        "Attributes": {"request_id": {"S": "req3"}, "status": {"S": "denied"}}
    }

    item = await deny_budget_request(
        dynamo_client_mock,
        "test_table",
        "team1",
        "REQUEST#ts2",
        "admin1",
        "Not enough justification",
    )

    assert item.status == "denied"
