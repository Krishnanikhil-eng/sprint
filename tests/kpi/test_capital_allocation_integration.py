"""
Unit tests for Day 32 Capital Allocation Report & Integration.
"""

import sqlite3
import pandas as pd

from src.analytics.capital_allocation_reporter import (
    process_capital_allocation_report,
    VALID_8_PATTERNS,
)


def test_capital_allocation_completeness_and_distribution(tmp_path):
    db_file = str(tmp_path / "test_cap_alloc.db")
    cap_csv = str(tmp_path / "capital_allocation.csv")
    dist_csv = str(tmp_path / "dist.csv")
    changes_csv = str(tmp_path / "changes.csv")

    conn = sqlite3.connect(db_file)
    cur = conn.cursor()
    cur.execute("CREATE TABLE companies (company_id TEXT PRIMARY KEY);")
    cur.execute("INSERT INTO companies VALUES ('COMP_A');")
    cur.execute("INSERT INTO companies VALUES ('COMP_B');")
    conn.commit()
    conn.close()

    # Create dummy capital_allocation.csv
    df_cap_dummy = pd.DataFrame(
        [
            {
                "company_id": "COMP_A",
                "year": 2023,
                "cfo_sign": "+",
                "cfi_sign": "-",
                "cff_sign": "-",
                "pattern_label": "Reinvestor",
            },
            {
                "company_id": "COMP_A",
                "year": 2024,
                "cfo_sign": "-",
                "cfi_sign": "+",
                "cff_sign": "+",
                "pattern_label": "Distress Signal",
            },
            {
                "company_id": "COMP_B",
                "year": 2023,
                "cfo_sign": "+",
                "cfi_sign": "-",
                "cff_sign": "-",
                "pattern_label": "Shareholder Returns",
            },
            {
                "company_id": "COMP_B",
                "year": 2024,
                "cfo_sign": "+",
                "cfi_sign": "-",
                "cff_sign": "-",
                "pattern_label": "Shareholder Returns",
            },
        ]
    )
    df_cap_dummy.to_csv(cap_csv, index=False)

    df_cap, df_dist, df_changes = process_capital_allocation_report(
        db_path=db_file,
        cap_alloc_csv=cap_csv,
        dist_csv=dist_csv,
        changes_csv=changes_csv,
    )

    # Verify distribution
    assert len(df_dist) == len(VALID_8_PATTERNS)
    assert set(df_dist["pattern"]) == VALID_8_PATTERNS
    assert df_dist["company_count"].sum() == 2

    # Verify pattern changes (COMP_A changed Reinvestor -> Distress Signal)
    assert len(df_changes) == 1
    ch_row = df_changes.iloc[0]
    assert ch_row["company_id"] == "COMP_A"
    assert ch_row["previous_pattern"] == "Reinvestor"
    assert ch_row["latest_pattern"] == "Distress Signal"
    assert ch_row["change_flag"] == True
