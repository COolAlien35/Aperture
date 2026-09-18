from fastapi import APIRouter, Request, HTTPException, Depends
from typing import List, Optional
import logging

from gateway.models.governance import (
    BudgetRequestCreate,
    BudgetApprovalDecision,
    BudgetRequestItem,
)
from gateway.budget.governance import (
    create_budget_request,
    list_budget_requests,
    approve_budget_request,
    deny_budget_request,
)
from gateway.middleware.auth import auth_middleware

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1/governance", tags=["Governance"])


# Dependency to ensure auth
async def require_auth(request: Request) -> Request:
    return await auth_middleware(request)


def require_admin_or_lead(request: Request):
    role = getattr(request.state, "role", "").lower()
    if role not in ["admin", "team lead"]:
        raise HTTPException(
            status_code=403,
            detail="Forbidden: Only Admin or Team Lead can perform this action",
        )


@router.post("/budget-requests", response_model=BudgetRequestItem, status_code=201)
async def submit_budget_request(body: BudgetRequestCreate, request: Request):
    """Developer submits a request to raise their team's budget limit."""
    request = await require_auth(request)
    team_id = request.state.team_id
    requester_id = request.state.key_id

    if not body.reason or not body.reason.strip():
        raise HTTPException(
            status_code=400, detail="A reason is required for a budget request"
        )

    dynamo_client = getattr(request.app.state, "dynamo", None)
    if not dynamo_client:
        raise HTTPException(status_code=500, detail="DynamoDB client not initialized")

    redis_client = getattr(request.app.state, "redis", None)

    # Get current limit
    current_limit = 50.0  # Default
    if redis_client:
        try:
            dynamic = await redis_client.get(f"budget:limit:{team_id}")
            if dynamic:
                current_limit = float(dynamic)
        except Exception:
            pass

    if body.requested_limit <= current_limit:
        raise HTTPException(
            status_code=400,
            detail=f"Requested limit must be greater than current limit ({current_limit})",
        )

    try:
        item = await create_budget_request(
            dynamo_client,
            "aperture_data",
            team_id,
            requester_id,
            current_limit,
            body.requested_limit,
            body.reason,
        )
        return item
    except Exception as e:
        logger.error(f"Failed to create budget request: {e}")
        raise HTTPException(status_code=500, detail="Failed to create budget request")


@router.get("/budget-requests", response_model=List[BudgetRequestItem])
async def get_budget_requests(
    request: Request, status: Optional[str] = None, team_id: Optional[str] = None
):
    """List pending budget requests."""
    request = await require_auth(request)
    require_admin_or_lead(request)

    dynamo_client = getattr(request.app.state, "dynamo", None)
    try:
        items = await list_budget_requests(
            dynamo_client, "aperture_data", status, team_id
        )
        return items
    except Exception as e:
        logger.error(f"Failed to list budget requests: {e}")
        raise HTTPException(status_code=500, detail="Failed to list budget requests")


@router.post(
    "/budget-requests/{team_id}/{timestamp_sk}/approve",
    response_model=BudgetRequestItem,
)
async def approve_request(
    team_id: str, timestamp_sk: str, body: BudgetApprovalDecision, request: Request
):
    """Admin approves a budget request, automatically increasing the live Redis limit."""
    request = await require_auth(request)
    require_admin_or_lead(request)

    dynamo_client = getattr(request.app.state, "dynamo", None)
    redis_client = getattr(request.app.state, "redis", None)
    approver_id = request.state.key_id

    try:
        item = await approve_budget_request(
            dynamo_client,
            redis_client,
            "aperture_data",
            team_id,
            timestamp_sk,
            approver_id,
            body.decision_reason,
        )
        return item
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to approve budget request: {e}")
        raise HTTPException(status_code=500, detail="Failed to approve budget request")


@router.post(
    "/budget-requests/{team_id}/{timestamp_sk}/deny", response_model=BudgetRequestItem
)
async def deny_request(
    team_id: str, timestamp_sk: str, body: BudgetApprovalDecision, request: Request
):
    """Admin denies a budget request."""
    request = await require_auth(request)
    require_admin_or_lead(request)

    dynamo_client = getattr(request.app.state, "dynamo", None)
    approver_id = request.state.key_id

    try:
        item = await deny_budget_request(
            dynamo_client,
            "aperture_data",
            team_id,
            timestamp_sk,
            approver_id,
            body.decision_reason,
        )
        return item
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to deny budget request: {e}")
        raise HTTPException(status_code=500, detail="Failed to deny budget request")


from gateway.models.forecasting import ForecastResponse
from gateway.budget.forecasting import calculate_forecast


@router.get("/forecast/{team_id}", response_model=ForecastResponse)
async def get_forecast(team_id: str, request: Request):
    """Predictive overage forecasting for a team's budget."""
    request = await require_auth(request)

    redis_client = getattr(request.app.state, "redis", None)

    current_limit = 50.0
    current_spend = 0.0

    if redis_client:
        try:
            dynamic = await redis_client.get(f"budget:limit:{team_id}")
            if dynamic:
                current_limit = float(dynamic)

            # Fetch current month spend
            from datetime import datetime, timezone

            current_month = datetime.now(timezone.utc).strftime("%Y-%m")
            usage_key = f"usage:{team_id}:{current_month}"
            spend = await redis_client.get(usage_key)
            if spend:
                current_spend = float(spend)
        except Exception as e:
            logger.warning(f"Failed to fetch redis data for forecast: {e}")

    # For Phase 2 implementation, if we don't have a real 7d spend,
    # we simulate a realistic burn rate based on current spend for demo purposes.
    # In production, Person C's DynamoDB aggregates would be queried here.
    trailing_7d_spend = current_spend * 0.4 if current_spend > 0 else 10.5

    return await calculate_forecast(
        team_id=team_id,
        current_spend=current_spend,
        trailing_7d_spend=trailing_7d_spend,
        budget_limit=current_limit,
    )


from gateway.models.summary import SpendSummaryResponse
from gateway.budget.summary import generate_spend_summary


@router.get("/summary/{team_id}", response_model=SpendSummaryResponse)
async def get_spend_summary(team_id: str, request: Request):
    """Generates a plain-language spend summary for the dashboard."""
    request = await require_auth(request)

    redis_client = getattr(request.app.state, "redis", None)

    current_spend = 0.0
    previous_spend = 0.0

    # In a full implementation, we'd query DynamoDB aggregates here for previous month
    # For Phase 2, we fetch current from Redis and mock a realistic previous spend for demo
    if redis_client:
        try:
            from datetime import datetime, timezone

            now = datetime.now(timezone.utc)
            current_month = now.strftime("%Y-%m")

            spend = await redis_client.get(f"usage:{team_id}:{current_month}")
            if spend:
                current_spend = float(spend)
        except Exception:
            pass

    # Mock data for demonstration purposes as specified in Phase 2
    previous_spend = current_spend * 0.85 if current_spend > 0 else 1076.00
    if current_spend == 0:
        current_spend = 1240.00

    return generate_spend_summary(
        team_id=team_id,
        period="2026-09",
        total_spend=current_spend,
        previous_period_spend=previous_spend,
        top_model_by_spend="claude-3-sonnet-20240229",
        top_model_spend_pct=60.0,
        top_spender_by_key_or_user="sk-gw-alice",
        top_spender_spend_pct=42.5,
    )
