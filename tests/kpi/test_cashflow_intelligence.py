"""
Unit tests for Day 31 Cash Flow Intelligence module.
"""

import pytest
import sqlite3
import pandas as pd
from typing import List

from src.analytics.cashflow_kpis import (
    calculate_free_cash_flow,
    calculate_cfo_quality_score,
    calculate_capex_intensity,
    calculate_fcf_conversion,
    classify_capital_allocation,
    run_cashflow_intelligence,
)


def test_cfo_quality_score_labels():
    # High Quality > 1.0
    score, label = calculate_cfo_quality_score([120.0, 150.0], [100.0, 100.0])
    assert score == 1.35
    assert label == "High Quality"

    # Moderate 0.5 - 1.0
    score, label = calculate_cfo_quality_score([70.0, 80.0], [100.0, 100.0])
    assert score == 0.75
    assert label == "Moderate"

    # Accrual Risk < 0.5
    score, label = calculate_cfo_quality_score([20.0, 40.0], [100.0, 100.0])
    assert score == 0.30
    assert label == "Accrual Risk"


def test_capex_intensity_labels():
    # Asset Light < 3%
    intensity, label = calculate_capex_intensity(-20.0, 1000.0)
    assert intensity == 2.0
    assert label == "Asset Light"

    # Moderate 3-8%
    intensity, label = calculate_capex_intensity(-50.0, 1000.0)
    assert intensity == 5.0
    assert label == "Moderate"

    # Capital Intensive > 8%
    intensity, label = calculate_capex_intensity(-100.0, 1000.0)
    assert intensity == 10.0
    assert label == "Capital Intensive"


def test_fcf_conversion():
    # Normal
    assert calculate_fcf_conversion(50.0, 100.0) == 50.0
    # Zero operating profit
    assert calculate_fcf_conversion(50.0, 0.0) is None
    # None
    assert calculate_fcf_conversion(None, 100.0) is None


def test_distress_and_deleveraging_logic(tmp_path):
    db_file = str(tmp_path / "test_cf.db")
    excel_file = str(tmp_path / "cashflow_intelligence.xlsx")
    alerts_file = str(tmp_path / "distress_alerts.csv")

    conn = sqlite3.connect(db_file)
    cur = conn.cursor()

    cur.execute("CREATE TABLE companies (company_id TEXT PRIMARY KEY);")
    cur.execute("CREATE TABLE sectors (company_id TEXT, broad_sector TEXT);")
    cur.execute("CREATE TABLE profitandloss (company_id TEXT, year INT, sales REAL, net_profit REAL, operating_profit REAL);")
    cur.execute("CREATE TABLE balancesheet (company_id TEXT, year INT, borrowings REAL);")
    cur.execute("CREATE TABLE cashflow (company_id TEXT, year INT, operating_activity REAL, investing_activity REAL, financing_activity REAL);")

    # DISTRESS_CO: CFO < 0 and CFF > 0 in 2024
    cur.execute("INSERT INTO companies VALUES ('DISTRESS_CO');")
    cur.execute("INSERT INTO sectors VALUES ('DISTRESS_CO', 'Textiles');")
    cur.execute("INSERT INTO profitandloss VALUES ('DISTRESS_CO', 2024, 100.0, -10.0, 15.0);")
    cur.execute("INSERT INTO balancesheet VALUES ('DISTRESS_CO', 2024, 50.0);")
    cur.execute("INSERT INTO cashflow VALUES ('DISTRESS_CO', 2024, -20.0, -5.0, 30.0);")

    # DELEVERAGED_CO: CFF < 0 and borrowings declining (2023: 100 -> 2024: 80)
    cur.execute("INSERT INTO companies VALUES ('DELEVERAGED_CO');")
    cur.execute("INSERT INTO sectors VALUES ('DELEVERAGED_CO', 'IT');")
    cur.execute("INSERT INTO profitandloss VALUES ('DELEVERAGED_CO', 2023, 500.0, 100.0, 150.0);")
    cur.execute("INSERT INTO profitandloss VALUES ('DELEVERAGED_CO', 2024, 600.0, 120.0, 180.0);")
    cur.execute("INSERT INTO balancesheet VALUES ('DELEVERAGED_CO', 2023, 100.0);")
    cur.execute("INSERT INTO balancesheet VALUES ('DELEVERAGED_CO', 2024, 80.0);")
    cur.execute("INSERT INTO cashflow VALUES ('DELEVERAGED_CO', 2023, 150.0, -50.0, -80.0);")
    cur.execute("INSERT INTO cashflow VALUES ('DELEVERAGED_CO', 2024, 160.0, -60.0, -90.0);")

    conn.commit()
    conn.close()

    df_res, df_distress = run_cashflow_intelligence(db_path=db_file, output_excel=excel_file, alerts_csv=alerts_file)

    assert len(df_res) == 2

    distress_row = df_res[df_res['company_id'] == 'DISTRESS_CO'].iloc[0]
    assert distress_row['distress_flag'] == True

    delev_row = df_res[df_res['company_id'] == 'DELEVERAGED_CO'].iloc[0]
    assert delev_row['deleveraging_flag'] == True

    assert len(df_distress) == 1
    assert df_distress.iloc[0]['company_id'] == 'DISTRESS_CO'
