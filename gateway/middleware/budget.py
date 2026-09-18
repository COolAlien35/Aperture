from fastapi import Request, HTTPException
import logging
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

    if redis_client and script_sha:
        usage_key = f"usage:{team_id}"
        try:
            # KEYS[1], ARGV[1], ARGV[2], ARGV[3]
            # action = 'RESERVE', estimated_cost, budget_limit
            result = await redis_client.evalsha(
                script_sha,
                1,
                usage_key,
                "RESERVE",
                str(estimated_cost),
                str(TEAM_BUDGET_LIMIT),
            )

            if result == 0:
                raise HTTPException(status_code=402, detail="Team budget exceeded")

        except HTTPException:
            raise
        except Exception as e:
            logger.warning(f"Redis budget check failed, failing open: {e}")
            # Fail open if Redis is down
    else:
        logger.warning("Redis client or Lua script not loaded, skipping budget check")

    request.state.reserved = True
    request.state.estimated_cost = estimated_cost

    return request
