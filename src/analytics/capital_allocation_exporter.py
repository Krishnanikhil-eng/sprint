"""
Capital Allocation Exporter.
Reads cash flow and profit & loss data from SQLite database, calculates 8-pattern classification,
and writes output/capital_allocation.csv.
"""

import os
import sqlite3
import pandas as pd
from src.analytics.cashflow_kpis import classify_capital_allocation


def export_capital_allocation(
    db_path: str = "data/nifty100.db", output_path: str = "output/capital_allocation.csv"
) -> str:
    conn = sqlite3.connect(db_path)

    cf_df = pd.read_sql_query(
        "SELECT company_id, year, operating_activity, investing_activity, financing_activity FROM cashflow",
        conn,
    )
    pnl_df = pd.read_sql_query(
        "SELECT company_id, year, net_profit FROM profitandloss", conn
    )

    conn.close()

    merged = pd.merge(cf_df, pnl_df, on=["company_id", "year"], how="left")

    results = []
    for _, row in merged.iterrows():
        company_id = row["company_id"]
        year = int(row["year"])
        cfo = row["operating_activity"]
        cfi = row["investing_activity"]
        cff = row["financing_activity"]
        pat = row["net_profit"]

        cfo_pat_ratio = None
        if cfo is not None and pat is not None and pat != 0:
            cfo_pat_ratio = cfo / pat

        cfo_sign, cfi_sign, cff_sign, label = classify_capital_allocation(
            cfo, cfi, cff, cfo_pat_ratio
        )

        results.append(
            {
                "company_id": company_id,
                "year": year,
                "cfo_sign": cfo_sign,
                "cfi_sign": cfi_sign,
                "cff_sign": cff_sign,
                "pattern_label": label,
            }
        )

    res_df = pd.DataFrame(results)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    res_df.to_csv(output_path, index=False)
    print(f"Capital allocation exported to {output_path} with {len(res_df)} records.")
    return output_path


if __name__ == "__main__":
    export_capital_allocation()
