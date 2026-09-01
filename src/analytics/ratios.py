"""
Financial Ratios Calculation Module.
Provides clean, robust functions for profitability, leverage, and efficiency ratios.
"""

from typing import Optional, Tuple, Dict, Any

def calculate_net_profit_margin(net_profit: Optional[float], sales: Optional[float]) -> Optional[float]:
    """
    Net Profit Margin = net_profit / sales * 100
    Rule: sales == 0 or sales is None -> None
    """
    if sales is None or sales == 0 or net_profit is None:
        return None
    return round((net_profit / sales) * 100, 4)

def calculate_operating_profit_margin(operating_profit: Optional[float], sales: Optional[float]) -> Optional[float]:
    """
    Operating Profit Margin = operating_profit / sales * 100
    Rule: sales == 0 or sales is None -> None
    """
    if sales is None or sales == 0 or operating_profit is None:
        return None
    return round((operating_profit / sales) * 100, 4)

def cross_check_opm(calculated_opm: Optional[float], source_opm: Optional[float]) -> Tuple[bool, float]:
    """
    Cross-checks calculated OPM against source opm_percentage.
    Returns (has_discrepancy, abs_diff). Log if abs_diff > 1.0%.
    """
    if calculated_opm is None or source_opm is None:
        return False, 0.0
    abs_diff = round(abs(calculated_opm - source_opm), 4)
    has_discrepancy = abs_diff > 1.0
    return has_discrepancy, abs_diff

def calculate_roe(net_profit: Optional[float], equity_capital: Optional[float], reserves: Optional[float]) -> Optional[float]:
    """
    Return on Equity (ROE) = net_profit / (equity_capital + reserves) * 100
    Rule: equity + reserves <= 0 -> None
    """
    if net_profit is None or equity_capital is None or reserves is None:
        return None
    total_equity = equity_capital + reserves
    if total_equity <= 0:
        return None
    return round((net_profit / total_equity) * 100, 4)

def calculate_roce(
    ebit: Optional[float],
    equity_capital: Optional[float],
    reserves: Optional[float],
    borrowings: Optional[float],
    is_financials: bool = False,
    sector_roce_benchmark: Optional[float] = None
) -> Optional[float]:
    """
    Return on Capital Employed (ROCE) = EBIT / (equity + reserves + borrowings) * 100
    Rule: capital_employed <= 0 -> None
    For Financials: ROCE is benchmarked relative to sector benchmark.
    """
    if ebit is None or equity_capital is None or reserves is None or borrowings is None:
        return None
    capital_employed = equity_capital + reserves + borrowings
    if capital_employed <= 0:
        return None
    roce = round((ebit / capital_employed) * 100, 4)
    return roce

def calculate_roa(net_profit: Optional[float], total_assets: Optional[float]) -> Optional[float]:
    """
    Return on Assets (ROA) = net_profit / total_assets * 100
    Rule: total_assets <= 0 or None -> None
    """
    if net_profit is None or total_assets is None or total_assets <= 0:
        return None
    return round((net_profit / total_assets) * 100, 4)
