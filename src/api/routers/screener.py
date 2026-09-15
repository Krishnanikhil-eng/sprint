"""
Screener API Router Module (Day 40).
Implements REST endpoint for multi-metric custom stock screening.
"""

import sqlite3
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query

from src.api.database import get_db

router = APIRouter(tags=["Screener"])


@router.get("/screener")
def run_screener(
    min_roe: Optional[float] = Query(None, description="Minimum Return on Equity (%)"),
    max_de: Optional[float] = Query(None, description="Maximum Debt to Equity ratio"),
    min_fcf: Optional[float] = Query(None, description="Minimum Free Cash Flow (Cr)"),
    sector: Optional[str] = Query(None, description="Filter by broad sector"),
    min_rev_cagr_5yr: Optional[float] = Query(None, description="Minimum 5-year Revenue CAGR (%)"),
    min_pat_cagr_5yr: Optional[float] = Query(None, description="Minimum 5-year PAT CAGR (%)"),
    max_pe: Optional[float] = Query(None, description="Maximum P/E Ratio"),
    db: sqlite3.Connection = Depends(get_db)
) -> List[Dict[str, Any]]:
    """
    Screens companies based on multi-metric quantitative filters.
    Returns array of matching companies with key financial ratios and valuation metrics.
    """
    # Validation check for negative bounds where inappropriate
    if max_de is not None and max_de < 0:
        raise HTTPException(status_code=400, detail="max_de cannot be negative")
    if max_pe is not None and max_pe < 0:
        raise HTTPException(status_code=400, detail="max_pe cannot be negative")

    query = """
    WITH LatestRatios AS (
        SELECT f.*,
               ROW_NUMBER() OVER (PARTITION BY f.company_id ORDER BY f.year DESC) as rn
        FROM financial_ratios f
    ),
    LatestValuation AS (
        SELECT m.*,
               ROW_NUMBER() OVER (PARTITION BY m.company_id ORDER BY m.year DESC) as rn
        FROM market_cap m
    )
    SELECT 
        c.company_id as ticker,
        c.company_name,
        s.broad_sector as sector,
        s.sub_sector,
        lr.return_on_equity_pct,
        lr.debt_to_equity,
        lr.free_cash_flow_cr,
        lr.revenue_cagr_5yr,
        lr.pat_cagr_5yr,
        lv.pe_ratio,
        lv.market_cap_crore
    FROM companies c
    LEFT JOIN sectors s ON c.company_id = s.company_id
    LEFT JOIN LatestRatios lr ON c.company_id = lr.company_id AND lr.rn = 1
    LEFT JOIN LatestValuation lv ON c.company_id = lv.company_id AND lv.rn = 1
    WHERE 1=1
    """
    params: List[Any] = []

    if sector:
        query += " AND UPPER(s.broad_sector) LIKE ?"
        params.append(f"%{sector.strip().upper()}%")

    cursor = db.cursor()
    cursor.execute(query, params)
    rows = cursor.fetchall()

    results: List[Dict[str, Any]] = []
    for row in rows:
        r = dict(row)
        
        # Apply numerical filter thresholds
        if min_roe is not None:
            val = r.get("return_on_equity_pct")
            if val is None or val < min_roe:
                continue

        if max_de is not None:
            # Exclude strict D/E filtering for Financials if desired, or standard apply
            val = r.get("debt_to_equity")
            if val is not None and val > max_de:
                # Check financial sector exemption
                sec = str(r.get("sector") or "").upper()
                if "FINANCIAL" not in sec and "BANK" not in sec:
                    continue

        if min_fcf is not None:
            val = r.get("free_cash_flow_cr")
            if val is None or val < min_fcf:
                continue

        if min_rev_cagr_5yr is not None:
            val = r.get("revenue_cagr_5yr")
            if val is None or val < min_rev_cagr_5yr:
                continue

        if min_pat_cagr_5yr is not None:
            val = r.get("pat_cagr_5yr")
            if val is None or val < min_pat_cagr_5yr:
                continue

        if max_pe is not None:
            val = r.get("pe_ratio")
            if val is None or val > max_pe:
                continue

        results.append(r)

    return results
