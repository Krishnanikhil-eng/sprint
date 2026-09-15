"""
Unit tests for ETL validator module (DataQualityValidator and DQ rules DQ-01 to DQ-16).
"""

import pandas as pd
from src.etl.validator import DataQualityValidator


def test_validator_dq01_ticker_format():
    validator = DataQualityValidator()
    df = pd.DataFrame({"company_id": ["RELIANCE", "invalid_lower", "TCS"]})
    fails = validator.check_dq01_ticker_format(df, "companies")
    assert fails == 1
    assert len(validator.failures) == 1
    assert validator.failures[0].rule_id == "DQ-01"


def test_validator_dq02_missing_ticker():
    validator = DataQualityValidator()
    df = pd.DataFrame({"company_id": ["RELIANCE", None, "   "]})
    fails = validator.check_dq02_missing_ticker(df, "companies")
    assert fails == 2
    assert validator.failures[0].rule_id == "DQ-02"


def test_validator_dq03_duplicate_company():
    validator = DataQualityValidator()
    df = pd.DataFrame({"company_id": ["RELIANCE", "RELIANCE", "TCS"]})
    fails = validator.check_dq03_duplicate_company(df, "companies")
    assert fails == 2


def test_validator_dq04_year_range():
    validator = DataQualityValidator()
    df = pd.DataFrame({"company_id": ["RELIANCE", "TCS"], "year": [2023, 1850]})
    fails = validator.check_dq04_year_range(df, "profitandloss")
    assert fails == 1


def test_validator_dq05_missing_year():
    validator = DataQualityValidator()
    df = pd.DataFrame({"company_id": ["RELIANCE", "TCS"], "year": [2023, None]})
    fails = validator.check_dq05_missing_year(df, "profitandloss")
    assert fails == 1


def test_validator_dq06_duplicate_year_per_company():
    validator = DataQualityValidator()
    df = pd.DataFrame({"company_id": ["RELIANCE", "RELIANCE"], "year": [2023, 2023]})
    fails = validator.check_dq06_duplicate_year_per_company(df, "profitandloss")
    assert fails == 2


def test_validator_dq09_balance_sheet_equation():
    validator = DataQualityValidator()
    df = pd.DataFrame(
        {
            "company_id": ["RELIANCE", "TCS"],
            "year": [2023, 2023],
            "total_assets": [1000, 2000],
            "total_liabilities": [1000, 1500],  # TCS mismatch
        }
    )
    fails = validator.check_dq09_balance_sheet_equation(df, "balancesheet")
    assert fails == 1
    assert validator.failures[0].rule_id == "DQ-09"


def test_validator_dq10_sales_non_negative():
    validator = DataQualityValidator()
    df = pd.DataFrame(
        {"company_id": ["RELIANCE", "TCS"], "year": [2023, 2023], "sales": [5000, -100]}
    )
    fails = validator.check_dq10_sales_non_negative(df, "profitandloss")
    assert fails == 1
    assert validator.failures[0].rule_id == "DQ-10"


def test_validator_full_pipeline_run():
    data_dict = {
        "companies": pd.DataFrame({"company_id": ["RELIANCE", "TCS"]}),
        "profitandloss": pd.DataFrame(
            {
                "company_id": ["RELIANCE", "TCS"],
                "year": [2023, 2023],
                "sales": [1000, 2000],
            }
        ),
    }
    validator = DataQualityValidator()
    results = validator.validate_tables(data_dict)
    assert len(results) == 16
    assert results["DQ-01"]["status"] == "PASS"
    assert results["DQ-10"]["status"] == "PASS"
