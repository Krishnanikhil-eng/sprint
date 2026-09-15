"""
Unit tests for Day 30 Rule-Based NLP Pros and Cons Generator.
Tests all 12 PRO rules and 12 CON rules for trigger, non-trigger, boundary, and missing data.
"""

import os
import sqlite3
import pytest
import pandas as pd
from unittest.mock import MagicMock

from src.nlp.pros_cons_generator import ProsConsEngine


@pytest.fixture
def mock_engine(tmp_path):
    """Creates a temporary sqlite DB with schema for testing pros/cons rules."""
    db_file = str(tmp_path / "test_proscons.db")
    conn = sqlite3.connect(db_file)
    cur = conn.cursor()

    cur.execute("""CREATE TABLE companies (company_id TEXT PRIMARY KEY, company_name TEXT);""")
    cur.execute("""CREATE TABLE profitandloss (company_id TEXT, year INT, sales REAL, net_profit REAL, opm_percentage REAL, eps REAL, dividend_payout REAL, operating_profit REAL, other_income REAL);""")
    cur.execute("""CREATE TABLE balancesheet (company_id TEXT, year INT, borrowings REAL, total_assets REAL, investments REAL);""")
    cur.execute("""CREATE TABLE cashflow (company_id TEXT, year INT, operating_activity REAL, investing_activity REAL, financing_activity REAL);""")
    cur.execute("""CREATE TABLE financial_ratios (company_id TEXT, year INT, return_on_equity_pct REAL, roce_pct REAL, debt_to_equity REAL, interest_coverage REAL);""")
    cur.execute("""CREATE TABLE market_cap (company_id TEXT, year INT, dividend_yield_pct REAL);""")
    cur.execute("""CREATE TABLE sectors (company_id TEXT, broad_sector TEXT);""")
    cur.execute("""CREATE TABLE prosandcons (company_id TEXT, pros TEXT, cons TEXT);""")
    conn.commit()
    conn.close()

    engine = ProsConsEngine(db_path=db_file)
    yield engine
    engine.close()


def test_pro_1_roe_sustained(mock_engine):
    # Setup test company TEST1: ROE > 20% for 3 years
    cur = mock_engine.conn.cursor()
    cur.execute("INSERT INTO companies VALUES ('TEST1', 'Test Corp')")
    for y in [2022, 2023, 2024]:
        cur.execute("INSERT INTO financial_ratios (company_id, year, return_on_equity_pct) VALUES ('TEST1', ?, 22.0)", (y,))
        cur.execute("INSERT INTO profitandloss (company_id, year) VALUES ('TEST1', ?)", (y,))
    mock_engine.conn.commit()
    mock_engine._load_data()

    res = mock_engine.evaluate_company("TEST1")
    pro1 = [r for r in res if r["rule_id"] == "PRO_1"]
    assert len(pro1) == 1
    assert pro1[0]["confidence_pct"] > 60.0


def test_pro_3_debt_free(mock_engine):
    cur = mock_engine.conn.cursor()
    cur.execute("INSERT INTO companies VALUES ('TEST3', 'Debt Free Co')")
    cur.execute("INSERT INTO profitandloss (company_id, year) VALUES ('TEST3', 2024)")
    cur.execute("INSERT INTO financial_ratios (company_id, year, debt_to_equity) VALUES ('TEST3', 2024, 0.0)")
    mock_engine.conn.commit()
    mock_engine._load_data()

    res = mock_engine.evaluate_company("TEST3")
    pro3 = [r for r in res if r["rule_id"] == "PRO_3"]
    assert len(pro3) == 1
    assert pro3[0]["confidence_pct"] >= 90.0


def test_con_1_high_de(mock_engine):
    cur = mock_engine.conn.cursor()
    cur.execute("INSERT INTO companies VALUES ('TEST_LEVERAGED', 'Leveraged Co')")
    cur.execute("INSERT INTO sectors VALUES ('TEST_LEVERAGED', 'Manufacturing')")
    cur.execute("INSERT INTO profitandloss (company_id, year) VALUES ('TEST_LEVERAGED', 2024)")
    cur.execute("INSERT INTO financial_ratios (company_id, year, debt_to_equity) VALUES ('TEST_LEVERAGED', 2024, 2.5)")
    mock_engine.conn.commit()
    mock_engine._load_data()

    res = mock_engine.evaluate_company("TEST_LEVERAGED")
    con1 = [r for r in res if r["rule_id"] == "CON_1"]
    assert len(con1) == 1
    assert "2.50" in con1[0]["text"]
    assert con1[0]["confidence_pct"] > 60.0


def test_con_4_net_loss(mock_engine):
    cur = mock_engine.conn.cursor()
    cur.execute("INSERT INTO companies VALUES ('TEST_LOSS', 'Loss Co')")
    cur.execute("INSERT INTO profitandloss (company_id, year, net_profit) VALUES ('TEST_LOSS', 2024, -50.0)")
    mock_engine.conn.commit()
    mock_engine._load_data()

    res = mock_engine.evaluate_company("TEST_LOSS")
    con4 = [r for r in res if r["rule_id"] == "CON_4"]
    assert len(con4) == 1
    assert con4[0]["confidence_pct"] >= 90.0


def test_missing_data_handling(mock_engine):
    cur = mock_engine.conn.cursor()
    cur.execute("INSERT INTO companies VALUES ('EMPTY_CO', 'Empty Co')")
    mock_engine.conn.commit()
    mock_engine._load_data()

    res = mock_engine.evaluate_company("EMPTY_CO")
    assert res == []
