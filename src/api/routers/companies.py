"""
Company Data API Router Module (Day 39).
Implements REST endpoints for listing companies, detailed company profiles, P&L,
Balance Sheet, Cash Flow histories, financial ratios, and binary tearsheet PDF streaming.
"""

import os
import sqlite3
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse

from src.api.database import get_db

router = APIRouter(tags=["Companies"])


@router.get("/companies")
def get_companies(
    sector: Optional[str] = Query(None, description="Filter by broad sector"),
    market_cap_category: Optional[str] = Query(None, description="Filter by market cap category"),
    search: Optional[str] = Query(None, description="Search term for ticker or company name"),
    db: sqlite3.Connection = Depends(get_db)
) -> List[Dict[str, Any]]:
    """
    Returns list of companies with basic info and latest ROE/ROCE metrics.
    Supports filtering by sector, market cap category, and search query.
    """
    query = """
    WITH LatestRatios AS (
        SELECT f.*,
               ROW_NUMBER() OVER (PARTITION BY f.company_id ORDER BY f.year DESC) as rn
        FROM financial_ratios f
    )
    SELECT 
        c.company_id as id,
        c.company_name,
        s.broad_sector,
        s.sub_sector,
        s.market_cap_category,
        lr.return_on_equity_pct as roe_pct,
        lr.roce_pct
    FROM companies c
    LEFT JOIN sectors s ON c.company_id = s.company_id
    LEFT JOIN LatestRatios lr ON c.company_id = lr.company_id AND lr.rn = 1
    WHERE 1=1
    """
    params = []

    if sector:
        query += " AND (s.broad_sector LIKE ? OR s.sub_sector LIKE ?)"
        params.extend([f"%{sector}%", f"%{sector}%"])

    if market_cap_category:
        query += " AND s.market_cap_category LIKE ?"
        params.append(f"%{market_cap_category}%")

    if search:
        query += " AND (c.company_id LIKE ? OR c.company_name LIKE ?)"
        params.extend([f"%{search}%", f"%{search}%"])

    query += " ORDER BY c.company_id ASC"

    cur = db.cursor()
    cur.execute(query, params)
    rows = cur.fetchall()

    return [dict(row) for row in rows]


@router.get("/companies/{ticker}")
def get_company_detail(ticker: str, db: sqlite3.Connection = Depends(get_db)) -> Dict[str, Any]:
    """
    Returns comprehensive profile and latest financial KPIs for a single company.
    Case-insensitive ticker lookup; returns 404 if not found.
    """
    ticker_upper = ticker.strip().upper()

    query = """
    WITH LatestRatios AS (
        SELECT f.*,
               ROW_NUMBER() OVER (PARTITION BY f.company_id ORDER BY f.year DESC) as rn
        FROM financial_ratios f
    ),
    LatestMarketCap AS (
        SELECT m.*,
               ROW_NUMBER() OVER (PARTITION BY m.company_id ORDER BY m.year DESC) as rn
        FROM market_cap m
    )
    SELECT 
        c.company_id,
        c.company_name,
        c.nse_profile,
        c.bse_profile,
        c.about_company,
        c.website,
        s.broad_sector,
        s.sub_sector,
        s.market_cap_category,
        lr.*,
        mc.market_cap_crore,
        mc.pe_ratio,
        mc.pb_ratio,
        mc.ev_ebitda,
        mc.dividend_yield_pct
    FROM companies c
    LEFT JOIN sectors s ON c.company_id = s.company_id
    LEFT JOIN LatestRatios lr ON c.company_id = lr.company_id AND lr.rn = 1
    LEFT JOIN LatestMarketCap mc ON c.company_id = mc.company_id AND mc.rn = 1
    WHERE UPPER(c.company_id) = ?
    """
    cur = db.cursor()
    cur.execute(query, (ticker_upper,))
    row = cur.fetchone()

    if not row:
        raise HTTPException(status_code=404, detail=f"Company with ticker '{ticker}' not found.")

    res = dict(row)
    if 'rn' in res:
        del res['rn']
    return res


@router.get("/companies/{ticker}/pl")
def get_company_pl(
    ticker: str,
    from_year: Optional[int] = Query(None, description="Start year YYYY"),
    to_year: Optional[int] = Query(None, description="End year YYYY"),
    db: sqlite3.Connection = Depends(get_db)
) -> List[Dict[str, Any]]:
    """Returns P&L historical statements for a company."""
    ticker_upper = ticker.strip().upper()

    query = "SELECT * FROM profitandloss WHERE UPPER(company_id) = ?"
    params = [ticker_upper]

    if from_year:
        query += " AND year >= ?"
        params.append(from_year)
    if to_year:
        query += " AND year <= ?"
        params.append(to_year)

    query += " ORDER BY year ASC"

    cur = db.cursor()
    cur.execute(query, params)
    rows = cur.fetchall()

    if not rows:
        # Check if company exists
        cur.execute("SELECT 1 FROM companies WHERE UPPER(company_id) = ?", (ticker_upper,))
        if not cur.fetchone():
            raise HTTPException(status_code=404, detail=f"Company '{ticker}' not found.")

    return [dict(row) for row in rows]


@router.get("/companies/{ticker}/bs")
def get_company_bs(
    ticker: str,
    from_year: Optional[int] = Query(None),
    to_year: Optional[int] = Query(None),
    db: sqlite3.Connection = Depends(get_db)
) -> List[Dict[str, Any]]:
    """Returns Balance Sheet historical statements for a company."""
    ticker_upper = ticker.strip().upper()

    query = "SELECT * FROM balancesheet WHERE UPPER(company_id) = ?"
    params = [ticker_upper]

    if from_year:
        query += " AND year >= ?"
        params.append(from_year)
    if to_year:
        query += " AND year <= ?"
        params.append(to_year)

    query += " ORDER BY year ASC"

    cur = db.cursor()
    cur.execute(query, params)
    rows = cur.fetchall()

    if not rows:
        cur.execute("SELECT 1 FROM companies WHERE UPPER(company_id) = ?", (ticker_upper,))
        if not cur.fetchone():
            raise HTTPException(status_code=404, detail=f"Company '{ticker}' not found.")

    return [dict(row) for row in rows]


@router.get("/companies/{ticker}/cashflow")
def get_company_cashflow(
    ticker: str,
    from_year: Optional[int] = Query(None),
    to_year: Optional[int] = Query(None),
    db: sqlite3.Connection = Depends(get_db)
) -> List[Dict[str, Any]]:
    """Returns Cash Flow historical statements for a company."""
    ticker_upper = ticker.strip().upper()

    query = "SELECT * FROM cashflow WHERE UPPER(company_id) = ?"
    params = [ticker_upper]

    if from_year:
        query += " AND year >= ?"
        params.append(from_year)
    if to_year:
        query += " AND year <= ?"
        params.append(to_year)

    query += " ORDER BY year ASC"

    cur = db.cursor()
    cur.execute(query, params)
    rows = cur.fetchall()

    if not rows:
        cur.execute("SELECT 1 FROM companies WHERE UPPER(company_id) = ?", (ticker_upper,))
        if not cur.fetchone():
            raise HTTPException(status_code=404, detail=f"Company '{ticker}' not found.")

    return [dict(row) for row in rows]


@router.get("/companies/{ticker}/ratios")
def get_company_ratios(
    ticker: str,
    year: Optional[int] = Query(None, description="Specific year YYYY"),
    db: sqlite3.Connection = Depends(get_db)
) -> List[Dict[str, Any]]:
    """Returns financial ratios for a company, optionally filtered by year."""
    ticker_upper = ticker.strip().upper()

    query = "SELECT * FROM financial_ratios WHERE UPPER(company_id) = ?"
    params = [ticker_upper]

    if year:
        query += " AND year = ?"
        params.append(year)

    query += " ORDER BY year ASC"

    cur = db.cursor()
    cur.execute(query, params)
    rows = cur.fetchall()

    if not rows:
        cur.execute("SELECT 1 FROM companies WHERE UPPER(company_id) = ?", (ticker_upper,))
        if not cur.fetchone():
            raise HTTPException(status_code=404, detail=f"Company '{ticker}' not found.")

    return [dict(row) for row in rows]


@router.get("/companies/{ticker}/tearsheet")
def get_company_tearsheet_pdf(ticker: str) -> FileResponse:
    """Returns pre-generated 2-page tearsheet PDF for the company."""
    ticker_upper = ticker.strip().upper()
    pdf_path = os.path.join("reports", "tearsheets", f"{ticker_upper}_tearsheet.pdf")

    if not os.path.exists(pdf_path):
        raise HTTPException(status_code=404, detail=f"Tearsheet PDF for ticker '{ticker}' not found.")

    return FileResponse(
        pdf_path,
        media_type="application/pdf",
        filename=f"{ticker_upper}_tearsheet.pdf"
    )
