"""
Sectors API Router Module (Day 40).
Implements REST endpoints for sector statistics and sector-filtered company listings.
"""

import sqlite3
from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException

from src.api.database import get_db

router = APIRouter(tags=["Sectors"])


@router.get("/sectors")
def get_sectors(db: sqlite3.Connection = Depends(get_db)) -> List[Dict[str, Any]]:
    """
    Returns aggregate financial metrics across broad sectors, including
    company count, average ROE/ROCE, and total market capitalization.
    """
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
        s.broad_sector as sector,
        COUNT(DISTINCT s.company_id) as company_count,
        ROUND(AVG(lr.return_on_equity_pct), 2) as avg_roe_pct,
        ROUND(AVG(lr.roce_pct), 2) as avg_roce_pct,
        ROUND(SUM(lv.market_cap_crore), 2) as total_market_cap_crore
    FROM sectors s
    LEFT JOIN LatestRatios lr ON s.company_id = lr.company_id AND lr.rn = 1
    LEFT JOIN LatestValuation lv ON s.company_id = lv.company_id AND lv.rn = 1
    WHERE s.broad_sector IS NOT NULL AND s.broad_sector != ''
    GROUP BY s.broad_sector
    ORDER BY total_market_cap_crore DESC;
    """
    cursor = db.cursor()
    cursor.execute(query)
    rows = cursor.fetchall()
    return [dict(row) for row in rows]


@router.get("/sectors/{sector}/companies")
def get_sector_companies(
    sector: str, db: sqlite3.Connection = Depends(get_db)
) -> List[Dict[str, Any]]:
    """
    Returns list of companies belonging to a specific broad sector.
    """
    query = """
    WITH LatestRatios AS (
        SELECT f.*,
               ROW_NUMBER() OVER (PARTITION BY f.company_id ORDER BY f.year DESC) as rn
        FROM financial_ratios f
    )
    SELECT 
        c.company_id as ticker,
        c.company_name,
        s.broad_sector as sector,
        s.sub_sector,
        s.market_cap_category,
        lr.return_on_equity_pct as roe_pct,
        lr.roce_pct,
        lr.debt_to_equity
    FROM companies c
    JOIN sectors s ON c.company_id = s.company_id
    LEFT JOIN LatestRatios lr ON c.company_id = lr.company_id AND lr.rn = 1
    WHERE UPPER(s.broad_sector) = UPPER(?);
    """
    cursor = db.cursor()
    cursor.execute(query, (sector.strip(),))
    rows = cursor.fetchall()

    if not rows:
        raise HTTPException(
            status_code=404, detail=f"No sector found matching '{sector}'"
        )

    return [dict(row) for row in rows]
