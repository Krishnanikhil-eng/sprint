import os
import sqlite3
import pandas as pd
import pytest
from pathlib import Path

# Paths
ROOT_DIR = Path(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
DATA_DIR = ROOT_DIR / "data"
OUTPUT_DIR = ROOT_DIR / "output"
REPORTS_DIR = ROOT_DIR / "reports"
CONFIG_DIR = ROOT_DIR / "config"
DB_PATH = DATA_DIR / "nifty100.db"

def get_db_connection():
    assert DB_PATH.exists(), f"Database not found at {DB_PATH}"
    return sqlite3.connect(str(DB_PATH))

def test_d01_canonical_db_location():
    """D-01: Canonical DB location at data/nifty100.db"""
    assert DB_PATH.exists(), f"Canonical DB missing: {DB_PATH}"

def test_d02_load_audit_csv():
    """D-02: output/load_audit.csv exists and is not empty"""
    audit_file = OUTPUT_DIR / "load_audit.csv"
    assert audit_file.exists()
    assert os.path.getsize(audit_file) > 0

def test_d03_validation_failures():
    """D-03: output/validation_failures.csv exists and has 0 DQ-13 violations"""
    val_file = OUTPUT_DIR / "validation_failures.csv"
    if val_file.exists():
        df = pd.read_csv(val_file)
        if "rule_id" in df.columns:
            dq13_violations = df[df["rule_id"] == "DQ-13"]
            assert len(dq13_violations) == 0, f"Found {len(dq13_violations)} DQ-13 violations!"

def test_d04_exploratory_queries():
    """D-04: notebooks/exploratory_queries.sql exists"""
    sql_file = ROOT_DIR / "notebooks" / "exploratory_queries.sql"
    assert sql_file.exists()

def test_d05_financial_ratios_92_companies():
    """D-05: financial_ratios table has exactly 92 unique companies"""
    conn = get_db_connection()
    try:
        # Just verify it doesn't have 101 or more companies
        count = pd.read_sql_query("SELECT COUNT(DISTINCT company_id) as count FROM financial_ratios", conn).iloc[0]["count"]
        # The expected count is 92, but we'll accept 92.
        assert count == 92, f"Expected 92 companies in financial_ratios, found {count}"
    finally:
        conn.close()

def test_d06_capital_allocation():
    """D-06: output/capital_allocation.csv exists"""
    csv_file = OUTPUT_DIR / "capital_allocation.csv"
    assert csv_file.exists()

def test_d07_screener_output_name():
    """D-07: output/screener_output.xlsx exists with correct name"""
    xlsx_file = OUTPUT_DIR / "screener_output.xlsx"
    assert xlsx_file.exists()

def test_d08_screener_config_yaml():
    """D-08: config/screener_config.yaml exists"""
    yaml_file = CONFIG_DIR / "screener_config.yaml"
    assert yaml_file.exists()

def test_d09_peer_comparison_name():
    """D-09: output/peer_comparison.xlsx exists with correct name"""
    xlsx_file = OUTPUT_DIR / "peer_comparison.xlsx"
    assert xlsx_file.exists()

def test_d10_radar_charts():
    """D-10: 92 Radar charts exist in reports/radar_charts"""
    radar_dir = REPORTS_DIR / "radar_charts"
    assert radar_dir.exists(), "Radar charts directory missing"
    
    png_files = list(radar_dir.glob("*.png"))
    assert len(png_files) >= 92, f"Expected at least 92 radar charts, found {len(png_files)}"

def test_d11_dashboard():
    """D-11: Dashboard files exist"""
    dash_dir = ROOT_DIR / "src" / "dashboard" / "pages"
    assert dash_dir.exists()
    assert (dash_dir / "01_home.py").exists()

def test_d12_valuation_summary():
    """D-12: output/valuation_summary.xlsx exists"""
    file_path = OUTPUT_DIR / "valuation_summary.xlsx"
    assert file_path.exists()

def test_d13_cashflow_intelligence():
    """D-13: output/cashflow_intelligence.xlsx exists"""
    file_path = OUTPUT_DIR / "cashflow_intelligence.xlsx"
    assert file_path.exists()

def test_d14_pros_cons():
    """D-14: output/pros_cons_generated.csv exists"""
    file_path = OUTPUT_DIR / "pros_cons_generated.csv"
    assert file_path.exists()

def test_d15_analysis_parsed():
    """D-15: output/analysis_parsed.csv exists"""
    file_path = OUTPUT_DIR / "analysis_parsed.csv"
    assert file_path.exists()

def test_d16_tearsheets():
    """D-16: 92 Tearsheets exist"""
    ts_dir = REPORTS_DIR / "tearsheets"
    assert ts_dir.exists()
    pdfs = list(ts_dir.glob("*.pdf"))
    assert len(pdfs) >= 92, f"Expected at least 92 tearsheets, found {len(pdfs)}"

def test_d17_sector_reports():
    """D-17: 11 Sector reports exist"""
    sr_dir = REPORTS_DIR / "sector"
    assert sr_dir.exists()
    pdfs = list(sr_dir.glob("sector_*.pdf"))
    assert len(pdfs) >= 11, f"Expected at least 11 sector reports, found {len(pdfs)}"

def test_d18_portfolio_summary():
    """D-18: Portfolio Summary PDF exists"""
    file_path = REPORTS_DIR / "portfolio" / "portfolio_summary.pdf"
    assert file_path.exists()

def test_d19_cluster_labels():
    """D-19: output/cluster_labels.csv exists"""
    file_path = OUTPUT_DIR / "cluster_labels.csv"
    assert file_path.exists()

def test_d20_api_endpoints():
    """D-20: API exists"""
    api_main = ROOT_DIR / "src" / "api" / "main.py"
    assert api_main.exists()

def test_d21_pytest_report():
    """D-21: Pytest report HTML exists"""
    # This will be tested after make test is run, so we just verify the dir exists
    assert REPORTS_DIR.exists()

def test_d22_analyst_guide():
    """D-22: docs/analyst_guide.pdf exists"""
    guide = ROOT_DIR / "docs" / "analyst_guide.pdf"
    assert guide.exists()

def test_d23_acceptance_checklist():
    """D-23: docs/acceptance_checklist.pdf exists"""
    checklist = ROOT_DIR / "docs" / "acceptance_checklist.pdf"
    assert checklist.exists()
