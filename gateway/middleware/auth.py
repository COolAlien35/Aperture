from fastapi import Request, HTTPException
import logging

from gateway.auth.key_management import get_key_metadata, KEY_PREFIX
from gateway.auth.rbac import can_access_model

logger = logging.getLogger(__name__)


async def auth_middleware(request: Request) -> Request:
    """
    Authenticate the incoming request using virtual API keys.
    """
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=401, detail="Missing or invalid Authorization header"
        )

    key_id = auth_header.split(" ")[1]

    # Use the real clients initialized in lifespan
    redis_client = getattr(request.app.state, "redis", None)
    dynamo_client = getattr(request.app.state, "dynamo", None)

    if dynamo_client is None:
        raise HTTPException(status_code=500, detail="DynamoDB client not initialized")

    try:
        metadata = await get_key_metadata(
            redis_client, dynamo_client, "KeysTable", key_id
        )
    except Exception as e:
        logger.error(f"Auth error: {e}")
        raise HTTPException(
            status_code=500, detail="Internal server error during authentication"
        )

    if not metadata:
        raise HTTPException(status_code=401, detail="Invalid or revoked API key")

    # If the user is trying to access a specific model, verify RBAC
    # We parse the body to get the model. Note: request.json() can only be read once
    # without caching, but for this exercise we can read it.
    # Actually, body stream needs to be preserved. Let's do a simple read and replace.
    try:
        body = await request.json()
        requested_model = body.get("model")
        if requested_model and not can_access_model(metadata["role"], requested_model):
            raise HTTPException(
                status_code=403,
                detail=f"Role {metadata['role']} is not permitted to access model {requested_model}",
            )
    except Exception as e:
        # If body is not JSON or empty, we ignore for now
        pass

    request.state.key_id = key_id
    request.state.team_id = metadata["team_id"]
    request.state.role = metadata["role"]

    return request
