from pydantic import BaseModel
from typing import Optional


class SpendSummaryResponse(BaseModel):
    team_id: str
    period: str
    total_spend: float
    previous_period_spend: float
    comparison_to_previous_period_pct: float
    top_model_by_spend: str
    top_model_spend_pct: float
    top_spender_by_key_or_user: str
    top_spender_spend_pct: float
    natural_language_summary: str
