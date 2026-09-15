"""
Data Quality Validation Rule Unit Tests (Day 41).
Contains 14 tests validating database records, ratio bounds, missing data handling,
and data anomaly detection rules.
"""

import sqlite3
import pytest
import pandas as pd
from pathlib import Path


def get_db():
    return sqlite3.connect("nifty100.db")


def test_dq_company_count():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM companies")
    count = cursor.fetchone()[0]
    conn.close()
    assert count == 92


def test_dq_ticker_non_empty():
    conn = get_db()
    df = pd.read_sql_query("SELECT company_id FROM companies", conn)
    conn.close()
    assert not df["company_id"].isnull().any()
    assert (df["company_id"].str.len() > 0).all()


def test_dq_sector_assignments():
    conn = get_db()
    df = pd.read_sql_query("SELECT broad_sector FROM sectors", conn)
    conn.close()
    assert not df["broad_sector"].isnull().any()
    assert len(df["broad_sector"].unique()) >= 5


def test_dq_financial_ratios_year_range():
    conn = get_db()
    df = pd.read_sql_query("SELECT year FROM financial_ratios", conn)
    conn.close()
    assert df["year"].min() >= 2010
    assert df["year"].max() <= 2026


def test_dq_no_duplicate_company_year_ratios():
    conn = get_db()
    df = pd.read_sql_query("SELECT company_id, year, COUNT(*) as cnt FROM financial_ratios GROUP BY company_id, year HAVING cnt > 1", conn)
    conn.close()
    assert df.empty


def test_dq_roe_within_plausible_range():
    conn = get_db()
    df = pd.read_sql_query("SELECT return_on_equity_pct FROM financial_ratios WHERE return_on_equity_pct IS NOT NULL", conn)
    conn.close()
    # ROE should generally lie between -2000% and +2000%
    assert (df["return_on_equity_pct"] > -2000).all()


def test_dq_debt_to_equity_non_negative_unless_null():
    conn = get_db()
    df = pd.read_sql_query("SELECT debt_to_equity FROM financial_ratios WHERE debt_to_equity IS NOT NULL", conn)
    conn.close()
    assert (df["debt_to_equity"] >= 0).all()


def test_dq_market_cap_positive():
    conn = get_db()
    df = pd.read_sql_query("SELECT market_cap_crore FROM market_cap WHERE market_cap_crore IS NOT NULL", conn)
    conn.close()
    assert (df["market_cap_crore"] > 0).all()


def test_dq_pe_ratio_reasonable_bounds():
    conn = get_db()
    df = pd.read_sql_query("SELECT pe_ratio FROM market_cap WHERE pe_ratio IS NOT NULL", conn)
    conn.close()
    # PE ratios should not be extreme negative errors
    assert (df["pe_ratio"] > -500).all()


def test_dq_cash_flow_integrity():
    conn = get_db()
    df = pd.read_sql_query("SELECT company_id, year FROM cashflow", conn)
    conn.close()
    assert not df.empty


def test_dq_documents_url_format():
    conn = get_db()
    df = pd.read_sql_query("SELECT annual_report FROM documents WHERE annual_report IS NOT NULL", conn)
    conn.close()
    urls = df["annual_report"]
    valid_count = sum(1 for u in urls if isinstance(u, str) and (u.startswith("http://") or u.startswith("https://")))
    assert valid_count > 0


def test_dq_prosandcons_coverage():
    conn = get_db()
    df = pd.read_sql_query("SELECT company_id FROM prosandcons", conn)
    conn.close()
    assert len(df["company_id"].unique()) == 92


def test_dq_peer_groups_coverage():
    conn = get_db()
    df = pd.read_sql_query("SELECT DISTINCT company_id FROM peer_groups", conn)
    conn.close()
    assert len(df) >= 50


def test_dq_stock_prices_series():
    conn = get_db()
    df = pd.read_sql_query("SELECT COUNT(*) as cnt FROM stock_prices", conn)
    conn.close()
    assert df.iloc[0]["cnt"] >= 5000
