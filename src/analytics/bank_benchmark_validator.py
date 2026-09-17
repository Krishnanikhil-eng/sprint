"""
Bank Sector Carve-Out Benchmark Validator Module.
Verifies that bank and financial sector entities follow special ratio rules:
1. ROCE is explicitly set to None (suppressed for banks/NBFCs)
2. High Leverage Flag (> 5.0 D/E) is suppressed for financial institutions
3. Non-financial entities correctly trigger High Leverage Flag when D/E > 5.0
"""

import sqlite3
import pandas as pd
from typing import Dict, Any


def validate_bank_carveout_rules(db_path: str = "data/nifty100.db") -> Dict[str, Any]:
    conn = sqlite3.connect(db_path)

    ratios = pd.read_sql_query("SELECT * FROM financial_ratios", conn)
    sec = pd.read_sql_query("SELECT * FROM sectors", conn)
    conn.close()

    fin_companies = set()
    if "broad_sector" in sec.columns:
        fin_companies = set(
            sec[
                sec["broad_sector"].str.contains(
                    "Financial|Bank|Finance|Insurance", case=False, na=False
                )
            ]["company_id"]
        )

    fin_ratios = ratios[ratios["company_id"].isin(fin_companies)]
    non_fin_ratios = ratios[~ratios["company_id"].isin(fin_companies)]

    # Rule 1: ROCE for Financials must be 100% None
    fin_roce_non_null = fin_ratios["roce_pct"].notnull().sum()

    # Rule 2: High Leverage Flag suppressed for Financials (should be 0 everywhere for Financials)
    fin_high_lev_active = (fin_ratios["high_leverage_flag"] == 1).sum()

    # Rule 3: Non-Financials with D/E > 5.0 must have high_leverage_flag = 1
    non_fin_over_5 = non_fin_ratios[non_fin_ratios["debt_to_equity"] > 5.0]
    non_fin_flagged = (non_fin_over_5["high_leverage_flag"] == 1).sum()
    non_fin_total_over_5 = len(non_fin_over_5)

    passed = bool(
        (fin_roce_non_null == 0)
        and (fin_high_lev_active == 0)
        and (non_fin_flagged == non_fin_total_over_5)
    )

    print(
        "==================================================================================="
    )
    print(
        "               BANK SECTOR CARVE-OUT & BENCHMARK AUDIT                            "
    )
    print(
        "==================================================================================="
    )
    print(f"Financial companies count                      : {len(fin_companies)}")
    print(
        f"Financial ROCE non-null count (Expected: 0)     : {fin_roce_non_null} ({'PASS' if fin_roce_non_null==0 else 'FAIL'})"
    )
    print(
        f"Financial High Leverage flag count (Expected: 0): {fin_high_lev_active} ({'PASS' if fin_high_lev_active==0 else 'FAIL'})"
    )
    print(
        f"Non-Financial D/E > 5.0 correctly flagged       : {non_fin_flagged}/{non_fin_total_over_5} ({'PASS' if non_fin_flagged==non_fin_total_over_5 else 'FAIL'})"
    )
    print(f"OVERALL CARVE-OUT AUDIT PASSED                 : {passed}")
    print(
        "==================================================================================="
    )

    return {
        "financial_companies_count": len(fin_companies),
        "fin_roce_non_null_count": int(fin_roce_non_null),
        "fin_high_leverage_active_count": int(fin_high_lev_active),
        "non_fin_flagged_count": int(non_fin_flagged),
        "passed": bool(passed),
    }


if __name__ == "__main__":
    validate_bank_carveout_rules()
