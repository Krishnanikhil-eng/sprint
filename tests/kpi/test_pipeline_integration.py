import os
import sqlite3
from src.analytics.pipeline import run_sprint2_pipeline


def test_sprint2_pipeline_integration(tmp_path):
    # Test pipeline execution on database
    summary = run_sprint2_pipeline("nifty100.db")

    assert summary["total_ratio_rows"] >= 1100
    assert os.path.exists(summary["capital_allocation_csv"])
    assert os.path.exists(summary["edge_case_log"])
    assert summary["spot_check_passed"] is True
    assert 15 <= summary["screener_matching_companies"] <= 50


def test_database_ratios_row_count():
    conn = sqlite3.connect("nifty100.db")
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM financial_ratios;")
    count = cursor.fetchone()[0]
    conn.close()
    assert count >= 1100
