"""
Unit tests for Day 34 Batch Tearsheets & Sector Reports.
"""

import os
import sqlite3

from src.reports.batch_generator import run_batch_tearsheet_generation, count_pdf_pages
from src.reports.sector_report import SectorReportGenerator


def test_batch_tearsheet_generation_and_skipped(tmp_path):
    db_file = str(tmp_path / "batch.db")
    output_dir = str(tmp_path / "tearsheets")
    skipped_csv = str(tmp_path / "skipped.csv")

    conn = sqlite3.connect(db_file)
    cur = conn.cursor()
    cur.execute(
        "CREATE TABLE companies (company_id TEXT PRIMARY KEY, company_name TEXT);"
    )
    cur.execute(
        "CREATE TABLE sectors (company_id TEXT, broad_sector TEXT, sub_sector TEXT);"
    )
    cur.execute(
        "CREATE TABLE profitandloss (company_id TEXT, year INT, sales REAL, net_profit REAL, opm_percentage REAL, eps REAL, dividend_payout REAL, operating_profit REAL, other_income REAL);"
    )
    cur.execute(
        "CREATE TABLE balancesheet (company_id TEXT, year INT, equity_capital REAL, reserves REAL, borrowings REAL, total_liabilities REAL);"
    )
    cur.execute(
        "CREATE TABLE cashflow (company_id TEXT, year INT, operating_activity REAL, investing_activity REAL, financing_activity REAL, net_cash_flow REAL);"
    )
    cur.execute(
        "CREATE TABLE financial_ratios (company_id TEXT, year INT, return_on_equity_pct REAL, roce_pct REAL, debt_to_equity REAL, interest_coverage REAL, revenue_cagr_5yr REAL, pat_cagr_5yr REAL, cfo_quality_label TEXT, free_cash_flow_cr REAL, capital_allocation_pattern TEXT);"
    )
    cur.execute(
        "CREATE TABLE market_cap (company_id TEXT, year INT, market_cap_crore REAL, pe_ratio REAL);"
    )
    cur.execute("CREATE TABLE prosandcons (company_id TEXT, pros TEXT, cons TEXT);")

    # Company 1: FULL_CO with 5 years
    cur.execute("INSERT INTO companies VALUES ('FULL_CO', 'Full Co Ltd');")
    cur.execute("INSERT INTO sectors VALUES ('FULL_CO', 'Technology', 'Software');")
    for y in [2020, 2021, 2022, 2023, 2024]:
        cur.execute(
            "INSERT INTO profitandloss VALUES ('FULL_CO', ?, 1000.0, 200.0, 20.0, 10.0, 25.0, 250.0, 10.0);",
            (y,),
        )
        cur.execute(
            "INSERT INTO balancesheet VALUES ('FULL_CO', ?, 100.0, 900.0, 50.0, 1100.0);",
            (y,),
        )
        cur.execute(
            "INSERT INTO cashflow VALUES ('FULL_CO', ?, 220.0, -100.0, -50.0, 70.0);",
            (y,),
        )
        cur.execute(
            "INSERT INTO financial_ratios VALUES ('FULL_CO', ?, 20.0, 18.0, 0.05, 20.0, 15.0, 18.0, 'High Quality', 120.0, 'Reinvestor');",
            (y,),
        )
        cur.execute("INSERT INTO market_cap VALUES ('FULL_CO', ?, 5000.0, 25.0);", (y,))

    # Company 2: SHORT_CO with 2 years (Should be skipped)
    cur.execute("INSERT INTO companies VALUES ('SHORT_CO', 'Short Co Ltd');")
    cur.execute("INSERT INTO sectors VALUES ('SHORT_CO', 'Technology', 'Hardware');")
    for y in [2023, 2024]:
        cur.execute(
            "INSERT INTO profitandloss VALUES ('SHORT_CO', ?, 100.0, 10.0, 10.0, 1.0, 0.0, 15.0, 0.0);",
            (y,),
        )

    conn.commit()
    conn.close()

    generated_files, skipped_records = run_batch_tearsheet_generation(
        db_path=db_file, output_dir=output_dir, skipped_csv=skipped_csv
    )

    assert len(generated_files) == 1
    assert os.path.exists(generated_files[0])
    assert count_pdf_pages(generated_files[0]) == 2

    assert len(skipped_records) == 1
    assert skipped_records[0]["company_id"] == "SHORT_CO"
    assert "insufficient" in skipped_records[0]["reason"].lower()


def test_sector_report_generation(tmp_path):
    db_file = str(tmp_path / "sector.db")
    output_dir = str(tmp_path / "sector_reports")
    conn = sqlite3.connect(db_file)
    cur = conn.cursor()
    cur.execute(
        "CREATE TABLE companies (company_id TEXT PRIMARY KEY, company_name TEXT);"
    )
    cur.execute(
        "CREATE TABLE sectors (company_id TEXT, broad_sector TEXT, sub_sector TEXT);"
    )
    cur.execute(
        "CREATE TABLE profitandloss (company_id TEXT, year INT, sales REAL, net_profit REAL, opm_percentage REAL);"
    )
    cur.execute(
        "CREATE TABLE financial_ratios (company_id TEXT, year INT, return_on_equity_pct REAL, roce_pct REAL, debt_to_equity REAL, interest_coverage REAL, operating_profit_margin_pct REAL, free_cash_flow_cr REAL);"
    )

    cur.execute("INSERT INTO companies VALUES ('SEC_CO1', 'Sector Co One');")
    cur.execute("INSERT INTO sectors VALUES ('SEC_CO1', 'Healthcare', 'Pharma');")
    cur.execute(
        "INSERT INTO profitandloss VALUES ('SEC_CO1', 2024, 500.0, 100.0, 20.0);"
    )
    cur.execute(
        "INSERT INTO financial_ratios VALUES ('SEC_CO1', 2024, 20.0, 18.0, 0.1, 15.0, 20.0, 80.0);"
    )

    conn.commit()
    conn.close()

    sec_gen = SectorReportGenerator(db_path=db_file, output_dir=output_dir)
    out_file = sec_gen.build_sector_report("Healthcare")
    sec_gen.close()

    assert os.path.exists(out_file)
    assert os.path.getsize(out_file) > 10 * 1024
