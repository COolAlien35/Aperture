import logging
import json
from typing import AsyncGenerator, Any
from gateway.budget.cost_estimation import calculate_actual_cost

logger = logging.getLogger(__name__)

async def _run_redis_reconciliation(
    redis_client: Any,
    script_sha: str,
    team_id: str,
    estimated_cost: float,
    actual_cost: float
) -> None:
    """
    Executes the Redis Lua script to reconcile the budget difference.
    """
    if not redis_client or not script_sha:
        logger.warning("No Redis client or Lua SHA found, skipping reconciliation.")
        return

    # Calculate difference (actual - estimated)
    # If actual > estimated, this is positive (deduct more from budget).
    # If actual < estimated, this is negative (refund to budget).
    cost_difference = actual_cost - estimated_cost
    usage_key = f"usage:{team_id}"

    try:
        await redis_client.evalsha(
            script_sha,
            1,
            usage_key,
            'RECONCILE',
            str(cost_difference)
        )
        logger.info(f"Reconciled team {team_id}: estimated={estimated_cost:.6f}, actual={actual_cost:.6f}, diff={cost_difference:.6f}")
    except Exception as e:
        logger.error(f"Failed to reconcile budget for team {team_id}: {e}")

def _estimate_tokens_from_text(text: str) -> int:
    """
    Extremely crude token estimator (approx 4 chars per token).
    In a real system, use tiktoken or provider-specific tokenizers.
    """
    return max(1, len(text) // 4)

async def token_tracking_stream(
    underlying_stream: AsyncGenerator[str, None],
    request_state: Any,
    app_state: Any,
    model: str,
    prompt_tokens: int,
    estimated_cost: float
) -> AsyncGenerator[str, None]:
    """
    Wraps an LLM provider's SSE stream.
    Passes chunks through transparently, counts tokens, and guarantees
    budget reconciliation fires when the stream ends or is aborted.
    """
    completion_tokens = 0
    team_id = getattr(request_state, "team_id", "default_team")

    try:
        async for chunk in underlying_stream:
            # We assume OpenAI SSE format: `data: {"choices": [{"delta": {"content": "..."}}]}`
            # For simplicity in this tracking, we'll try to extract the content length.
            # If parsing fails, we'll just fall back to raw length / 4.
            text_content = ""
            if chunk.startswith("data: ") and chunk.strip() != "data: [DONE]":
                try:
                    data = json.loads(chunk[6:])
                    if "choices" in data and len(data["choices"]) > 0:
                        delta = data["choices"][0].get("delta", {})
                        text_content = delta.get("content", "")
                except Exception:
                    # Fallback if not standard JSON
                    text_content = chunk
            
            completion_tokens += _estimate_tokens_from_text(text_content) if text_content else 0
            
            yield chunk
            
    finally:
        # This block executes no matter what: normal finish, client abort, or upstream error.
        actual_cost = calculate_actual_cost(model, prompt_tokens, completion_tokens)
        
        redis_client = getattr(app_state, "redis", None)
        script_sha = getattr(app_state, "budget_script_sha", None)
        
        # Fire and forget the reconciliation task to avoid blocking the final chunk
        await _run_redis_reconciliation(
            redis_client=redis_client,
            script_sha=script_sha,
            team_id=team_id,
            estimated_cost=estimated_cost,
            actual_cost=actual_cost
        )
