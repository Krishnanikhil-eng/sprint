"""
Manual Spot-Check Validation Script.
Validates 3 representative companies (TCS, INFY, RELIANCE) for ROE and 5-Year Revenue CAGR
against raw statement values, confirming difference < 0.1%.
"""

import sqlite3
import pandas as pd


def run_manual_spot_checks(db_path: str = "data/nifty100.db") -> bool:
    conn = sqlite3.connect(db_path)

    pnl = pd.read_sql_query("SELECT * FROM profitandloss", conn)
    bs = pd.read_sql_query("SELECT * FROM balancesheet", conn)
    ratios = pd.read_sql_query("SELECT * FROM financial_ratios", conn)
    conn.close()

    sample_companies = ["TCS", "INFY", "RELIANCE"]
    target_year = 2024
    base_year = 2019
    n_years = 5

    all_passed = True
    print(
        "==================================================================================="
    )
    print(
        "               SPRINT 2 — 3-COMPANY MANUAL SPOT-CHECK VALIDATION                    "
    )
    print(
        "==================================================================================="
    )

    for cid in sample_companies:
        print(f"\n--- Company: {cid} ---")

        # 1. Manual ROE Check for 2024
        pnl_row = pnl[(pnl["company_id"] == cid) & (pnl["year"] == target_year)]
        bs_row = bs[(bs["company_id"] == cid) & (bs["year"] == target_year)]
        db_ratio_row = ratios[
            (ratios["company_id"] == cid) & (ratios["year"] == target_year)
        ]

        if not pnl_row.empty and not bs_row.empty and not db_ratio_row.empty:
            np_val = pnl_row.iloc[0]["net_profit"]
            eq_val = bs_row.iloc[0]["equity_capital"]
            res_val = bs_row.iloc[0]["reserves"]

            manual_roe = (np_val / (eq_val + res_val)) * 100.0
            db_roe = db_ratio_row.iloc[0]["return_on_equity_pct"]
            diff_roe = abs(manual_roe - db_roe)

            pass_roe = diff_roe < 0.1
            print(
                f"ROE (2024): Manual = {manual_roe:.4f}% | DB = {db_roe:.4f}% | Diff = {diff_roe:.4f}% | Result: {'PASS' if pass_roe else 'FAIL'}"
            )
            if not pass_roe:
                all_passed = False
        else:
            print("ROE Check: Insufficient raw data")

        # 2. Manual 5-Year Revenue CAGR Check (2019 to 2024)
        pnl_base = pnl[(pnl["company_id"] == cid) & (pnl["year"] == base_year)]
        pnl_end = pnl[(pnl["company_id"] == cid) & (pnl["year"] == target_year)]

        if not pnl_base.empty and not pnl_end.empty and not db_ratio_row.empty:
            rev_base = pnl_base.iloc[0]["sales"]
            rev_end = pnl_end.iloc[0]["sales"]

            manual_cagr = ((rev_end / rev_base) ** (1.0 / n_years) - 1.0) * 100.0
            db_cagr = db_ratio_row.iloc[0]["revenue_cagr_5yr"]
            diff_cagr = abs(manual_cagr - db_cagr)

            pass_cagr = diff_cagr < 0.1
            print(
                f"Revenue CAGR (5Y): Manual = {manual_cagr:.4f}% | DB = {db_cagr:.4f}% | Diff = {diff_cagr:.4f}% | Result: {'PASS' if pass_cagr else 'FAIL'}"
            )
            if not pass_cagr:
                all_passed = False
        else:
            print("CAGR Check: Insufficient raw data")

    print(
        "\n==================================================================================="
    )
    print(
        f"FINAL MANUAL SPOT CHECK RESULT: {'PASS (All diffs < 0.1%)' if all_passed else 'FAIL'}"
    )
    print(
        "==================================================================================="
    )
    return all_passed


if __name__ == "__main__":
    run_manual_spot_checks()
