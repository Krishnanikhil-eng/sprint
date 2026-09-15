"""
Capital Allocation Intelligence Integration & Reporter (Day 32).
Analyzes output/capital_allocation.csv, computes latest-year distribution,
tracks year-over-year pattern changes, and verifies integration with cashflow_intelligence.xlsx.
"""

import os
import sqlite3
import pandas as pd
import numpy as np
from typing import Tuple, Dict, List, Any

from src.analytics.capital_allocation_exporter import export_capital_allocation


VALID_8_PATTERNS = {
    "Shareholder Returns",
    "Reinvestor",
    "Liquidating Assets",
    "Distress Signal",
    "Growth Funded by Debt",
    "Cash Accumulator",
    "Pre-Revenue",
    "Mixed"
}


def process_capital_allocation_report(
    db_path: str = "nifty100.db",
    cap_alloc_csv: str = "output/capital_allocation.csv",
    dist_csv: str = "output/capital_allocation_distribution.csv",
    changes_csv: str = "output/pattern_changes.csv",
    cashflow_intel_excel: str = "output/cashflow_intelligence.xlsx"
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Processes capital allocation data, generates distribution CSV and pattern changes CSV.
    """
    # Ensure capital_allocation.csv exists and is up to date
    if not os.path.exists(cap_alloc_csv):
        export_capital_allocation(db_path=db_path, output_path=cap_alloc_csv)

    df_cap = pd.read_csv(cap_alloc_csv)
    conn = sqlite3.connect(db_path)
    df_comp = pd.read_sql_query("SELECT company_id FROM companies", conn)
    conn.close()

    valid_comp_ids = set(df_comp['company_id'].str.strip())
    
    # 1. Distribution for Latest Year per company
    latest_rows = df_cap.sort_values(['company_id', 'year']).groupby('company_id').last().reset_index()
    latest_rows = latest_rows[latest_rows['company_id'].isin(valid_comp_ids)]

    dist_counts = latest_rows['pattern_label'].value_counts()
    total_companies = len(latest_rows)

    dist_records = []
    for pattern in sorted(list(VALID_8_PATTERNS)):
        cnt = int(dist_counts.get(pattern, 0))
        pct = round((cnt / total_companies) * 100.0, 2) if total_companies > 0 else 0.0
        dist_records.append({
            "pattern": pattern,
            "company_count": cnt,
            "percentage": pct
        })

    df_dist = pd.DataFrame(dist_records)
    os.makedirs(os.path.dirname(dist_csv), exist_ok=True)
    df_dist.to_csv(dist_csv, index=False)

    # 2. Year-over-Year Pattern Changes (compare previous year vs latest year for each company)
    changes_records = []
    for cid, group in df_cap.groupby('company_id'):
        cid = str(cid).strip()
        if cid not in valid_comp_ids:
            continue

        group_sorted = group.sort_values('year')
        if len(group_sorted) >= 2:
            prev_row = group_sorted.iloc[-2]
            latest_row = group_sorted.iloc[-1]

            prev_yr = int(prev_row['year'])
            prev_pat = str(prev_row['pattern_label'])
            latest_yr = int(latest_row['year'])
            latest_pat = str(latest_row['pattern_label'])

            is_changed = (prev_pat != latest_pat)
            if is_changed:
                changes_records.append({
                    "company_id": cid,
                    "previous_year": prev_yr,
                    "previous_pattern": prev_pat,
                    "latest_year": latest_yr,
                    "latest_pattern": latest_pat,
                    "change_flag": True
                })

    df_changes = pd.DataFrame(changes_records, columns=[
        "company_id", "previous_year", "previous_pattern", "latest_year", "latest_pattern", "change_flag"
    ])
    df_changes.to_csv(changes_csv, index=False)

    # 3. Cashflow Intelligence Integration Verification
    if os.path.exists(cashflow_intel_excel):
        df_cf_intel = pd.read_excel(cashflow_intel_excel)
        # Verify alignment
        merged = pd.merge(df_cf_intel, latest_rows[['company_id', 'pattern_label']], on='company_id', how='inner')
        mismatches = merged[merged['capital_allocation_label'] != merged['pattern_label']]
        if not mismatches.empty:
            print(f"WARNING: Found {len(mismatches)} capital allocation label mismatches in cashflow_intelligence.xlsx!")

    print(f"=== Capital Allocation Report Summary ===")
    print(f"Evaluated Companies (Latest Year): {total_companies}")
    print(f"Pattern Distribution:\n{df_dist}")
    print(f"Total Companies with YoY Pattern Change: {len(df_changes)}")
    print(f"Saved Distribution -> {dist_csv}")
    print(f"Saved Pattern Changes -> {changes_csv}")

    return df_cap, df_dist, df_changes


if __name__ == "__main__":
    process_capital_allocation_report()
