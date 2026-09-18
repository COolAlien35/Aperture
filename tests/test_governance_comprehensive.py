import pytest
from datetime import datetime, timezone
import calendar

from gateway.budget.forecasting import calculate_forecast
from gateway.budget.summary import generate_spend_summary
from gateway.budget.governance import (
    create_budget_request, 
    list_budget_requests, 
    approve_budget_request, 
    deny_budget_request
)
from unittest.mock import MagicMock, AsyncMock
from botocore.exceptions import ClientError

# ---------------------------------------------------------
# FORECASTING EDGE CASES (10 tests)
# ---------------------------------------------------------

@pytest.mark.asyncio
async def test_forecast_negative_spend():
    test_date = datetime(2026, 9, 15, tzinfo=timezone.utc)
    forecast = await calculate_forecast("team1", -50.0, 7.0, 100.0, test_date)
    assert forecast.current_spend == -50.0
    assert forecast.status == "ok"
    assert forecast.will_exceed is False

@pytest.mark.asyncio
async def test_forecast_zero_budget():
    test_date = datetime(2026, 9, 15, tzinfo=timezone.utc)
    forecast = await calculate_forecast("team1", 10.0, 7.0, 0.0, test_date)
    assert forecast.will_exceed is True
    assert forecast.status == "exceeded"

@pytest.mark.asyncio
async def test_forecast_negative_budget():
    test_date = datetime(2026, 9, 15, tzinfo=timezone.utc)
    forecast = await calculate_forecast("team1", 10.0, 7.0, -100.0, test_date)
    assert forecast.will_exceed is True
    assert forecast.status == "exceeded"

@pytest.mark.asyncio
async def test_forecast_massive_spend():
    test_date = datetime(2026, 9, 15, tzinfo=timezone.utc)
    forecast = await calculate_forecast("team1", 1e9, 1e6, 50.0, test_date)
    assert forecast.will_exceed is True
    assert forecast.status == "exceeded"

@pytest.mark.asyncio
async def test_forecast_first_day_of_month():
    test_date = datetime(2026, 9, 1, tzinfo=timezone.utc)
    forecast = await calculate_forecast("team1", 0.0, 70.0, 100.0, test_date)
    # Burn rate = 10/day. Remaining = 29 days. Proj = 290. Limit = 100
    assert forecast.days_remaining_in_month == 29
    assert forecast.projected_month_end_spend == 290.0
    assert forecast.status == "warning"

@pytest.mark.asyncio
async def test_forecast_last_day_of_month():
    test_date = datetime(2026, 9, 30, tzinfo=timezone.utc)
    forecast = await calculate_forecast("team1", 50.0, 7.0, 100.0, test_date)
    assert forecast.days_remaining_in_month == 0
    assert forecast.projected_month_end_spend == 50.0
    assert forecast.status == "ok"

@pytest.mark.asyncio
async def test_forecast_no_burn_rate():
    test_date = datetime(2026, 9, 15, tzinfo=timezone.utc)
    forecast = await calculate_forecast("team1", 99.9, 0.0, 100.0, test_date)
    assert forecast.projected_month_end_spend == 99.9
    assert forecast.status == "ok"
    assert forecast.will_exceed is False

@pytest.mark.asyncio
async def test_forecast_exact_limit_hit():
    test_date = datetime(2026, 9, 15, tzinfo=timezone.utc)
    forecast = await calculate_forecast("team1", 100.0, 0.0, 100.0, test_date)
    assert forecast.status == "exceeded"
    assert forecast.will_exceed is True

@pytest.mark.asyncio
async def test_forecast_fractional_days():
    test_date = datetime(2026, 9, 15, 12, 0, 0, tzinfo=timezone.utc)
    forecast = await calculate_forecast("team1", 10.0, 7.0, 100.0, test_date)
    assert forecast.days_remaining_in_month == 15

@pytest.mark.asyncio
async def test_forecast_leap_year():
    test_date = datetime(2024, 2, 10, tzinfo=timezone.utc)
    forecast = await calculate_forecast("team1", 10.0, 7.0, 100.0, test_date)
    assert forecast.days_remaining_in_month == 19  # 29 - 10

# ---------------------------------------------------------
# SUMMARY EDGE CASES (10 tests)
# ---------------------------------------------------------

def test_summary_negative_previous_spend():
    summary = generate_spend_summary("t1", "2026", 100.0, -50.0, "m1", 100.0, "u1", 100.0)
    assert summary.comparison_to_previous_period_pct == 100.0
    assert "up 100.0%" in summary.natural_language_summary

def test_summary_negative_current_spend():
    summary = generate_spend_summary("t1", "2026", -100.0, 100.0, "m1", 100.0, "u1", 100.0)
    assert summary.comparison_to_previous_period_pct == -200.0
    assert "down 200.0%" in summary.natural_language_summary

def test_summary_zero_total_spend_zero_previous():
    summary = generate_spend_summary("t1", "2026", 0.0, 0.0, "m1", 0.0, "u1", 0.0)
    assert summary.comparison_to_previous_period_pct == 0.0
    assert "up 0.0%" in summary.natural_language_summary

def test_summary_tiny_increase():
    summary = generate_spend_summary("t1", "2026", 100.01, 100.0, "m1", 100.0, "u1", 100.0)
    assert summary.comparison_to_previous_period_pct == 0.01
    assert "up 0.0%" in summary.natural_language_summary

def test_summary_massive_increase():
    summary = generate_spend_summary("t1", "2026", 1000000.0, 1.0, "m1", 100.0, "u1", 100.0)
    assert summary.comparison_to_previous_period_pct == 99999900.0

def test_summary_float_precision():
    summary = generate_spend_summary("t1", "2026", 100.333333, 50.111111, "m1", 33.3333, "u1", 33.3333)
    assert summary.total_spend == 100.33
    assert summary.top_model_spend_pct == 33.33

def test_summary_empty_model_data():
    summary = generate_spend_summary("t1", "2026", 100.0, 50.0, "", 0.0, "", 0.0)
    assert "0.0% on " in summary.natural_language_summary

def test_summary_empty_team_id():
    summary = generate_spend_summary("", "2026", 100.0, 50.0, "m1", 100.0, "u1", 100.0)
    assert summary.natural_language_summary.startswith(" spent $")

def test_summary_special_characters_team_id():
    summary = generate_spend_summary("team-@#$!", "2026", 100.0, 50.0, "m1", 100.0, "u1", 100.0)
    assert summary.team_id == "team-@#$!"
    assert "Team-@#$!" in summary.natural_language_summary

def test_summary_exact_zero_percent_change():
    summary = generate_spend_summary("t1", "2026", 100.0, 100.0, "m1", 100.0, "u1", 100.0)
    assert summary.comparison_to_previous_period_pct == 0.0

# ---------------------------------------------------------
# GOVERNANCE EDGE CASES (10 tests)
# ---------------------------------------------------------

@pytest.fixture
def dynamo_mock():
    return MagicMock()

@pytest.fixture
def redis_mock():
    return AsyncMock()

@pytest.mark.asyncio
async def test_gov_create_request_zero_limit(dynamo_mock):
    item = await create_budget_request(dynamo_mock, "t", "team1", "u1", 10.0, 0.0, "test")
    assert item.requested_limit == 0.0
    assert item.status == "pending"

@pytest.mark.asyncio
async def test_gov_create_request_huge_limit(dynamo_mock):
    item = await create_budget_request(dynamo_mock, "t", "team1", "u1", 10.0, 1e12, "test")
    assert item.requested_limit == 1e12

@pytest.mark.asyncio
async def test_gov_create_request_special_chars_reason(dynamo_mock):
    item = await create_budget_request(dynamo_mock, "t", "team1", "u1", 10.0, 20.0, "Need \n\t null \x00 emojis 💰")
    assert "💰" in item.reason

@pytest.mark.asyncio
async def test_gov_list_requests_empty(dynamo_mock):
    dynamo_mock.query.return_value = {"Items": []}
    items = await list_budget_requests(dynamo_mock, "t", "pending", "team1")
    assert len(items) == 0

@pytest.mark.asyncio
async def test_gov_list_requests_missing_fields(dynamo_mock):
    dynamo_mock.query.return_value = {"Items": [{"request_id": {"S": "1"}}]} # Missing lots of fields
    items = await list_budget_requests(dynamo_mock, "t", None, "team1")
    assert items[0].team_id == ""
    assert items[0].current_limit == 0.0

@pytest.mark.asyncio
async def test_gov_approve_non_existent_request(dynamo_mock, redis_mock):
    dynamo_mock.get_item.return_value = {} # Not found
    with pytest.raises(ValueError, match="Budget request not found"):
        await approve_budget_request(dynamo_mock, redis_mock, "t", "team1", "ts1", "admin1")

@pytest.mark.asyncio
async def test_gov_approve_missing_requested_limit(dynamo_mock, redis_mock):
    dynamo_mock.get_item.return_value = {"Item": {"status": {"S": "pending"}}}
    with pytest.raises(ValueError, match="Invalid requested limit"):
        await approve_budget_request(dynamo_mock, redis_mock, "t", "team1", "ts1", "admin1")

@pytest.mark.asyncio
async def test_gov_approve_redis_failure(dynamo_mock, redis_mock):
    dynamo_mock.get_item.return_value = {"Item": {"requested_limit": {"N": "100"}}}
    dynamo_mock.update_item.return_value = {"Attributes": {"status": {"S": "approved"}}}
    redis_mock.set.side_effect = Exception("Redis connection died")
    
    # Should not raise exception, but log it and return parsed item
    item = await approve_budget_request(dynamo_mock, redis_mock, "t", "team1", "ts1", "admin1")
    assert item.status == "approved"

@pytest.mark.asyncio
async def test_gov_deny_redis_never_called(dynamo_mock, redis_mock):
    dynamo_mock.update_item.return_value = {"Attributes": {"status": {"S": "denied"}}}
    item = await deny_budget_request(dynamo_mock, "t", "team1", "ts1", "admin1")
    assert item.status == "denied"
    redis_mock.set.assert_not_called()

@pytest.mark.asyncio
async def test_gov_deny_with_long_reason(dynamo_mock):
    dynamo_mock.update_item.return_value = {"Attributes": {"status": {"S": "denied"}}}
    long_reason = "No" * 1000
    item = await deny_budget_request(dynamo_mock, "t", "team1", "ts1", "admin1", long_reason)
    assert item.status == "denied"
