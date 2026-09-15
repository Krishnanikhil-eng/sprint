from src.analytics.ratios import (
    calculate_debt_to_equity,
    check_high_leverage_flag,
    calculate_interest_coverage,
    calculate_net_debt,
    calculate_asset_turnover,
)


def test_debt_to_equity_zero_borrowings():
    # Borrowings 0 should return 0.0, NOT None
    assert calculate_debt_to_equity(0.0, 100.0, 400.0) == 0.0
    assert calculate_debt_to_equity(None, 100.0, 400.0) == 0.0


def test_debt_to_equity_normal_and_negative_equity():
    assert calculate_debt_to_equity(500.0, 100.0, 400.0) == 1.0
    assert calculate_debt_to_equity(500.0, 100.0, -200.0) is None


def test_high_leverage_flag():
    # D/E > 5 non-bank -> True
    assert check_high_leverage_flag(6.0, is_financials=False) is True
    # D/E > 5 bank -> False (suppressed)
    assert check_high_leverage_flag(6.0, is_financials=True) is False
    # D/E <= 5 non-bank -> False
    assert check_high_leverage_flag(4.5, is_financials=False) is False


def test_interest_coverage_zero_interest():
    icr, label, warning = calculate_interest_coverage(100.0, 20.0, 0.0)
    assert icr is None
    assert label == "Debt Free"
    assert warning is False


def test_interest_coverage_low_coverage_warning():
    # EBIT = 100 + 20 = 120, interest = 100 => ICR = 1.2 (< 1.5 -> Warning)
    icr, label, warning = calculate_interest_coverage(100.0, 20.0, 100.0)
    assert icr == 1.2
    assert label == "Low Coverage"
    assert warning is True


def test_interest_coverage_normal():
    # EBIT = 300, interest = 50 => ICR = 6.0
    icr, label, warning = calculate_interest_coverage(250.0, 50.0, 50.0)
    assert icr == 6.0
    assert label == "Normal Coverage"
    assert warning is False


def test_net_debt():
    assert calculate_net_debt(1000.0, 300.0) == 700.0
    assert calculate_net_debt(1000.0, None) == 1000.0


def test_asset_turnover():
    assert calculate_asset_turnover(2000.0, 1000.0) == 2.0
    assert calculate_asset_turnover(2000.0, 0.0) is None
