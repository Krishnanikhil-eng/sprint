"""
SQLite Database Index Optimization Script (Day 43).
Creates composite indexes on company_id and year across all major tables
to accelerate REST API query performance and JOIN efficiency.
"""

import sqlite3
import time

DB_PATH = "nifty100.db"


def optimize_indexes():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    index_statements = [
        "CREATE INDEX IF NOT EXISTS idx_ratios_company_year ON financial_ratios (company_id, year DESC)",
        "CREATE INDEX IF NOT EXISTS idx_mcap_company_year ON market_cap (company_id, year DESC)",
        "CREATE INDEX IF NOT EXISTS idx_pnl_company_year ON profitandloss (company_id, year DESC)",
        "CREATE INDEX IF NOT EXISTS idx_bs_company_year ON balancesheet (company_id, year DESC)",
        "CREATE INDEX IF NOT EXISTS idx_cf_company_year ON cashflow (company_id, year DESC)",
        "CREATE INDEX IF NOT EXISTS idx_doc_company_year ON documents (company_id, year DESC)",
        "CREATE INDEX IF NOT EXISTS idx_prices_company_date ON stock_prices (company_id, date DESC)",
        "CREATE INDEX IF NOT EXISTS idx_sectors_company ON sectors (company_id)",
        "CREATE INDEX IF NOT EXISTS idx_peers_company ON peer_groups (company_id)"
    ]

    print("Optimizing SQLite database indexes...")
    start = time.time()
    for stmt in index_statements:
        cursor.execute(stmt)
    conn.commit()
    conn.close()
    elapsed = round((time.time() - start) * 1000, 2)
    print(f"Database indexes optimized successfully in {elapsed} ms.")


if __name__ == "__main__":
    optimize_indexes()
