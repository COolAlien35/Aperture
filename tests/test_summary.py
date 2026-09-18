import pytest
from gateway.budget.summary import generate_spend_summary


def test_generate_spend_summary_increase():
    summary = generate_spend_summary(
        team_id="engineering",
        period="2026-09",
        total_spend=1240.0,
        previous_period_spend=1076.0,
        top_model_by_spend="claude-3-sonnet",
        top_model_spend_pct=60.0,
        top_spender_by_key_or_user="alice",
        top_spender_spend_pct=42.5,
    )

    assert summary.team_id == "engineering"
    assert summary.comparison_to_previous_period_pct == 15.24
    expected_sentence = "Engineering spent $1,240.00 this month, 60.0% on claude-3-sonnet, up 15.2% from last month."
    assert summary.natural_language_summary == expected_sentence


def test_generate_spend_summary_decrease():
    summary = generate_spend_summary(
        team_id="marketing",
        period="2026-09",
        total_spend=500.0,
        previous_period_spend=1000.0,
        top_model_by_spend="gpt-4",
        top_model_spend_pct=80.0,
        top_spender_by_key_or_user="bob",
        top_spender_spend_pct=50.0,
    )

    assert summary.comparison_to_previous_period_pct == -50.0
    expected_sentence = "Marketing spent $500.00 this month, 80.0% on gpt-4, down 50.0% from last month."
    assert summary.natural_language_summary == expected_sentence


def test_generate_spend_summary_from_zero():
    summary = generate_spend_summary(
        team_id="sales",
        period="2026-09",
        total_spend=100.0,
        previous_period_spend=0.0,
        top_model_by_spend="gpt-3.5-turbo",
        top_model_spend_pct=100.0,
        top_spender_by_key_or_user="charlie",
        top_spender_spend_pct=100.0,
    )

    assert summary.comparison_to_previous_period_pct == 100.0
    expected_sentence = "Sales spent $100.00 this month, 100.0% on gpt-3.5-turbo, up 100.0% from last month."
    assert summary.natural_language_summary == expected_sentence
