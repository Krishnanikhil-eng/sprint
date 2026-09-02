"""
Screener Engine Core Module.
Provides the fundamental engine class for querying, filtering, and scoring
Nifty 100 stock ratios stored in the SQLite database.
"""

import sqlite3
import logging
from typing import Optional, Dict, Any, List
import pandas as pd

from src.analytics.screener_config import ScreenerConfig, FilterCriterion, FilterOperator

logger = logging.getLogger(__name__)

class ScreenerEngine:
    """Core execution engine for stock screening operations."""
    
    def __init__(self, db_path: str = "nifty100.db"):
        self.db_path = db_path
        self.raw_data: Optional[pd.DataFrame] = None
        self.filtered_data: Optional[pd.DataFrame] = None
        self.config: Optional[ScreenerConfig] = None

    def set_config(self, config: ScreenerConfig) -> None:
        """Sets the active screening configuration."""
        self.config = config
        logger.info(f"Loaded active config: '{config.name}' with {len(config.criteria)} criteria.")

    def load_config_from_json(self, json_path: str) -> ScreenerConfig:
        """Loads and sets configuration from a JSON file path."""
        config = ScreenerConfig.from_json(json_path)
        self.set_config(config)
        return config


    def get_connection(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)

    def load_latest_company_ratios(self) -> pd.DataFrame:
        """
        Loads the latest available annual financial ratios per company from SQLite,
        joined with company metadata and broad sector classifications.
        """
        query = """
        WITH LatestRatios AS (
            SELECT f.*,
                   ROW_NUMBER() OVER (PARTITION BY f.company_id ORDER BY f.year DESC) as rn
            FROM financial_ratios f
        )
        SELECT 
            lr.company_id,
            c.company_name,
            s.broad_sector,
            s.sub_sector,
            s.market_cap_category,
            lr.year,
            lr.net_profit_margin_pct,
            lr.operating_profit_margin_pct,
            lr.return_on_equity_pct,
            lr.roce_pct,
            lr.roa_pct,
            lr.debt_to_equity,
            lr.interest_coverage,
            lr.icr_label,
            lr.asset_turnover,
            lr.free_cash_flow_cr,
            lr.capex_cr,
            lr.earnings_per_share,
            lr.book_value_per_share,
            lr.dividend_payout_ratio_pct,
            lr.total_debt_cr,
            lr.cash_from_operations_cr,
            lr.revenue_cagr_5yr,
            lr.pat_cagr_5yr,
            lr.eps_cagr_5yr,
            lr.composite_quality_score,
            lr.high_leverage_flag,
            lr.net_debt_cr,
            lr.capex_intensity_pct,
            lr.fcf_conversion_pct,
            lr.capital_allocation_pattern
        FROM LatestRatios lr
        JOIN companies c ON lr.company_id = c.company_id
        LEFT JOIN sectors s ON lr.company_id = s.company_id
        WHERE lr.rn = 1;
        """
        conn = self.get_connection()
        try:
            df = pd.read_sql_query(query, conn)
            self.raw_data = df
            logger.info(f"Loaded latest ratios for {len(df)} companies.")
            return df
        finally:
            conn.close()
