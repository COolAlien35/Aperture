import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock
from gateway.main import app


@pytest.fixture
def test_client():
    return TestClient(app)


@pytest.fixture
def mock_dynamodb():
    dynamo = MagicMock()
    app.state.dynamo = dynamo
    return dynamo


@pytest.fixture
def mock_redis():
    redis = AsyncMock()
    app.state.redis = redis
    return redis


@pytest.fixture
def mock_auth(monkeypatch):
    # Mock auth_middleware to return a request with desired state
    async def mock_auth_middleware(request):
        # Read header to determine role
        auth_header = request.headers.get("Authorization", "")
        if "admin" in auth_header:
            request.state.role = "Admin"
            request.state.key_id = "sk-admin"
        else:
            request.state.role = "Developer"
            request.state.key_id = "sk-dev"
        request.state.team_id = "team1"
        return request

    monkeypatch.setattr("gateway.routes.governance.require_auth", mock_auth_middleware)


def test_submit_budget_request(test_client, mock_dynamodb, mock_redis, mock_auth):
    # Developer submits request
    mock_redis.get.return_value = "50.0"

    response = test_client.post(
        "/v1/governance/budget-requests",
        headers={"Authorization": "Bearer sk-dev"},
        json={"requested_limit": 100.0, "reason": "Testing limits"},
    )

    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "pending"
    assert data["requested_limit"] == 100.0
    assert data["requester_id"] == "sk-dev"
    mock_dynamodb.put_item.assert_called_once()


def test_submit_budget_request_invalid_limit(test_client, mock_redis, mock_auth):
    mock_redis.get.return_value = "100.0"

    response = test_client.post(
        "/v1/governance/budget-requests",
        headers={"Authorization": "Bearer sk-dev"},
        json={"requested_limit": 50.0, "reason": "Testing limits"},
    )

    assert response.status_code == 400
    assert "greater than current limit" in response.json()["detail"]


def test_approve_request_unauthorized(test_client, mock_auth):
    # Developer tries to approve
    response = test_client.post(
        "/v1/governance/budget-requests/team1/REQUEST%23123/approve",
        headers={"Authorization": "Bearer sk-dev"},
        json={"decision_reason": "Looks good to me"},
    )

    assert response.status_code == 403


def test_approve_request_success(test_client, mock_dynamodb, mock_redis, mock_auth):
    # Admin approves
    mock_dynamodb.get_item.return_value = {"Item": {"requested_limit": {"N": "100.0"}}}

    mock_dynamodb.update_item.return_value = {
        "Attributes": {
            "request_id": {"S": "req1"},
            "team_id": {"S": "team1"},
            "status": {"S": "approved"},
            "requested_limit": {"N": "100.0"},
        }
    }

    response = test_client.post(
        "/v1/governance/budget-requests/team1/REQUEST%23123/approve",
        headers={"Authorization": "Bearer sk-admin"},
        json={"decision_reason": "Approved for phase 2"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "approved"

    mock_dynamodb.update_item.assert_called_once()
    mock_redis.set.assert_called_once_with("budget:limit:team1", "100.0")


def test_list_requests(test_client, mock_dynamodb, mock_auth):
    mock_dynamodb.query.return_value = {
        "Items": [
            {
                "request_id": {"S": "req1"},
                "team_id": {"S": "team1"},
                "status": {"S": "pending"},
            }
        ]
    }

    response = test_client.get(
        "/v1/governance/budget-requests?status=pending&team_id=team1",
        headers={"Authorization": "Bearer sk-admin"},
    )

    assert response.status_code == 200
    assert len(response.json()) == 1
    mock_dynamodb.query.assert_called_once()
