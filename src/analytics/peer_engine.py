"""
Peer Engine Foundation Module.
Calculates peer group benchmarks, relative percentiles, and inverse debt ranks
for Nifty 100 stocks.
"""

import sqlite3
import logging
from typing import Optional, Dict, Any, List
import pandas as pd

logger = logging.getLogger(__name__)

class PeerEngine:
    """Engine for peer group comparison and percentile rank computations."""

    def __init__(self, db_path: str = "nifty100.db"):
        self.db_path = db_path
        self.peer_groups_df: Optional[pd.DataFrame] = None
        self.ratios_df: Optional[pd.DataFrame] = None
        self.percentiles_df: Optional[pd.DataFrame] = None

    def get_connection(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)

    def load_peer_data(self) -> pd.DataFrame:
        """
        Loads company peer groups along with latest financial ratios and sector info.
        Uses `peer_groups` mapping table or falls back to sub_sector / broad_sector.
        """
        conn = self.get_connection()
        try:
            # Query latest financial ratios per company
            ratios_query = """
            WITH LatestRatios AS (
                SELECT f.*,
                       ROW_NUMBER() OVER (PARTITION BY company_id ORDER BY year DESC) as rn
                FROM financial_ratios f
            )
            SELECT lr.*
            FROM LatestRatios lr
            WHERE lr.rn = 1;
            """
            ratios_df = pd.read_sql_query(ratios_query, conn)

            # Query company metadata & sectors
            meta_query = """
            SELECT c.company_id, c.company_name, s.broad_sector, s.sub_sector
            FROM companies c
            LEFT JOIN sectors s ON c.company_id = s.company_id;
            """
            meta_df = pd.read_sql_query(meta_query, conn)

            # Query peer_groups table
            peer_query = "SELECT * FROM peer_groups;"
            try:
                peers_df = pd.read_sql_query(peer_query, conn)
            except Exception:
                peers_df = pd.DataFrame()

            # Merge metadata with ratios
            merged = pd.merge(meta_df, ratios_df, on="company_id", how="inner")

            # Map peer_group_name (use sub_sector if peer_group_name not available)
            if len(peers_df) > 0 and "peer_group_name" in peers_df.columns:
                merged = pd.merge(merged, peers_df[["company_id", "peer_group_name"]], on="company_id", how="left")
                merged["effective_peer_group"] = merged["peer_group_name"].fillna(merged["sub_sector"]).fillna(merged["broad_sector"])
            else:
                merged["effective_peer_group"] = merged["sub_sector"].fillna(merged["broad_sector"])

            self.ratios_df = merged
            logger.info(f"Loaded peer data for {len(merged)} companies across {merged['effective_peer_group'].nunique()} peer groups.")
            return merged
        finally:
            conn.close()

