"""
Cash Flow KPIs and Capital Allocation Classifier Module.
Calculates Free Cash Flow, CFO Quality Score, CapEx Intensity, FCF Conversion,
and classifies 8-pattern Capital Allocation profiles.
"""

from typing import Optional, Tuple, Dict, List

def calculate_free_cash_flow(operating_activity: Optional[float], investing_activity: Optional[float]) -> Optional[float]:
    """
    Free Cash Flow = operating_activity + investing_activity
    Note: Investing activity is typically negative (outflow for capex), so addition computes FCF.
    Negative FCF is valid.
    """
    if operating_activity is None or investing_activity is None:
        return None
    return round(operating_activity + investing_activity, 4)

def calculate_cfo_quality_score(cfo_list: List[float], pat_list: List[float]) -> Tuple[Optional[float], Optional[str]]:
    """
    CFO Quality Score = average(CFO / PAT) over 5 years.
    Classifications:
    - > 1.0: High Quality
    - 0.5 - 1.0: Moderate
    - < 0.5: Accrual Risk
    """
    if not cfo_list or not pat_list or len(cfo_list) != len(pat_list):
        return None, None
    
    ratios = []
    for cfo, pat in zip(cfo_list, pat_list):
        if pat is not None and pat != 0 and cfo is not None:
            ratios.append(cfo / pat)
            
    if not ratios:
        return None, None
        
    avg_score = round(sum(ratios) / len(ratios), 4)
    if avg_score > 1.0:
        label = "High Quality"
    elif avg_score >= 0.5:
        label = "Moderate"
    else:
        label = "Accrual Risk"
        
    return avg_score, label

def calculate_capex_intensity(investing_activity: Optional[float], sales: Optional[float]) -> Tuple[Optional[float], Optional[str]]:
    """
    CapEx Intensity = abs(investing_activity) / sales * 100
    Classifications:
    - < 3%: Asset Light
    - 3 - 8%: Moderate
    - > 8%: Capital Intensive
    """
    if investing_activity is None or sales is None or sales <= 0:
        return None, None
        
    intensity = round((abs(investing_activity) / sales) * 100, 4)
    if intensity < 3.0:
        label = "Asset Light"
    elif intensity <= 8.0:
        label = "Moderate"
    else:
        label = "Capital Intensive"
        
    return intensity, label

def calculate_fcf_conversion(fcf: Optional[float], operating_profit: Optional[float]) -> Optional[float]:
    """
    FCF Conversion Rate = FCF / operating_profit * 100
    Rule: operating_profit == 0 or None -> None
    """
    if fcf is None or operating_profit is None or operating_profit == 0:
        return None
    return round((fcf / operating_profit) * 100, 4)

def classify_capital_allocation(
    cfo: Optional[float],
    cfi: Optional[float],
    cff: Optional[float],
    cfo_pat_ratio: Optional[float] = None
) -> Tuple[str, str, str, str]:
    """
    Classifies 8-pattern Capital Allocation based on signs (+/-) of (CFO, CFI, CFF):
    - (+, -, -) -> Shareholder Returns if cfo_pat_ratio > 1.0 else Reinvestor
    - (+, +, -) -> Liquidating Assets
    - (-, +, +) -> Distress Signal
    - (-, -, +) -> Growth Funded by Debt
    - (+, +, +) -> Cash Accumulator
    - (-, -, -) -> Pre-Revenue
    - (+, -, +) -> Mixed
    Returns (cfo_sign, cfi_sign, cff_sign, pattern_label)
    """
    if cfo is None or cfi is None or cff is None:
        return "?", "?", "?", "Unknown"
        
    cfo_sign = "+" if cfo >= 0 else "-"
    cfi_sign = "+" if cfi >= 0 else "-"
    cff_sign = "+" if cff >= 0 else "-"
    
    pattern = (cfo_sign, cfi_sign, cff_sign)
    
    if pattern == ("+", "-", "-"):
        if cfo_pat_ratio is not None and cfo_pat_ratio > 1.0:
            label = "Shareholder Returns"
        else:
            label = "Reinvestor"
    elif pattern == ("+", "+", "-"):
        label = "Liquidating Assets"
    elif pattern == ("-", "+", "+"):
        label = "Distress Signal"
    elif pattern == ("-", "-", "+"):
        label = "Growth Funded by Debt"
    elif pattern == ("+", "+", "+"):
        label = "Cash Accumulator"
    elif pattern == ("-", "-", "-"):
        label = "Pre-Revenue"
    elif pattern == ("+", "-", "+"):
        label = "Mixed"
    else:
        label = "Distress Signal" if cfo < 0 else "Mixed"
        
    return cfo_sign, cfi_sign, cff_sign, label
