"""
Unit tests for NLP analysis text parser (Day 29).
"""

import sqlite3

from src.nlp.parser import (
    parse_metric_text,
    validate_cagr_against_db,
)


def test_parse_metric_text_normal():
    period, val, err = parse_metric_text("10 Years: 21%")
    assert err is None
    assert period == 10
    assert val == 21.0


def test_parse_metric_text_singular():
    period, val, err = parse_metric_text("5 Year: 15.5%")
    assert err is None
    assert period == 5
    assert val == 15.5


def test_parse_metric_text_whitespace_variations():
    cases = [
        ("10 Years:21%", 10, 21.0),
        ("10 Years : 21.5%", 10, 21.5),
        (" 3  Years:   12% ", 3, 12.0),
        ("1 Year: -2%", 1, -2.0),
    ]
    for text, exp_period, exp_val in cases:
        period, val, err = parse_metric_text(text)
        assert err is None, f"Failed for {text}"
        assert period == exp_period
        assert val == exp_val


def test_parse_metric_text_malformed_strings():
    malformed = [
        "N/A",
        "Invalid String",
        "10 Yrs: 21%",
        "Years: 21%",
        "10 Years: ",
    ]
    for text in malformed:
        period, val, err = parse_metric_text(text)
        assert err is not None
        assert period is None
        assert val is None


def test_parse_metric_text_empty_values():
    empty_inputs = [None, "", "   ", float("nan")]
    for val in empty_inputs:
        period, parsed_val, err = parse_metric_text(val)
        assert err is not None
        assert period is None
        assert parsed_val is None


def test_cagr_divergence_low(tmp_path):
    db_file = str(tmp_path / "test.db")
    conn = sqlite3.connect(db_file)
    cur = conn.cursor()
    cur.execute("CREATE TABLE profitandloss (company_id TEXT, year INT, sales REAL)")
    cur.execute("INSERT INTO profitandloss VALUES ('TCS', 2019, 100.0)")
    cur.execute("INSERT INTO profitandloss VALUES ('TCS', 2024, 200.0)")  # CAGR ~14.87%
    conn.commit()

    res = validate_cagr_against_db(
        company_id="TCS",
        metric_type="compounded_sales_growth",
        period_years=5,
        parsed_value=15.0,  # Divergence ~0.13% <= 5%
        conn=conn,
    )
    conn.close()

    assert res["review_flag"] == "VALIDATED"
    assert res["divergence_pct"] <= 5.0


def test_cagr_divergence_high(tmp_path):
    db_file = str(tmp_path / "test.db")
    conn = sqlite3.connect(db_file)
    cur = conn.cursor()
    cur.execute("CREATE TABLE profitandloss (company_id TEXT, year INT, sales REAL)")
    cur.execute("INSERT INTO profitandloss VALUES ('TCS', 2019, 100.0)")
    cur.execute("INSERT INTO profitandloss VALUES ('TCS', 2024, 200.0)")  # CAGR ~14.87%
    conn.commit()

    res = validate_cagr_against_db(
        company_id="TCS",
        metric_type="compounded_sales_growth",
        period_years=5,
        parsed_value=30.0,  # Divergence ~15.13% > 5%
        conn=conn,
    )
    conn.close()

    assert res["review_flag"] == "DIVERGENCE_HIGH"
    assert res["divergence_pct"] > 5.0
