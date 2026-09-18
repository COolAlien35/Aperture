import logging
from gateway.models.summary import SpendSummaryResponse

logger = logging.getLogger(__name__)


def generate_spend_summary(
    team_id: str,
    period: str,
    total_spend: float,
    previous_period_spend: float,
    top_model_by_spend: str,
    top_model_spend_pct: float,
    top_spender_by_key_or_user: str,
    top_spender_spend_pct: float,
) -> SpendSummaryResponse:
    """
    Generates a structured spend summary with a plain-language sentence for dashboards.
    """
    if previous_period_spend > 0:
        comparison_pct = (
            (total_spend - previous_period_spend) / previous_period_spend
        ) * 100.0
    elif total_spend > 0:
        comparison_pct = (
            100.0  # From 0 to something is a 100% increase by convention here
        )
    else:
        comparison_pct = 0.0

    trend = "up" if comparison_pct >= 0 else "down"
    abs_pct = abs(comparison_pct)

    # Capitalize team_id for the sentence
    team_name = team_id.capitalize()

    sentence = (
        f"{team_name} spent ${total_spend:,.2f} this month, "
        f"{top_model_spend_pct:.1f}% on {top_model_by_spend}, "
        f"{trend} {abs_pct:.1f}% from last month."
    )

    return SpendSummaryResponse(
        team_id=team_id,
        period=period,
        total_spend=round(total_spend, 2),
        previous_period_spend=round(previous_period_spend, 2),
        comparison_to_previous_period_pct=round(comparison_pct, 2),
        top_model_by_spend=top_model_by_spend,
        top_model_spend_pct=round(top_model_spend_pct, 2),
        top_spender_by_key_or_user=top_spender_by_key_or_user,
        top_spender_spend_pct=round(top_spender_spend_pct, 2),
        natural_language_summary=sentence,
    )
