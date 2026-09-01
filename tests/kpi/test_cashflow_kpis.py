import pytest
from src.analytics.cashflow_kpis import (
    calculate_free_cash_flow,
    calculate_cfo_quality_score,
    calculate_capex_intensity,
    calculate_fcf_conversion,
    classify_capital_allocation,
)

def test_free_cash_flow():
    # Operating 500, Investing -200 => FCF = 300
    assert calculate_free_cash_flow(500.0, -200.0) == 300.0
    # Operating 100, Investing -300 => Negative FCF = -200
    assert calculate_free_cash_flow(100.0, -300.0) == -200.0

def test_cfo_quality_score():
    cfo = [120.0, 150.0, 110.0, 130.0, 140.0]
    pat = [100.0, 100.0, 100.0, 100.0, 100.0]
    score, label = calculate_cfo_quality_score(cfo, pat)
    assert score == 1.3
    assert label == "High Quality"

def test_capex_intensity():
    # abs(-50) / 1000 * 100 = 5% => Moderate
    intensity, label = calculate_capex_intensity(-50.0, 1000.0)
    assert intensity == 5.0
    assert label == "Moderate"

def test_fcf_conversion():
    assert calculate_fcf_conversion(300.0, 400.0) == 75.0
    assert calculate_fcf_conversion(300.0, 0.0) is None

def test_capital_allocation_patterns():
    # (+,-,-) Reinvestor vs Shareholder Returns
    _, _, _, label1 = classify_capital_allocation(500, -200, -100, cfo_pat_ratio=0.8)
    assert label1 == "Reinvestor"
    
    _, _, _, label2 = classify_capital_allocation(500, -200, -100, cfo_pat_ratio=1.5)
    assert label2 == "Shareholder Returns"
    
    # (+,+,-) Liquidating Assets
    _, _, _, label3 = classify_capital_allocation(500, 100, -100)
    assert label3 == "Liquidating Assets"
    
    # (-,+,+) Distress Signal
    _, _, _, label4 = classify_capital_allocation(-100, 50, 50)
    assert label4 == "Distress Signal"
    
    # (-,-,+) Growth Funded by Debt
    _, _, _, label5 = classify_capital_allocation(-100, -200, 300)
    assert label5 == "Growth Funded by Debt"
    
    # (+,+,+) Cash Accumulator
    _, _, _, label6 = classify_capital_allocation(100, 50, 50)
    assert label6 == "Cash Accumulator"
    
    # (-,-,-) Pre-Revenue
    _, _, _, label7 = classify_capital_allocation(-10, -20, -30)
    assert label7 == "Pre-Revenue"
    
    # (+,-,+) Mixed
    _, _, _, label8 = classify_capital_allocation(100, -50, 20)
    assert label8 == "Mixed"
