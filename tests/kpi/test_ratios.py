"""
Comprehensive Unit Tests for Financial Ratio Engine (Day 41).
Validates 20 distinct ratio calculation edge cases including zero division, negative values,
financial sector exemptions, and CAGR edge cases.
"""

from src.analytics.ratios import (
    calculate_net_profit_margin,
    calculate_operating_profit_margin,
    calculate_roe,
    calculate_roce,
    calculate_debt_to_equity,
    calculate_interest_coverage,
    calculate_asset_turnover,
    cross_check_opm,
)
from src.analytics.cagr import calculate_cagr


def test_npm_normal():
    assert calculate_net_profit_margin(150, 1000) == 15.0


def test_npm_zero_sales():
    assert calculate_net_profit_margin(150, 0) is None


def test_npm_negative_profit():
    assert calculate_net_profit_margin(-50, 1000) == -5.0


def test_npm_none_input():
    assert calculate_net_profit_margin(None, 1000) is None


def test_opm_normal():
    assert calculate_operating_profit_margin(250, 1000) == 25.0


def test_opm_cross_check_match():
    has_disc, diff = cross_check_opm(25.0, 25.1)
    assert not has_disc
    assert diff == 0.1


def test_opm_cross_check_discrepancy():
    has_disc, diff = cross_check_opm(25.0, 28.0)
    assert has_disc
    assert diff == 3.0


def test_roe_normal():
    assert calculate_roe(100, 50, 450) == 20.0


def test_roe_negative_equity():
    assert calculate_roe(100, 50, -100) is None


def test_roe_zero_equity():
    assert calculate_roe(100, 0, 0) is None


def test_roce_normal():
    assert calculate_roce(200, 100, 400, 500, is_financials=False) == 20.0


def test_roce_financials_exemption():
    assert calculate_roce(200, 100, 400, 500, is_financials=True) is None


def test_de_normal():
    assert calculate_debt_to_equity(500, 100, 400) == 1.0


def test_de_zero_debt():
    assert calculate_debt_to_equity(0, 100, 400) == 0.0


def test_de_negative_equity():
    assert calculate_debt_to_equity(500, 50, -100) is None


def test_icr_normal():
    icr, label, flag = calculate_interest_coverage(450, 50, 50)
    assert icr == 10.0
    assert label == "Normal Coverage"
    assert not flag


def test_icr_zero_interest():
    icr, label, flag = calculate_interest_coverage(500, 0, 0)
    assert icr is None
    assert label == "Debt Free"
    assert not flag


def test_asset_turnover_normal():
    assert calculate_asset_turnover(1000, 500) == 2.0


def test_cagr_5yr_normal():
    cagr, flag = calculate_cagr(100, 200, 5)
    assert cagr is not None
    assert round(cagr, 2) == 14.87
    assert flag == "NORMAL"


def test_cagr_negative_start_value():
    cagr, flag = calculate_cagr(-100, 200, 5)
    assert cagr is None
    assert flag == "TURNAROUND"
