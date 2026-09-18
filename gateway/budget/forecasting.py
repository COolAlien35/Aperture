from datetime import datetime, timezone, timedelta
import calendar
import logging
from gateway.models.forecasting import ForecastResponse

logger = logging.getLogger(__name__)


async def calculate_forecast(
    team_id: str,
    current_spend: float,
    trailing_7d_spend: float,
    budget_limit: float,
    current_date: datetime = None,
) -> ForecastResponse:
    """
    Computes a linear projection for the current month's budget.
    """
    if current_date is None:
        current_date = datetime.now(timezone.utc)

    year = current_date.year
    month = current_date.month
    day = current_date.day

    _, last_day = calendar.monthrange(year, month)
    days_remaining = last_day - day

    # Average daily spend over the trailing 7 days
    daily_burn_rate = trailing_7d_spend / 7.0

    projected_month_end_spend = current_spend + (daily_burn_rate * days_remaining)

    will_exceed = projected_month_end_spend > budget_limit

    status = "ok"
    exceed_date_estimate = None

    if current_spend >= budget_limit:
        status = "exceeded"
        will_exceed = True
        exceed_date_estimate = "already_exceeded"
    elif will_exceed and daily_burn_rate > 0:
        status = "warning"
        # Days until limit is hit = remaining budget / daily burn rate
        days_until_exceed = (budget_limit - current_spend) / daily_burn_rate
        exceed_date = current_date + timedelta(days=days_until_exceed)
        exceed_date_estimate = exceed_date.strftime("%Y-%m-%d")

    return ForecastResponse(
        team_id=team_id,
        current_spend=round(current_spend, 2),
        projected_month_end_spend=round(projected_month_end_spend, 2),
        budget_limit=round(budget_limit, 2),
        will_exceed=will_exceed,
        exceed_date_estimate=exceed_date_estimate,
        daily_burn_rate=round(daily_burn_rate, 2),
        days_remaining_in_month=days_remaining,
        status=status,
    )
