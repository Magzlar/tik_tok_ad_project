# test_utils.py

import pytest
from utils import calculate_roas, calculate_adjustment_factor, calculate_new_budget, retry
from tik_tok_api import Campaign
from config import TARGET_ROAS, MAX_ADJUSTMENT, MIN_BUDGET


def test_calculate_roas():
    campaign = Campaign(campaign_id="123", spend=100, total_complete_payment_rate=200)
    assert calculate_roas(campaign) == 2.0


def test_calculate_adjustment_factor_above_target():
    roas = TARGET_ROAS * 2
    expected = min((roas - TARGET_ROAS) / TARGET_ROAS, MAX_ADJUSTMENT)
    assert calculate_adjustment_factor(roas) == expected


def test_calculate_adjustment_factor_below_target():
    roas = TARGET_ROAS * 0.25
    expected = max((roas - TARGET_ROAS) / TARGET_ROAS, -MAX_ADJUSTMENT)
    assert calculate_adjustment_factor(roas) == expected


def test_calculate_new_budget_above_minimum():
    current_budget = 100
    adjustment_factor = 0.5
    expected = current_budget * (1 + adjustment_factor)
    assert calculate_new_budget(current_budget, adjustment_factor) == expected


def test_calculate_new_budget_below_minimum():
    current_budget = 40
    adjustment_factor = -0.5
    assert calculate_new_budget(current_budget, adjustment_factor) == MIN_BUDGET


def test_retry_success_immediately():
    def dummy_function():
        return "success"
    assert retry(dummy_function, max_retries=2, delay=0) == "success"


def test_retry_with_fail_then_success(monkeypatch):
    calls = []

    def sometimes_fails():
        if len(calls) < 1:
            calls.append(1)
            raise ValueError("Temporary failure")
        return "success"

    assert retry(sometimes_fails, max_retries=2, delay=0, exception_types=(ValueError,)) == "success"


def test_retry_exceeds_retries(monkeypatch):
    def always_fails():
        raise ValueError("Always fails")

    with pytest.raises(ValueError):
        retry(always_fails, max_retries=1, delay=0, exception_types=(ValueError,))
