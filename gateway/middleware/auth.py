"""
Authentication middleware — STUB for Person B.

Person B: Replace this stub with real virtual-key authentication logic.
This middleware resolves who is calling and attaches identity to request.state.

Runs AFTER request_id generation, BEFORE budget_check_middleware.
"""
from fastapi import Request


async def auth_middleware(request: Request) -> Request:
    """
    Authenticate the incoming request using virtual API keys.

    Person B will implement:
    - Look up the virtual key from the Authorization header
    - Validate against DynamoDB (cached in Redis, TTL=60s per decision #4)
    - Resolve team, role, budget limits
    - Reject if key is revoked or invalid

    Currently: always passes, sets stub identity values.
    """
    request.state.key_id = "stub-key"
    request.state.team_id = "stub-team"
    request.state.role = "developer"
    return request
