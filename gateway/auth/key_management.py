import secrets
import json
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

KEY_PREFIX = "sk-gw-"
CACHE_TTL_SECONDS = 60


def generate_virtual_key() -> str:
    """
    Generates a secure virtual key for API access.
    Format: sk-gw-<32-byte-hex>
    """
    random_part = secrets.token_hex(32)
    return f"{KEY_PREFIX}{random_part}"


async def get_key_metadata(
    redis_client, dynamodb_client, table_name: str, key_id: str
) -> Optional[Dict[str, Any]]:
    """
    Validates a virtual key and retrieves its metadata (team_id, roles, budget context).
    Uses a Redis cache layer (60s TTL) to minimize DynamoDB reads on the hot path.
    """
    if not key_id.startswith(KEY_PREFIX):
        return None

    cache_key = f"key_meta:{key_id}"

    # 1. Check Redis Cache
    try:
        cached_meta = await redis_client.get(cache_key)
        if cached_meta:
            return json.loads(cached_meta)
    except Exception as e:
        logger.warning(f"Redis cache read failed for key validation: {e}")
        # Fail-open for cache layer, proceed to DB check

    # 2. Check DynamoDB (Cold Path)
    try:
        # Expected Schema: PK=KEY#<id>, SK=METADATA
        response = dynamodb_client.get_item(
            TableName=table_name,
            Key={"PK": {"S": f"KEY#{key_id}"}, "SK": {"S": "METADATA"}},
        )

        item = response.get("Item")
        if not item:
            return None

        # Parse DynamoDB Item into a standard dict
        metadata = {
            "team_id": item.get("team_id", {}).get("S"),
            "role": item.get("role", {}).get("S", "Developer"),
            "status": item.get("status", {}).get("S", "active"),
        }

        if metadata["status"] != "active":
            return None

        # 3. Populate Redis Cache
        try:
            await redis_client.setex(cache_key, CACHE_TTL_SECONDS, json.dumps(metadata))
        except Exception as e:
            logger.warning(f"Failed to populate Redis cache for key metadata: {e}")

        return metadata

    except Exception as e:
        logger.error(f"DynamoDB read failed during key validation: {e}")
        # If DB fails, we must fail closed on auth to prevent unauthorized access
        raise
