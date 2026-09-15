from src.analytics.bank_benchmark_validator import validate_bank_carveout_rules


def test_bank_carveout_rules_pass():
    res = validate_bank_carveout_rules("nifty100.db")
    assert res["fin_roce_non_null_count"] == 0
    assert res["fin_high_leverage_active_count"] == 0
    assert res["passed"] is True
