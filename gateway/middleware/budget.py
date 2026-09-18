"""
Budget check middleware — STUB for Person B.

Person B: Replace this stub with real Redis-based budget enforcement.
This middleware checks if the team/key has remaining budget before
allowing the request to proceed to the LLM provider.

Runs AFTER auth_middleware, BEFORE translator/router logic.
"""

from fastapi import Request


async def budget_check_middleware(request: Request) -> Request:
    """
    Check budget and reserve estimated cost in Redis.

    Person B will implement:
    - Calculate estimated cost using formula from decision #1:
      estimated_cost = (prompt_tokens × input_price) + (max_tokens × output_price)
    - Atomic Redis check-and-reserve (Lua script)
    - Fail-open for 10s if Redis is down, then fail-closed (decision #2)
    - Reject with 429 if over budget

    Currently: always allows, sets reserved=True.
    """
    request.state.reserved = True
    return request
