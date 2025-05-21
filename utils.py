# utils.py

from tik_tok_api import Campaign
from config import TARGET_ROAS, MAX_ADJUSTMENT, MIN_BUDGET
import time

def calculate_roas(campaign: Campaign) -> float:
    """Calculate the Return on Ad Spend (ROAS)"""
    return campaign.total_complete_payment_rate / campaign.spend

def calculate_adjustment_factor(roas: float) -> float:
    """Calculate the proportional adjustment factor based on target ROAS."""
    adjustment = (roas - TARGET_ROAS) / TARGET_ROAS
    return max(min(adjustment, MAX_ADJUSTMENT), -MAX_ADJUSTMENT)

def calculate_new_budget(current_budget: float, adjustment_factor: float) -> float:
    """Apply the adjustment factor and clamp to minimum budget."""
    new_budget = current_budget * (1 + adjustment_factor)
    return max(new_budget, MIN_BUDGET)


def retry(func, max_retries=2, delay=300, exception_types=(Exception,), *args, **kwargs):
    """
    Executes a function with retry logic for handling transient errors.

    Parameters:
        func (callable): The function to execute.
        max_retries (int): The maximum number of retry attempts. Defaults to 2.
        delay (int): Delay between retries in seconds. Defaults to 300 (5 minutes).
        exception_types (tuple): A tuple of exception classes that will trigger a retry. Defaults to (Exception,).
        *args: Positional arguments to pass to the function.
        **kwargs: Keyword arguments to pass to the function.

    Returns:
        Any: The return value of the function if successful.

    Raises:
        Exception: Re-raises the last exception encountered if all retries fail.
    """
    attempt = 0
    while attempt <= max_retries:
        try:
            return func(*args, **kwargs)
        except exception_types as e:
            attempt += 1
            if attempt > max_retries:
                raise
            print(f"Error: {e}. Retrying in {delay} seconds... (Attempt {attempt}/{max_retries})")
            time.sleep(delay)
