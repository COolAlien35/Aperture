import pytest
from datetime import datetime, timezone
from gateway.budget.forecasting import calculate_forecast


@pytest.mark.asyncio
async def test_calculate_forecast_ok():
    # 15 days left in month (assume 30-day month for simplicity, let's use a specific date)
    test_date = datetime(
        2026, 9, 15, tzinfo=timezone.utc
    )  # September has 30 days, 15 days left

    forecast = await calculate_forecast(
        team_id="team1",
        current_spend=10.0,
        trailing_7d_spend=7.0,  # $1 per day
        budget_limit=50.0,
        current_date=test_date,
    )

    assert forecast.team_id == "team1"
    assert forecast.current_spend == 10.0
    assert forecast.daily_burn_rate == 1.0
    assert forecast.days_remaining_in_month == 15
    assert forecast.projected_month_end_spend == 25.0
    assert forecast.will_exceed is False
    assert forecast.status == "ok"
    assert forecast.exceed_date_estimate is None


@pytest.mark.asyncio
async def test_calculate_forecast_warning():
    test_date = datetime(2026, 9, 15, tzinfo=timezone.utc)

    forecast = await calculate_forecast(
        team_id="team1",
        current_spend=40.0,
        trailing_7d_spend=14.0,  # $2 per day
        budget_limit=50.0,
        current_date=test_date,
    )

    assert forecast.current_spend == 40.0
    assert forecast.daily_burn_rate == 2.0
    assert forecast.days_remaining_in_month == 15
    assert forecast.projected_month_end_spend == 70.0  # 40 + (2 * 15)
    assert forecast.will_exceed is True
    assert forecast.status == "warning"

    # Needs $10 to exceed, at $2/day = 5 days.
    # Sept 15 + 5 days = Sept 20
    assert forecast.exceed_date_estimate == "2026-09-20"


@pytest.mark.asyncio
async def test_calculate_forecast_already_exceeded():
    test_date = datetime(2026, 9, 15, tzinfo=timezone.utc)

    forecast = await calculate_forecast(
        team_id="team1",
        current_spend=55.0,
        trailing_7d_spend=14.0,
        budget_limit=50.0,
        current_date=test_date,
    )

    assert forecast.will_exceed is True
    assert forecast.status == "exceeded"
    assert forecast.exceed_date_estimate == "already_exceeded"


@pytest.mark.asyncio
async def test_calculate_forecast_zero_burn():
    test_date = datetime(2026, 9, 15, tzinfo=timezone.utc)

    forecast = await calculate_forecast(
        team_id="team1",
        current_spend=10.0,
        trailing_7d_spend=0.0,
        budget_limit=50.0,
        current_date=test_date,
    )

    assert forecast.daily_burn_rate == 0.0
    assert forecast.projected_month_end_spend == 10.0
    assert forecast.will_exceed is False
    assert forecast.status == "ok"
