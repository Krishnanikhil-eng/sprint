"""
Screener Preview Validation Script.
Runs the required equity screener query: ROE > 15% AND D/E < 1.0 (for latest available year per company)
Expected output: 15 to 50 companies.
"""

import sqlite3
import pandas as pd


def run_screener_preview(db_path: str = "data/nifty100.db") -> pd.DataFrame:
    conn = sqlite3.connect(db_path)

    query = """
    WITH LatestRatios AS (
        SELECT f.*,
               ROW_NUMBER() OVER (PARTITION BY company_id ORDER BY year DESC) as rn
        FROM financial_ratios f
    )
    SELECT company_id, year, return_on_equity_pct, debt_to_equity, net_profit_margin_pct, operating_profit_margin_pct
    FROM LatestRatios
    WHERE rn = 1
      AND return_on_equity_pct > 15.0
      AND debt_to_equity < 1.0
    ORDER BY return_on_equity_pct DESC;
    """

    df_screener = pd.read_sql_query(query, conn)
    conn.close()

    comp_count = len(df_screener)
    print(
        "==================================================================================="
    )
    print(
        "               SPRINT 2 — SCREENER PREVIEW (ROE > 15%, D/E < 1.0)                 "
    )
    print(
        "==================================================================================="
    )
    print(f"Total matching companies: {comp_count}")
    print("\nMatching Companies Sample (Top 15):")
    print(df_screener.head(15).to_string(index=False))

    valid_range = 15 <= comp_count <= 50
    print(
        "\n==================================================================================="
    )
    print(
        f"SCREENER VALIDATION RESULT: {'PASS (Count within expected range 15-50)' if valid_range else 'FAIL (Out of range)'}"
    )
    print(
        "==================================================================================="
    )
    return df_screener


if __name__ == "__main__":
    run_screener_preview()
