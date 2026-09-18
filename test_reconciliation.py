import unittest
from unittest.mock import AsyncMock, MagicMock
import json
from datetime import datetime, timezone

from gateway.budget.reconciliation import (
    token_tracking_stream, 
    _estimate_tokens_from_text,
    _run_redis_reconciliation
)
from gateway.budget.cost_estimation import calculate_actual_cost

class DummyRequestState:
    def __init__(self, team_id="team_1"):
        self.team_id = team_id

class DummyAppState:
    def __init__(self, redis_client, sha):
        self.redis = redis_client
        self.budget_script_sha = sha

async def _simulate_provider_stream(chunks):
    """A mock underlying stream generator"""
    for c in chunks:
        yield c

async def _simulate_broken_provider_stream(chunks, break_after):
    """A mock underlying stream generator that raises an exception mid-way"""
    for i, c in enumerate(chunks):
        if i == break_after:
            raise ConnectionError("Client disconnected early!")
        yield c

class TestReconciliation(unittest.IsolatedAsyncioTestCase):

    def test_token_estimator(self):
        """Test the crude fallback token estimator"""
        # ~4 chars = 1 token. Length 20 = 5 tokens.
        self.assertEqual(_estimate_tokens_from_text("This is a twenty chr"), 5)
        # Minimum should be 1
        self.assertEqual(_estimate_tokens_from_text("a"), 1)

    async def test_successful_stream_reconciliation(self):
        """Test that a healthy stream counts tokens correctly and calls Redis."""
        mock_redis = AsyncMock()
        mock_app_state = DummyAppState(mock_redis, "dummy_sha_123")
        mock_req_state = DummyRequestState(team_id="test_team_99")
        
        # Two SSE chunks with 16 chars each (4 tokens each) = 8 completion tokens total
        chunks = [
            'data: {"choices": [{"delta": {"content": "1234567890123456"}}]}',
            'data: {"choices": [{"delta": {"content": "1234567890123456"}}]}',
            'data: [DONE]'
        ]
        
        stream = token_tracking_stream(
            underlying_stream=_simulate_provider_stream(chunks),
            request_state=mock_req_state,
            app_state=mock_app_state,
            model="gpt-3.5-turbo",
            prompt_tokens=100,
            estimated_cost=0.50 # e.g. reserved 50 cents initially
        )
        
        # Consume the stream
        output = [chunk async for chunk in stream]
        self.assertEqual(len(output), 3)
        
        # The finally block runs when the generator closes
        # actual_cost for 100 prompt, 8 completion on gpt-3.5-turbo:
        # (100/1000 * 0.0005) + (8/1000 * 0.0015) = 0.00005 + 0.000012 = 0.000062
        expected_actual = calculate_actual_cost("gpt-3.5-turbo", 100, 8)
        expected_diff = expected_actual - 0.50
        
        current_month = datetime.now(timezone.utc).strftime('%Y-%m')
        mock_redis.evalsha.assert_called_once_with(
            "dummy_sha_123", 
            1, 
            f"usage:test_team_99:{current_month}", 
            'RECONCILE', 
            str(expected_diff)
        )

    async def test_aborted_stream_reconciliation(self):
        """Test that a disconnected/aborted stream STILL calls Redis with the tokens consumed up to the abort."""
        mock_redis = AsyncMock()
        mock_app_state = DummyAppState(mock_redis, "dummy_sha_123")
        mock_req_state = DummyRequestState()
        
        chunks = [
            'data: {"choices": [{"delta": {"content": "1234567890123456"}}]}', # 4 tokens
            'data: {"choices": [{"delta": {"content": "1234567890123456"}}]}', # won't be reached
        ]
        
        stream = token_tracking_stream(
            underlying_stream=_simulate_broken_provider_stream(chunks, break_after=1),
            request_state=mock_req_state,
            app_state=mock_app_state,
            model="gpt-3.5-turbo",
            prompt_tokens=100,
            estimated_cost=1.00 
        )
        
        output = []
        with self.assertRaises(ConnectionError):
            async for chunk in stream:
                output.append(chunk)
                
        self.assertEqual(len(output), 1) # Only got the first chunk
        
        # actual cost should be based ONLY on the 100 prompt + 4 completion tokens
        expected_actual = calculate_actual_cost("gpt-3.5-turbo", 100, 4)
        expected_diff = expected_actual - 1.00
        
        current_month = datetime.now(timezone.utc).strftime('%Y-%m')
        mock_redis.evalsha.assert_called_once_with(
            "dummy_sha_123", 
            1, 
            f"usage:team_1:{current_month}", 
            'RECONCILE', 
            str(expected_diff)
        )

    async def test_empty_stream_reconciliation(self):
        """Test that if the provider immediately fails and returns no tokens, we refund the ENTIRE estimated cost minus prompt cost."""
        mock_redis = AsyncMock()
        mock_app_state = DummyAppState(mock_redis, "dummy_sha_123")
        mock_req_state = DummyRequestState()
        
        stream = token_tracking_stream(
            underlying_stream=_simulate_provider_stream([]), # Empty stream
            request_state=mock_req_state,
            app_state=mock_app_state,
            model="gpt-4",
            prompt_tokens=50,
            estimated_cost=0.50 
        )
        
        output = [chunk async for chunk in stream]
        self.assertEqual(len(output), 0)
        
        # actual cost should be ONLY the prompt tokens (50 tokens)
        expected_actual = calculate_actual_cost("gpt-4", 50, 0)
        expected_diff = expected_actual - 0.50
        
        current_month = datetime.now(timezone.utc).strftime('%Y-%m')
        mock_redis.evalsha.assert_called_once_with(
            "dummy_sha_123", 
            1, 
            f"usage:team_1:{current_month}", 
            'RECONCILE', 
            str(expected_diff)
        )

if __name__ == '__main__':
    unittest.main()
