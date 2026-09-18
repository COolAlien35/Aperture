import unittest
from unittest.mock import AsyncMock, MagicMock
import json

# Import the modules we just created
from gateway.auth.key_management import generate_virtual_key, get_key_metadata, KEY_PREFIX
from gateway.auth.rbac import can_access_model, Role
from gateway.budget.cost_estimation import estimate_cost, calculate_actual_cost

class TestTeamBModules(unittest.IsolatedAsyncioTestCase):

    async def test_virtual_key_generation(self):
        """Test that keys are generated with the correct prefix and length."""
        key = generate_virtual_key()
        self.assertTrue(key.startswith(KEY_PREFIX))
        # Prefix length is len("sk-gw-") = 6. 32 bytes hex = 64 chars. Total 70 chars.
        self.assertEqual(len(key), 70)

    async def test_rbac_access_control(self):
        """Test that different roles have appropriate model access."""
        # Admin can access anything
        self.assertTrue(can_access_model("Admin", "gpt-4-turbo"))
        self.assertTrue(can_access_model("Admin", "some-unknown-model"))
        
        # Team Lead can access expensive models
        self.assertTrue(can_access_model("Team Lead", "gpt-4-turbo"))
        self.assertTrue(can_access_model("Team Lead", "claude-3-opus-20240229"))
        
        # Developer is restricted
        self.assertFalse(can_access_model("Developer", "gpt-4-turbo"))
        self.assertFalse(can_access_model("Developer", "claude-3-opus-20240229"))
        self.assertTrue(can_access_model("Developer", "gpt-3.5-turbo"))
        
        # Unknown role defaults to restricted
        self.assertFalse(can_access_model("Hacker", "gpt-3.5-turbo"))

    async def test_cost_estimation(self):
        """Test cost estimation logic and fallback behavior."""
        # GPT-4-turbo is 0.01/1k input, 0.03/1k output
        # Test with explicit max_tokens
        cost = estimate_cost("gpt-4-turbo", prompt_tokens=1000, requested_max_tokens=2000)
        self.assertEqual(cost, 0.01 + 0.06)
        
        # Test with fallback max_tokens (4096)
        cost_fallback = estimate_cost("gpt-4-turbo", prompt_tokens=1000, requested_max_tokens=None)
        expected_fallback = 0.01 + ((4096 / 1000.0) * 0.03)
        self.assertAlmostEqual(cost_fallback, expected_fallback, places=4)

    async def test_actual_cost_calculation(self):
        """Test calculation of actual usage cost."""
        actual_cost = calculate_actual_cost("gpt-3.5-turbo", prompt_tokens=500, completion_tokens=1000)
        # 0.0005/1k input, 0.0015/1k output
        expected = (0.5 * 0.0005) + (1.0 * 0.0015)
        self.assertAlmostEqual(actual_cost, expected, places=5)

    async def test_key_metadata_cache_hit(self):
        """Test get_key_metadata when Redis cache has the data."""
        mock_redis = AsyncMock()
        mock_redis.get.return_value = json.dumps({
            "team_id": "team_1",
            "role": "Admin",
            "status": "active"
        })
        mock_dynamo = MagicMock()
        
        key = generate_virtual_key()
        metadata = await get_key_metadata(mock_redis, mock_dynamo, "KeysTable", key)
        
        self.assertIsNotNone(metadata)
        self.assertEqual(metadata["team_id"], "team_1")
        mock_dynamo.get_item.assert_not_called()

    async def test_key_metadata_dynamo_fallback(self):
        """Test get_key_metadata when Redis misses and fetches from DynamoDB."""
        mock_redis = AsyncMock()
        mock_redis.get.return_value = None
        
        mock_dynamo = MagicMock()
        mock_dynamo.get_item.return_value = {
            "Item": {
                "team_id": {"S": "team_2"},
                "role": {"S": "Developer"},
                "status": {"S": "active"}
            }
        }
        
        key = generate_virtual_key()
        metadata = await get_key_metadata(mock_redis, mock_dynamo, "KeysTable", key)
        
        self.assertIsNotNone(metadata)
        self.assertEqual(metadata["team_id"], "team_2")
        mock_redis.setex.assert_called_once()

    async def test_key_metadata_inactive_key(self):
        """Test that inactive keys are rejected."""
        mock_redis = AsyncMock()
        mock_redis.get.return_value = None
        
        mock_dynamo = MagicMock()
        mock_dynamo.get_item.return_value = {
            "Item": {
                "team_id": {"S": "team_2"},
                "role": {"S": "Developer"},
                "status": {"S": "revoked"}
            }
        }
        
        key = generate_virtual_key()
        metadata = await get_key_metadata(mock_redis, mock_dynamo, "KeysTable", key)
        self.assertIsNone(metadata)

if __name__ == '__main__':
    unittest.main()
