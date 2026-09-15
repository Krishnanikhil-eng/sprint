"""
Unit tests for Day 33 Two-Page Company Tearsheet PDF Generator.
Programmatically verifies PDF page counts, file sizes, text wrapping, and edge cases.
"""

import os
import re
import pytest
import sqlite3
import pandas as pd

from src.reports.tearsheet import TearsheetGenerator, run_batch_test_tearsheets


def get_pdf_page_count(filepath: str) -> int:
    """Helper to count pages in raw PDF file using regex."""
    with open(filepath, 'rb') as f:
        content = f.read()
    pages = re.findall(rb'/Type\s*/Page\b', content)
    return len(pages)


def test_generate_5_test_tearsheets(tmp_path):
    output_dir = str(tmp_path / "test_tearsheets")
    files = run_batch_test_tearsheets(db_path="nifty100.db", output_dir=output_dir)

    assert len(files) == 5
    for pdf_path in files:
        assert os.path.exists(pdf_path)
        size_bytes = os.path.getsize(pdf_path)
        # Check non-zero and reasonable file size >= 30 KB
        assert size_bytes >= 30 * 1024, f"File {pdf_path} size is too small: {size_bytes} bytes"

        # Check page count is strictly 2 pages
        page_count = get_pdf_page_count(pdf_path)
        assert page_count == 2, f"PDF {pdf_path} has {page_count} pages, expected exactly 2"


def test_tearsheet_layout_edge_cases(tmp_path):
    db_file = str(tmp_path / "edge_case.db")
    output_dir = str(tmp_path / "edge_output")
    conn = sqlite3.connect(db_file)
    cur = conn.cursor()

    cur.execute("""CREATE TABLE companies (company_id TEXT PRIMARY KEY, company_name TEXT);""")
    cur.execute("""CREATE TABLE sectors (company_id TEXT, broad_sector TEXT, sub_sector TEXT);""")
    cur.execute("""CREATE TABLE profitandloss (company_id TEXT, year INT, sales REAL, net_profit REAL, opm_percentage REAL, eps REAL, dividend_payout REAL, operating_profit REAL, other_income REAL);""")
    cur.execute("""CREATE TABLE balancesheet (company_id TEXT, year INT, equity_capital REAL, reserves REAL, borrowings REAL, total_liabilities REAL);""")
    cur.execute("""CREATE TABLE cashflow (company_id TEXT, year INT, operating_activity REAL, investing_activity REAL, financing_activity REAL, net_cash_flow REAL);""")
    cur.execute("""CREATE TABLE financial_ratios (company_id TEXT, year INT, return_on_equity_pct REAL, roce_pct REAL, debt_to_equity REAL, interest_coverage REAL, revenue_cagr_5yr REAL, pat_cagr_5yr REAL, cfo_quality_label TEXT, free_cash_flow_cr REAL, capital_allocation_pattern TEXT);""")
    cur.execute("""CREATE TABLE market_cap (company_id TEXT, year INT, market_cap_crore REAL, pe_ratio REAL);""")
    cur.execute("""CREATE TABLE prosandcons (company_id TEXT, pros TEXT, cons TEXT);""")

    # Extremely long company name, long pros and cons
    long_name = "Super Ultra Extremely Long International Conglomerate Corporation Limited India Private Public Enterprises Holding"
    long_pro = "Consistently high return on equity above 20% demonstrates exceptional capital efficiency over multi-decade cycles; Strong free cash flow generation over 5 years signals healthy business fundamentals and disciplined capital management; Debt-free balance sheet provides financial flexibility and eliminates interest burden entirely"
    long_con = "Rising debt-to-equity ratio over 3 years suggests increasing financial leverage risk in volatile economic environment; Earnings per share declining for 3 consecutive years reflects deteriorating profitability and severe competitive intensity"

    cur.execute("INSERT INTO companies VALUES ('LONG_CO', ?);", (long_name,))
    cur.execute("INSERT INTO sectors VALUES ('LONG_CO', 'Conglomerates & Diversified Industrial Capital Goods', 'Heavy Industrial Machinery');")
    cur.execute("INSERT INTO profitandloss VALUES ('LONG_CO', 2024, 150000.0, 25000.0, 22.0, 150.0, 30.0, 33000.0, 2000.0);")
    cur.execute("INSERT INTO balancesheet VALUES ('LONG_CO', 2024, 5000.0, 95000.0, 10000.0, 120000.0);")
    cur.execute("INSERT INTO cashflow VALUES ('LONG_CO', 2024, 30000.0, -15000.0, -10000.0, 5000.0);")
    cur.execute("INSERT INTO financial_ratios VALUES ('LONG_CO', 2024, 25.0, 22.0, 0.10, 15.0, 18.0, 22.0, 'High Quality', 15000.0, 'Reinvestor');")
    cur.execute("INSERT INTO market_cap VALUES ('LONG_CO', 2024, 500000.0, 20.0);")
    cur.execute("INSERT INTO prosandcons VALUES ('LONG_CO', ?, ?);", (long_pro, long_con))

    conn.commit()
    conn.close()

    gen = TearsheetGenerator(db_path=db_file, output_dir=output_dir)
    out_pdf = gen.build_pdf("LONG_CO")
    gen.close()

    assert os.path.exists(out_pdf)
    assert get_pdf_page_count(out_pdf) == 2
