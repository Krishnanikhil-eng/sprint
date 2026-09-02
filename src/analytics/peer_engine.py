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

    def compute_peer_percentiles(self, df: Optional[pd.DataFrame] = None) -> pd.DataFrame:
        """
        Computes percentile ranks (0 to 100) for standard metrics within each peer group.
        Higher numeric values get higher percentile ranks for standard metrics.
        """
        if df is None:
            if self.ratios_df is None:
                self.load_peer_data()
            df = self.ratios_df.copy()

        standard_metrics = [
            "return_on_equity_pct", "roce_pct", "roa_pct",
            "net_profit_margin_pct", "operating_profit_margin_pct",
            "asset_turnover", "free_cash_flow_cr", "revenue_cagr_5yr", "pat_cagr_5yr"
        ]

        def _percentile_group(g):
            res = g.copy()
            for metric in standard_metrics:
                if metric in res.columns and res[metric].notnull().any():
                    col_name = f"{metric}_percentile"
                    if len(res) == 1:
                        res[col_name] = 100.0
                    else:
                        res[col_name] = (res[metric].rank(pct=True) * 100.0).round(2)
            return res

        try:
            res_df = df.groupby("effective_peer_group", group_keys=False, include_groups=False).apply(_percentile_group)
        except TypeError:
            res_df = df.groupby("effective_peer_group", group_keys=False).apply(_percentile_group)

        self.percentiles_df = res_df
        logger.info(f"Computed standard metric percentiles across {len(res_df)} companies.")
        return res_df

    def compute_inverse_debt_percentiles(self, df: Optional[pd.DataFrame] = None) -> pd.DataFrame:
        """
        Computes INVERSE percentile ranks for leverage metrics (debt_to_equity, net_debt_cr).
        For debt metrics, LOWER is BETTER, so lower numeric values get higher percentile scores (100 = lowest debt).
        """
        if df is None:
            if self.percentiles_df is None:
                df = self.compute_peer_percentiles()
            else:
                df = self.percentiles_df.copy()
        else:
            df = df.copy()

        inverse_metrics = ["debt_to_equity", "net_debt_cr"]

        def _inverse_group(g):
            res = g.copy()
            for metric in inverse_metrics:
                if metric in res.columns and res[metric].notnull().any():
                    col_name = f"{metric}_percentile"
                    if len(res) == 1:
                        res[col_name] = 100.0
                    else:
                        # Invert rank: rank ascending=False gives 1st rank to smallest debt
                        res[col_name] = (res[metric].rank(pct=True, ascending=False) * 100.0).round(2)
            return res

        try:
            res_df = df.groupby("effective_peer_group", group_keys=False, include_groups=False).apply(_inverse_group)
        except TypeError:
            res_df = df.groupby("effective_peer_group", group_keys=False).apply(_inverse_group)

        self.percentiles_df = res_df
        logger.info("Computed inverse leverage metric percentiles.")
        return res_df

    def save_peer_percentiles_to_db(self, df: Optional[pd.DataFrame] = None) -> None:
        """
        Creates and populates the `peer_percentiles` table in SQLite database `nifty100.db`.
        """
        if df is None:
            if self.percentiles_df is None:
                self.compute_inverse_debt_percentiles()
            df = self.percentiles_df.copy()

        # Calculate overall peer composite percentile score
        percentile_cols = [c for c in df.columns if c.endswith("_percentile")]
        df["overall_peer_percentile"] = df[percentile_cols].mean(axis=1).round(2)

        # Prepare table schema & columns
        db_cols = {
            "company_id": "TEXT PRIMARY KEY",
            "effective_peer_group": "TEXT",
            "broad_sector": "TEXT",
            "sub_sector": "TEXT",
            "return_on_equity_pct_percentile": "REAL",
            "roce_pct_percentile": "REAL",
            "debt_to_equity_percentile": "REAL",
            "net_profit_margin_pct_percentile": "REAL",
            "operating_profit_margin_pct_percentile": "REAL",
            "asset_turnover_percentile": "REAL",
            "free_cash_flow_cr_percentile": "REAL",
            "revenue_cagr_5yr_percentile": "REAL",
            "pat_cagr_5yr_percentile": "REAL",
            "overall_peer_percentile": "REAL"
        }

        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("DROP TABLE IF EXISTS peer_percentiles;")
            
            create_sql = """
            CREATE TABLE peer_percentiles (
                company_id TEXT PRIMARY KEY,
                effective_peer_group TEXT,
                broad_sector TEXT,
                sub_sector TEXT,
                roe_percentile REAL,
                roce_percentile REAL,
                de_percentile_inv REAL,
                npm_percentile REAL,
                opm_percentile REAL,
                asset_turnover_percentile REAL,
                fcf_percentile REAL,
                revenue_cagr_percentile REAL,
                pat_cagr_percentile REAL,
                overall_peer_percentile REAL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """
            cursor.execute(create_sql)

            # Map dataframe columns to table schema
            save_df = pd.DataFrame()
            save_df["company_id"] = df["company_id"]
            save_df["effective_peer_group"] = df["effective_peer_group"]
            save_df["broad_sector"] = df["broad_sector"]
            save_df["sub_sector"] = df["sub_sector"]
            save_df["roe_percentile"] = df.get("return_on_equity_pct_percentile", 0.0)
            save_df["roce_percentile"] = df.get("roce_pct_percentile", 0.0)
            save_df["de_percentile_inv"] = df.get("debt_to_equity_percentile", 0.0)
            save_df["npm_percentile"] = df.get("net_profit_margin_pct_percentile", 0.0)
            save_df["opm_percentile"] = df.get("operating_profit_margin_pct_percentile", 0.0)
            save_df["asset_turnover_percentile"] = df.get("asset_turnover_percentile", 0.0)
            save_df["fcf_percentile"] = df.get("free_cash_flow_cr_percentile", 0.0)
            save_df["revenue_cagr_percentile"] = df.get("revenue_cagr_5yr_percentile", 0.0)
            save_df["pat_cagr_percentile"] = df.get("pat_cagr_5yr_percentile", 0.0)
            save_df["overall_peer_percentile"] = df["overall_peer_percentile"]

            save_df.to_sql("peer_percentiles", conn, if_exists="append", index=False)
            conn.commit()
            logger.info(f"Saved {len(save_df)} rows to `peer_percentiles` database table.")
        finally:
            conn.close()




