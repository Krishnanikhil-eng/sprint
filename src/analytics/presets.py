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

def get_value_pick_preset() -> ScreenerConfig:
    """
    Value Pick Preset:
    Identifies attractively priced businesses with solid margin profiles and modest leverage.
    Criteria:
    - D/E <= 1.0
    - ROE >= 12%
    - Net Profit Margin >= 8%
    - FCF > 0 Cr
    - Book Value per Share > 0
    """
    return ScreenerConfig(
        name="Value Pick",
        description="Low leverage, healthy profit margin, and positive free cash flow value candidates",
        criteria=[
            FilterCriterion("debt_to_equity", FilterOperator.LESS_EQUAL, value=1.0, description="D/E <= 1.0"),
            FilterCriterion("return_on_equity_pct", FilterOperator.GREATER_EQUAL, value=12.0, description="ROE >= 12%"),
            FilterCriterion("net_profit_margin_pct", FilterOperator.GREATER_EQUAL, value=8.0, description="NPM >= 8%"),
            FilterCriterion("free_cash_flow_cr", FilterOperator.GREATER_THAN, value=0.0, description="FCF > 0 Cr"),
            FilterCriterion("book_value_per_share", FilterOperator.GREATER_THAN, value=0.0, description="Book Value > 0")
        ],
        handle_financials_de=True,
        handle_zero_debt_icr=True,
        sort_by="composite_score",
        ascending=False
    )

def get_growth_accelerator_preset() -> ScreenerConfig:
    """
    Growth Accelerator Preset:
    Identifies high-growth compounders expanding both top-line revenue and bottom-line profit.
    Criteria:
    - Revenue 5Yr CAGR >= 10%
    - PAT 5Yr CAGR >= 10%
    - ROE >= 14%
    - OPM >= 10%
    """
    return ScreenerConfig(
        name="Growth Accelerator",
        description="High top-line & bottom-line compounders with expanding profit margins",
        criteria=[
            FilterCriterion("revenue_cagr_5yr", FilterOperator.GREATER_EQUAL, value=10.0, description="Revenue CAGR 5Yr >= 10%"),
            FilterCriterion("pat_cagr_5yr", FilterOperator.GREATER_EQUAL, value=10.0, description="PAT CAGR 5Yr >= 10%"),
            FilterCriterion("return_on_equity_pct", FilterOperator.GREATER_EQUAL, value=14.0, description="ROE >= 14%"),
            FilterCriterion("operating_profit_margin_pct", FilterOperator.GREATER_EQUAL, value=10.0, description="OPM >= 10%")
        ],
        handle_financials_de=True,
        handle_zero_debt_icr=True,
        sort_by="composite_score",
        ascending=False
    )


