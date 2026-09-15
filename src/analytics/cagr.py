"""
CAGR Engine Module.
Computes 3Y, 5Y, 10Y Compound Annual Growth Rate (CAGR) for Revenue, PAT, and EPS
with robust 6-state edge case handling.
"""

from typing import Optional, Tuple, Dict

# Flag constants
FLAG_NORMAL = "NORMAL"
FLAG_DECLINE_TO_LOSS = "DECLINE_TO_LOSS"
FLAG_TURNAROUND = "TURNAROUND"
FLAG_BOTH_NEGATIVE = "BOTH_NEGATIVE"
FLAG_ZERO_BASE = "ZERO_BASE"
FLAG_INSUFFICIENT = "INSUFFICIENT"


def calculate_cagr(
    start_val: Optional[float], end_val: Optional[float], n_years: int
) -> Tuple[Optional[float], str]:
    """
    Calculates Compound Annual Growth Rate (CAGR) = ((end / start) ** (1 / n) - 1) * 100

    Handles 6 Edge Cases:
    1. Positive -> Positive: NORMAL CAGR
    2. Positive -> Negative: None, DECLINE_TO_LOSS
    3. Negative -> Positive: None, TURNAROUND
    4. Negative -> Negative: None, BOTH_NEGATIVE
    5. Zero Base (start == 0): None, ZERO_BASE
    6. Insufficient Data / Invalid n: None, INSUFFICIENT
    """
    if start_val is None or end_val is None or n_years <= 0:
        return None, FLAG_INSUFFICIENT

    if start_val == 0:
        return None, FLAG_ZERO_BASE

    if start_val > 0 and end_val > 0:
        cagr = ((end_val / start_val) ** (1.0 / n_years) - 1.0) * 100.0
        return round(cagr, 4), FLAG_NORMAL

    if start_val > 0 and end_val < 0:
        return None, FLAG_DECLINE_TO_LOSS

    if start_val < 0 and end_val > 0:
        return None, FLAG_TURNAROUND

    if start_val < 0 and end_val < 0:
        return None, FLAG_BOTH_NEGATIVE

    # Handle end_val == 0 with positive/negative start_val
    if end_val == 0:
        if start_val > 0:
            return None, FLAG_DECLINE_TO_LOSS
        else:
            return None, FLAG_TURNAROUND

    return None, FLAG_INSUFFICIENT


def calculate_series_cagr(
    time_series: Dict[int, float], end_year: int, n_years: int
) -> Tuple[Optional[float], str]:
    """
    Given a dictionary mapping year -> metric value, extracts start_val and end_val
    and calculates n_years CAGR.
    """
    start_year = end_year - n_years
    if start_year not in time_series or end_year not in time_series:
        return None, FLAG_INSUFFICIENT

    return calculate_cagr(time_series[start_year], time_series[end_year], n_years)
