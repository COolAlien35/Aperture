from pydantic import BaseModel
from typing import Optional


class ForecastResponse(BaseModel):
    team_id: str
    current_spend: float
    projected_month_end_spend: float
    budget_limit: float
    will_exceed: bool
    exceed_date_estimate: Optional[str] = None
    daily_burn_rate: float
    days_remaining_in_month: int
    status: str  # "ok", "warning", "exceeded"
