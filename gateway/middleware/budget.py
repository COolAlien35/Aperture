from fastapi import Request, HTTPException
import logging
import time
from datetime import datetime, timezone
from gateway.budget.cost_estimation import estimate_cost

logger = logging.getLogger(__name__)

# Hardcoded budget limit for now, Team C will put this in DynamoDB eventually
TEAM_BUDGET_LIMIT = 50.0


async def budget_check_middleware(request: Request) -> Request:
    """
    Check budget and reserve estimated cost in Redis.
    """
    try:
        body = await request.json()
    except Exception:
        body = {}

    model = body.get("model", "unknown")
    max_tokens = body.get("max_tokens")

    # We estimate 50 tokens for the prompt since we don't have a tokenizer here yet.
    estimated_cost = estimate_cost(
        model, prompt_tokens=50, requested_max_tokens=max_tokens
    )

    team_id = getattr(request.state, "team_id", "default_team")
    redis_client = getattr(request.app.state, "redis", None)
    script_sha = getattr(request.app.state, "budget_script_sha", None)

    team_budget_limit = TEAM_BUDGET_LIMIT
    if redis_client:
        try:
            dynamic_limit = await redis_client.get(f"budget:limit:{team_id}")
            if dynamic_limit:
                team_budget_limit = float(dynamic_limit)
        except Exception as e:
            logger.warning(f"Failed to fetch dynamic limit for team {team_id}: {e}")

    if redis_client and script_sha:
        current_month = datetime.now(timezone.utc).strftime("%Y-%m")
        usage_key = f"usage:{team_id}:{current_month}"
        try:
            # KEYS[1], ARGV[1], ARGV[2], ARGV[3]
            # action = 'RESERVE', estimated_cost, budget_limit
            result = await redis_client.evalsha(
                script_sha,
                1,
                usage_key,
                "RESERVE",
                str(estimated_cost),
                str(team_budget_limit),
            )

            if result == 0:
                raise HTTPException(status_code=402, detail="Team budget exceeded")

            # If successful, reset the failure timer
            if getattr(request.app.state, "redis_down_since", None) is not None:
                request.app.state.redis_down_since = None

        except HTTPException:
            raise
        except Exception as e:
            # Redis failed. Check the grace window.
            now = time.time()
            down_since = getattr(request.app.state, "redis_down_since", None)

            if down_since is None:
                # First failure
                request.app.state.redis_down_since = now
                logger.warning(
                    f"Redis budget check failed, starting 10s grace period: {e}"
                )
            elif (now - down_since) > 10:
                logger.error("Redis has been down for > 10 seconds. Failing closed.")
                raise HTTPException(
                    status_code=503, detail="Service temporarily unavailable"
                )
            else:
                logger.warning(f"Redis down, failing open (grace period active): {e}")
    else:
        logger.warning("Redis client or Lua script not loaded, skipping budget check")

    request.state.reserved = True
    request.state.estimated_cost = estimated_cost

    return request
