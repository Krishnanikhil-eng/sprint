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
        """Evaluates whether a row matches a specific filter criterion with sector awareness."""
        # Financials sector D/E exemption handling
        if criterion.metric_name == "debt_to_equity" and self.config and self.config.handle_financials_de:
            sector = str(row.get("broad_sector", "")).upper()
            sub_sector = str(row.get("sub_sector", "")).upper()
            if "FINANCIAL" in sector or "BANK" in sector or "FINANCIAL" in sub_sector or "BANK" in sub_sector:
                # Exclude Financials from strict D/E threshold check unless specified otherwise
                return True

        # Debt-Free ICR handling
        if criterion.metric_name == "interest_coverage" and self.config and self.config.handle_zero_debt_icr:
            icr_label = str(row.get("icr_label", "")).upper()
            total_debt = row.get("total_debt_cr")
            if icr_label == "DEBT_FREE" or total_debt == 0 or total_debt == 0.0:
                # Debt-free company automatically satisfies interest coverage requirements
                return True

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

    def compute_raw_composite_score(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Computes a raw weighted composite score based on 4 pillars:
        - Quality/Profitability (35%)
        - Growth (25%)
        - Financial Health/Cash Flow (25%)
        - Capital Efficiency/Turnover (15%)
        """
        df = df.copy()

        # Fill missing values for scoring safely
        roe = df["return_on_equity_pct"].fillna(0.0).clip(lower=-50, upper=100)
        roce = df["roce_pct"].fillna(0.0).clip(lower=-50, upper=100)
        npm = df["net_profit_margin_pct"].fillna(0.0).clip(lower=-50, upper=100)
        
        rev_cagr = df["revenue_cagr_5yr"].fillna(0.0).clip(lower=-30, upper=100)
        pat_cagr = df["pat_cagr_5yr"].fillna(0.0).clip(lower=-30, upper=100)
        
        fcf = df["free_cash_flow_cr"].fillna(0.0)
        fcf_score = (fcf > 0).astype(float) * 10.0 + (fcf / 100.0).clip(lower=-10, upper=40)
        de = df["debt_to_equity"].fillna(0.0).clip(lower=0, upper=10)
        de_health = (10.0 - de).clip(lower=0, upper=10) # lower D/E is healthier
        
        asset_turnover = df["asset_turnover"].fillna(0.0).clip(lower=0, upper=5)

        # Pillar Scores
        quality_pillar = (roe * 0.4) + (roce * 0.4) + (npm * 0.2)
        growth_pillar = (rev_cagr * 0.5) + (pat_cagr * 0.5)
        health_pillar = (de_health * 5.0) + (fcf_score * 0.5)
        efficiency_pillar = asset_turnover * 20.0

        raw_score = (quality_pillar * 0.35) + (growth_pillar * 0.25) + (health_pillar * 0.25) + (efficiency_pillar * 0.15)
        df["raw_composite_score"] = raw_score.round(2)
        return df

    def normalize_composite_scores(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Normalizes raw composite scores to a standardized 0-100 scale using Min-Max scaling.
        If all scores are identical, defaults to 50.0.
        """
        if "raw_composite_score" not in df.columns:
            df = self.compute_raw_composite_score(df)
        else:
            df = df.copy()

        if len(df) == 0:
            df["composite_score"] = pd.Series(dtype=float)
            return df

        min_s = df["raw_composite_score"].min()
        max_s = df["raw_composite_score"].max()

        if max_s == min_s:
            df["composite_score"] = 50.0
        else:
            norm = ((df["raw_composite_score"] - min_s) / (max_s - min_s)) * 100.0
            df["composite_score"] = norm.round(2)

        return df





