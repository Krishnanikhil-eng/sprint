import pytest
from src.analytics.ratios import (
    calculate_net_profit_margin,
    calculate_operating_profit_margin,
    cross_check_opm,
    calculate_roe,
    calculate_roce,
    calculate_roa,
)

def test_net_profit_margin_normal():
    assert calculate_net_profit_margin(150.0, 1000.0) == 15.0

def test_net_profit_margin_zero_sales():
    assert calculate_net_profit_margin(150.0, 0.0) is None
    assert calculate_net_profit_margin(150.0, None) is None

def test_operating_profit_margin_normal_and_cross_check():
    opm = calculate_operating_profit_margin(200.0, 1000.0)
    assert opm == 20.0
    
    # Matching cross-check
    has_disc, diff = cross_check_opm(opm, 20.2)
    assert has_disc is False
    assert diff == 0.2
    
    # Mismatch cross-check (>1% diff)
    has_disc_mismatch, diff_mismatch = cross_check_opm(opm, 22.5)
    assert has_disc_mismatch is True
    assert diff_mismatch == 2.5

def test_roe_normal():
    assert calculate_roe(200.0, 100.0, 900.0) == 20.0  # 200 / (100+900) * 100 = 20.0%

def test_roe_negative_equity():
    assert calculate_roe(100.0, 100.0, -200.0) is None  # Total equity -100 <= 0 -> None
    assert calculate_roe(100.0, 50.0, -50.0) is None   # Total equity 0 <= 0 -> None

def test_roce_normal():
    # EBIT = 300, equity = 100, reserves = 900, borrowings = 500 => Capital Employed = 1500 => ROCE = 300/1500*100 = 20%
    assert calculate_roce(300.0, 100.0, 900.0, 500.0) == 20.0

def test_roce_zero_capital():
    assert calculate_roce(300.0, 0.0, 0.0, 0.0) is None

def test_roa_normal_and_zero():
    assert calculate_roa(100.0, 2000.0) == 5.0
    assert calculate_roa(100.0, 0.0) is None
    assert calculate_roa(100.0, -50.0) is None
