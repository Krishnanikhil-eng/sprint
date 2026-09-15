from src.analytics.db_ratio_validator import validate_financial_ratios_db


def test_db_ratios_validation_pass():
    res = validate_financial_ratios_db("nifty100.db")
    assert res["row_count"] >= 1100
    assert res["duplicate_rows"] == 0
    assert res["sbin_present"] is True
    assert res["sbin_rows"] > 0
    assert res["atgl_present"] is True
    assert res["atgl_rows"] > 0
    assert res["validation_passed"] is True
