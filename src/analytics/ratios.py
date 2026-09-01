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

def calculate_debt_to_equity(
    borrowings: Optional[float],
    equity_capital: Optional[float],
    reserves: Optional[float]
) -> Optional[float]:
    """
    Debt-to-Equity = borrowings / (equity_capital + reserves)
    Rules:
    - borrowings == 0 -> 0.0 (NOT None)
    - equity + reserves <= 0 -> None
    """
    if equity_capital is None or reserves is None:
        return None
    total_equity = equity_capital + reserves
    if total_equity <= 0:
        return None
    if borrowings is None or borrowings == 0:
        return 0.0
    return round(borrowings / total_equity, 4)

def check_high_leverage_flag(debt_to_equity: Optional[float], is_financials: bool) -> bool:
    """
    High Leverage Flag = True when D/E > 5 and company is NOT Financials.
    Suppressed for Financials (Banks, NBFCs, etc.).
    """
    if debt_to_equity is None or is_financials:
        return False
    return debt_to_equity > 5.0

def calculate_interest_coverage(
    operating_profit: Optional[float],
    other_income: Optional[float],
    interest: Optional[float]
) -> Tuple[Optional[float], Optional[str], bool]:
    """
    Interest Coverage Ratio = (operating_profit + other_income) / interest
    Rules:
    - interest == 0 or None -> ICR is None, icr_label = "Debt Free", warning_flag = False
    - ICR < 1.5 -> warning_flag = True, icr_label = "Low Coverage"
    """
    if interest is None or interest == 0:
        return None, "Debt Free", False
    
    op = operating_profit if operating_profit is not None else 0.0
    oi = other_income if other_income is not None else 0.0
    ebit = op + oi
    
    icr = round(ebit / interest, 4)
    warning_flag = icr < 1.5
    icr_label = "Low Coverage" if warning_flag else "Normal Coverage"
    return icr, icr_label, warning_flag

def calculate_net_debt(borrowings: Optional[float], investments: Optional[float]) -> Optional[float]:
    """
    Net Debt = borrowings - investments (using investments as liquid asset proxy)
    """
    if borrowings is None:
        return None
    inv = investments if investments is not None else 0.0
    return round(borrowings - inv, 4)

def calculate_asset_turnover(sales: Optional[float], total_assets: Optional[float]) -> Optional[float]:
    """
    Asset Turnover = sales / total_assets
    Rule: total_assets == 0 or None -> None
    """
    if sales is None or total_assets is None or total_assets <= 0:
        return None
    return round(sales / total_assets, 4)

