"""
Health Router Module (Day 38).
Provides GET /api/v1/health returning application status, database table row counts,
uptime, and version info.
"""

import time
import sqlite3
from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException

from src.api.database import get_db

router = APIRouter()
START_TIME = time.time()

PROJECT_TABLES = [
    "companies",
    "profitandloss",
    "balancesheet",
    "cashflow",
    "analysis",
    "documents",
    "prosandcons",
    "sectors",
    "peer_groups",
    "financial_ratios",
    "stock_prices",
    "market_cap",
]


@router.get("/health", tags=["Health"])
def get_health_status(db: sqlite3.Connection = Depends(get_db)) -> Dict[str, Any]:
    """
    Returns system health status, DB row counts for project tables,
    uptime in seconds, and version.
    """
    db_counts = {}
    try:
        cur = db.cursor()
        for table in PROJECT_TABLES:
            try:
                cur.execute(f"SELECT COUNT(1) FROM {table}")
                db_counts[table] = cur.fetchone()[0]
            except sqlite3.Error:
                db_counts[table] = 0
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Database connection error: {str(e)}"
        )

    uptime = round(time.time() - START_TIME, 2)

    return {
        "status": "ok",
        "version": "1.0.0",
        "uptime_seconds": uptime,
        "db_row_counts": db_counts,
    }
