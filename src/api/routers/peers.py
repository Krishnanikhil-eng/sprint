"""
Peer Analysis API Router Module (Day 40).
Implements REST endpoints for peer group listings, group member metrics,
and company peer relative percentile comparisons.
"""

import sqlite3
from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException

from src.api.database import get_db

router = APIRouter(tags=["Peers"])


@router.get("/peers")
def get_peer_groups(db: sqlite3.Connection = Depends(get_db)) -> List[Dict[str, Any]]:
    """
    Returns list of all available peer groups with member company counts.
    """
    query = """
    SELECT 
        peer_group_name,
        COUNT(company_id) as member_count
    FROM peer_groups
    GROUP BY peer_group_name
    ORDER BY member_count DESC;
    """
    cursor = db.cursor()
    cursor.execute(query)
    rows = cursor.fetchall()
    return [dict(row) for row in rows]


@router.get("/peers/{group_name}")
def get_peer_group_members(
    group_name: str,
    db: sqlite3.Connection = Depends(get_db)
) -> Dict[str, Any]:
    """
    Returns company members and aggregate metrics for a specified peer group.
    """
    group_clean = group_name.strip()
    query_members = """
    WITH LatestRatios AS (
        SELECT f.*,
               ROW_NUMBER() OVER (PARTITION BY f.company_id ORDER BY f.year DESC) as rn
        FROM financial_ratios f
    )
    SELECT 
        pg.company_id as ticker,
        c.company_name,
        pg.is_benchmark,
        lr.return_on_equity_pct as roe_pct,
        lr.roce_pct,
        lr.debt_to_equity,
        lr.operating_profit_margin_pct as opm_pct,
        lr.revenue_cagr_5yr
    FROM peer_groups pg
    JOIN companies c ON pg.company_id = c.company_id
    LEFT JOIN LatestRatios lr ON pg.company_id = lr.company_id AND lr.rn = 1
    WHERE UPPER(pg.peer_group_name) = UPPER(?);
    """
    cursor = db.cursor()
    cursor.execute(query_members, (group_clean,))
    rows = cursor.fetchall()

    if not rows:
        raise HTTPException(
            status_code=404,
            detail=f"Peer group '{group_name}' not found"
        )

    members = [dict(row) for row in rows]
    return {
        "peer_group_name": group_clean,
        "member_count": len(members),
        "members": members
    }


@router.get("/companies/{ticker}/peers/compare")
def compare_company_peers(
    ticker: str,
    db: sqlite3.Connection = Depends(get_db)
) -> Dict[str, Any]:
    """
    Returns peer comparison profile for a company, including peer group percentiles
    and relative performance against peer averages.
    """
    ticker_upper = ticker.strip().upper()
    cursor = db.cursor()

    # Verify company exists
    cursor.execute("SELECT company_id, company_name FROM companies WHERE UPPER(company_id) = ?", (ticker_upper,))
    company = cursor.fetchone()
    if not company:
        raise HTTPException(status_code=404, detail=f"Company ticker '{ticker}' not found")

    # Fetch percentiles
    cursor.execute("SELECT * FROM peer_percentiles WHERE UPPER(company_id) = ?", (ticker_upper,))
    pct_row = cursor.fetchone()
    
    percentiles = dict(pct_row) if pct_row else {}

    # Fetch peer group members and group averages
    cursor.execute("""
        SELECT pg.peer_group_name 
        FROM peer_groups pg 
        WHERE UPPER(pg.company_id) = ?
        LIMIT 1
    """, (ticker_upper,))
    pg_res = cursor.fetchone()
    
    peer_group_name = pg_res["peer_group_name"] if pg_res else percentiles.get("effective_peer_group", "Unknown")

    return {
        "ticker": company["company_id"],
        "company_name": company["company_name"],
        "peer_group": peer_group_name,
        "percentiles": percentiles
    }
