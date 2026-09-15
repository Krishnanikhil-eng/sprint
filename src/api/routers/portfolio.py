"""
Portfolio Statistics API Router Module (Day 40).
Implements REST endpoint for overall 92-company portfolio KPIs and statistical distributions.
"""

import os
import sqlite3
from typing import Dict, Any, List
import pandas as pd
from fastapi import APIRouter, Depends, HTTPException

from src.api.database import get_db

router = APIRouter(tags=["Portfolio"])


@router.get("/portfolio/stats")
def get_portfolio_stats(db: sqlite3.Connection = Depends(get_db)) -> Dict[str, Any]:
    """
    Returns portfolio-wide aggregate KPIs, percentile distributions (P10-P90),
    broad sector allocation, and cluster archetype counts across all companies.
    """
    # Load statistical distributions from output/portfolio_stats.csv if available
    stats_path = os.path.join("output", "portfolio_stats.csv")
    kpi_distributions: List[Dict[str, Any]] = []
    if os.path.exists(stats_path):
        try:
            df_stats = pd.read_csv(stats_path)
            kpi_distributions = df_stats.to_dict(orient="records")
        except Exception:
            kpi_distributions = []

    # Sector distribution count
    cursor = db.cursor()
    cursor.execute("""
        SELECT broad_sector as sector, COUNT(company_id) as count
        FROM sectors
        WHERE broad_sector IS NOT NULL AND broad_sector != ''
        GROUP BY broad_sector
        ORDER BY count DESC;
    """)
    sector_dist = [dict(row) for row in cursor.fetchall()]

    # Cluster distribution count from cluster_labels.csv
    cluster_path = os.path.join("output", "cluster_labels.csv")
    cluster_dist: List[Dict[str, Any]] = []
    if os.path.exists(cluster_path):
        try:
            df_clusters = pd.read_csv(cluster_path)
            if "cluster_label" in df_clusters.columns:
                counts = df_clusters["cluster_label"].value_counts().to_dict()
                cluster_dist = [{"archetype": k, "count": int(v)} for k, v in counts.items()]
        except Exception:
            cluster_dist = []

    return {
        "total_companies": 92,
        "kpi_distributions": kpi_distributions,
        "sector_allocation": sector_dist,
        "cluster_archetypes": cluster_dist
    }
