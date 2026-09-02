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

    def _matches_criterion(self, row: pd.Series, criterion: FilterCriterion) -> bool:
        """Evaluates whether a row matches a specific filter criterion."""
        val = row.get(criterion.metric_name)
        return criterion.evaluate(val)

    def apply_filters(self, df: Optional[pd.DataFrame] = None) -> pd.DataFrame:
        """
        Applies configured criteria filters against loaded company data.
        """
        if df is None:
            if self.raw_data is None:
                self.load_latest_company_ratios()
            df = self.raw_data.copy()
        else:
            df = df.copy()

        if not self.config or not self.config.criteria:
            self.filtered_data = df
            return df

        mask = pd.Series(True, index=df.index)
        for criterion in self.config.criteria:
            crit_mask = df.apply(lambda row: self._matches_criterion(row, criterion), axis=1)
            mask = mask & crit_mask

        filtered = df[mask].copy()
        self.filtered_data = filtered
        logger.info(f"Applied {len(self.config.criteria)} criteria: {len(filtered)} / {len(df)} companies passed.")
        return filtered

    def filter_by_core_ratios(self,
                              min_roe: Optional[float] = None,
                              max_de: Optional[float] = None,
                              min_fcf: Optional[float] = None,
                              df: Optional[pd.DataFrame] = None) -> pd.DataFrame:
        """
        Convenience method to quickly filter companies by core pillar metrics:
        Return on Equity (%), Debt to Equity, and Free Cash Flow (Cr).
        """
        if df is None:
            if self.raw_data is None:
                self.load_latest_company_ratios()
            df = self.raw_data.copy()

        criteria = []
        if min_roe is not None:
            criteria.append(FilterCriterion("return_on_equity_pct", FilterOperator.GREATER_EQUAL, value=min_roe, description=f"ROE >= {min_roe}%"))
        if max_de is not None:
            criteria.append(FilterCriterion("debt_to_equity", FilterOperator.LESS_EQUAL, value=max_de, description=f"D/E <= {max_de}"))
        if min_fcf is not None:
            criteria.append(FilterCriterion("free_cash_flow_cr", FilterOperator.GREATER_EQUAL, value=min_fcf, description=f"FCF >= {min_fcf} Cr"))

        config = ScreenerConfig(name="Core Ratios Quick Filter", description="Filtering by ROE, D/E, and FCF", criteria=criteria)
        self.set_config(config)
        return self.apply_filters(df)

    def filter_by_multi_metrics(self,
                                min_npm: Optional[float] = None,
                                min_opm: Optional[float] = None,
                                min_roce: Optional[float] = None,
                                min_roa: Optional[float] = None,
                                min_asset_turnover: Optional[float] = None,
                                min_rev_cagr: Optional[float] = None,
                                min_pat_cagr: Optional[float] = None,
                                min_dividend_payout: Optional[float] = None,
                                df: Optional[pd.DataFrame] = None) -> pd.DataFrame:
        """
        Filters data across profitability margins, capital efficiency, turnover, and growth CAGRs.
        """
        if df is None:
            if self.raw_data is None:
                self.load_latest_company_ratios()
            df = self.raw_data.copy()

        criteria = []
        if min_npm is not None:
            criteria.append(FilterCriterion("net_profit_margin_pct", FilterOperator.GREATER_EQUAL, value=min_npm))
        if min_opm is not None:
            criteria.append(FilterCriterion("operating_profit_margin_pct", FilterOperator.GREATER_EQUAL, value=min_opm))
        if min_roce is not None:
            criteria.append(FilterCriterion("roce_pct", FilterOperator.GREATER_EQUAL, value=min_roce))
        if min_roa is not None:
            criteria.append(FilterCriterion("roa_pct", FilterOperator.GREATER_EQUAL, value=min_roa))
        if min_asset_turnover is not None:
            criteria.append(FilterCriterion("asset_turnover", FilterOperator.GREATER_EQUAL, value=min_asset_turnover))
        if min_rev_cagr is not None:
            criteria.append(FilterCriterion("revenue_cagr_5yr", FilterOperator.GREATER_EQUAL, value=min_rev_cagr))
        if min_pat_cagr is not None:
            criteria.append(FilterCriterion("pat_cagr_5yr", FilterOperator.GREATER_EQUAL, value=min_pat_cagr))
        if min_dividend_payout is not None:
            criteria.append(FilterCriterion("dividend_payout_ratio_pct", FilterOperator.GREATER_EQUAL, value=min_dividend_payout))

        config = ScreenerConfig(name="Multi-Metric Advanced Filter", description="Filtering margins, return ratios, turnover, and CAGRs", criteria=criteria)
        self.set_config(config)
        return self.apply_filters(df)



