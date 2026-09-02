"""
Screener Presets Module.
Provides pre-configured institutional screening presets for Nifty 100 stocks.
"""

from typing import Dict
from src.analytics.screener_config import ScreenerConfig, FilterCriterion, FilterOperator

def get_quality_compounder_preset() -> ScreenerConfig:
    """
    Quality Compounder Preset:
    Identifies high-ROCE, high-ROE businesses with strong cash conversion and clean balance sheets.
    Criteria:
    - ROE >= 15%
    - ROCE >= 15%
    - D/E <= 0.5 (Financials sector exempted)
    - Free Cash Flow > 0 Cr
    - 5-Year Revenue CAGR >= 8%
    """
    return ScreenerConfig(
        name="Quality Compounder",
        description="High capital return, low debt, and positive free cash flow compounders",
        criteria=[
            FilterCriterion("return_on_equity_pct", FilterOperator.GREATER_EQUAL, value=15.0, description="ROE >= 15%"),
            FilterCriterion("roce_pct", FilterOperator.GREATER_EQUAL, value=15.0, description="ROCE >= 15%"),
            FilterCriterion("debt_to_equity", FilterOperator.LESS_EQUAL, value=0.5, description="D/E <= 0.5"),
            FilterCriterion("free_cash_flow_cr", FilterOperator.GREATER_THAN, value=0.0, description="FCF > 0 Cr"),
            FilterCriterion("revenue_cagr_5yr", FilterOperator.GREATER_EQUAL, value=8.0, description="Revenue CAGR 5Yr >= 8%")
        ],
        handle_financials_de=True,
        handle_zero_debt_icr=True,
        sort_by="composite_score",
        ascending=False
    )
