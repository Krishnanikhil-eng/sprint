"""
Valuation API Router Module (Day 40).
Implements REST endpoint for company valuation history and market cap metrics.
"""

import sqlite3
from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException

from src.api.database import get_db

router = APIRouter(tags=["Valuation"])


@router.get("/market-cap/{ticker}")
@router.get("/companies/{ticker}/valuation")
def get_company_valuation(
    ticker: str,
    db: sqlite3.Connection = Depends(get_db)
) -> Dict[str, Any]:
    """
    Returns annual valuation history (Market Cap, Enterprise Value, P/E, P/B, EV/EBITDA, Dividend Yield)
    for a specified company ticker.
    """
    ticker_upper = ticker.strip().upper()
    cursor = db.cursor()

    # Verify company exists
    cursor.execute("SELECT company_id, company_name FROM companies WHERE UPPER(company_id) = ?", (ticker_upper,))
    company = cursor.fetchone()
    if not company:
        raise HTTPException(
            status_code=404,
            detail=f"Company ticker '{ticker}' not found"
        )

    # Fetch market cap valuation series
    query = """
    SELECT 
        year,
        market_cap_crore,
        enterprise_value_crore,
        pe_ratio,
        pb_ratio,
        ev_ebitda,
        dividend_yield_pct
    FROM market_cap
    WHERE UPPER(company_id) = ?
    ORDER BY year ASC;
    """
    cursor.execute(query, (ticker_upper,))
    rows = cursor.fetchall()

    history = [dict(row) for row in rows]
    latest = history[-1] if history else {}

    return {
        "ticker": company["company_id"],
        "company_name": company["company_name"],
        "latest_valuation": latest,
        "history": history
    }
