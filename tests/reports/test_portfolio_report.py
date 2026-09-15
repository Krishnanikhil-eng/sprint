"""
Unit tests for Day 35 Portfolio Summary PDF Report Generator.
"""

import os
import re
import pytest
import sqlite3
import pandas as pd

from src.reports.portfolio_report import (
    compute_trend_arrow,
    PortfolioReportGenerator,
    run_portfolio_report
)


def get_pdf_page_count(filepath: str) -> int:
    """Helper to count pages in raw PDF."""
    with open(filepath, 'rb') as f:
        content = f.read()
    pages = re.findall(rb'/Type\s*/Page\b', content)
    return len(pages)


def test_trend_arrow_calculations():
    # Standard metrics (higher is better)
    assert compute_trend_arrow(100.0, 80.0) == "↑" # Improved
    assert compute_trend_arrow(80.0, 100.0) == "↓" # Declined
    assert compute_trend_arrow(100.0, 101.0) == "→" # Flat within 2%

    # Inverse metrics (lower is better, e.g. Debt/Equity)
    assert compute_trend_arrow(0.5, 0.8, lower_is_better=True) == "↑" # Improved (lower debt)
    assert compute_trend_arrow(0.8, 0.5, lower_is_better=True) == "↓" # Declined (higher debt)
    assert compute_trend_arrow(0.50, 0.51, lower_is_better=True) == "→" # Flat within 2%

    # Missing values
    assert compute_trend_arrow(None, 10.0) == "→"
    assert compute_trend_arrow(10.0, None) == "→"


def test_portfolio_report_generation(tmp_path):
    db_file = str(tmp_path / "port.db")
    output_pdf = str(tmp_path / "portfolio_summary.pdf")

    conn = sqlite3.connect(db_file)
    cur = conn.cursor()
    cur.execute("CREATE TABLE companies (company_id TEXT PRIMARY KEY, company_name TEXT);")
    cur.execute("CREATE TABLE sectors (company_id TEXT, broad_sector TEXT, sub_sector TEXT);")
    cur.execute("CREATE TABLE profitandloss (company_id TEXT, year INT, sales REAL, net_profit REAL, opm_percentage REAL);")
    cur.execute("CREATE TABLE financial_ratios (company_id TEXT, year INT, return_on_equity_pct REAL, roce_pct REAL, debt_to_equity REAL, interest_coverage REAL, operating_profit_margin_pct REAL, free_cash_flow_cr REAL, cfo_quality_label TEXT, capital_allocation_pattern TEXT);")
    cur.execute("CREATE TABLE market_cap (company_id TEXT, year INT, market_cap_crore REAL, pe_ratio REAL);")
    cur.execute("CREATE TABLE prosandcons (company_id TEXT, pros TEXT, cons TEXT);")

    # 3 Companies in non-alphabetical insert order: TCS, AAC, M&M
    for cid in ["TCS", "AAC", "MM"]:
        cur.execute("INSERT INTO companies VALUES (?, ?);", (cid, f"{cid} Ltd"))
        cur.execute("INSERT INTO sectors VALUES (?, 'Tech', 'Software');", (cid,))
        for y in [2023, 2024]:
            cur.execute("INSERT INTO profitandloss VALUES (?, ?, 1000.0, 200.0, 20.0);", (cid, y))
            cur.execute("INSERT INTO financial_ratios VALUES (?, ?, 20.0, 18.0, 0.1, 15.0, 20.0, 100.0, 'High Quality', 'Reinvestor');", (cid, y))
            cur.execute("INSERT INTO market_cap VALUES (?, ?, 10000.0, 25.0);", (cid, y))
            cur.execute("INSERT INTO prosandcons VALUES (?, 'Good ROE', 'High P/E');", (cid,))

    conn.commit()
    conn.close()

    out_file = run_portfolio_report(db_path=db_file, output_pdf=output_pdf)

    assert os.path.exists(out_file)
    assert os.path.getsize(out_file) > 1000
    # Page count should equal company count (3)
    assert get_pdf_page_count(out_file) == 3
