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

def get_dividend_champion_preset() -> ScreenerConfig:
    """
    Dividend Champion Preset:
    Identifies high dividend payout companies backed by strong cash flow and clean leverage.
    Criteria:
    - Dividend Payout Ratio >= 20%
    - Free Cash Flow > 0 Cr
    - D/E <= 1.0
    - ROE >= 12%
    """
    return ScreenerConfig(
        name="Dividend Champion",
        description="High dividend payout ratio backed by positive free cash flow and low debt",
        criteria=[
            FilterCriterion("dividend_payout_ratio_pct", FilterOperator.GREATER_EQUAL, value=20.0, description="Dividend Payout >= 20%"),
            FilterCriterion("free_cash_flow_cr", FilterOperator.GREATER_THAN, value=0.0, description="FCF > 0 Cr"),
            FilterCriterion("debt_to_equity", FilterOperator.LESS_EQUAL, value=1.0, description="D/E <= 1.0"),
            FilterCriterion("return_on_equity_pct", FilterOperator.GREATER_EQUAL, value=12.0, description="ROE >= 12%")
        ],
        handle_financials_de=True,
        handle_zero_debt_icr=True,
        sort_by="composite_score",
        ascending=False
    )

def get_debt_free_bluechip_preset() -> ScreenerConfig:
    """
    Debt-Free Blue Chip Preset:
    Identifies high-ROE blue chip companies operating with zero or negligible debt.
    Criteria:
    - D/E <= 0.1
    - ROE >= 15%
    - Free Cash Flow > 0 Cr
    - Interest Coverage >= 5.0 (DEBT_FREE exempted)
    """
    return ScreenerConfig(
        name="Debt-Free Blue Chip",
        description="Zero/virtually zero debt, robust ROE, and strong free cash flow generation",
        criteria=[
            FilterCriterion("debt_to_equity", FilterOperator.LESS_EQUAL, value=0.1, description="D/E <= 0.1"),
            FilterCriterion("return_on_equity_pct", FilterOperator.GREATER_EQUAL, value=15.0, description="ROE >= 15%"),
            FilterCriterion("free_cash_flow_cr", FilterOperator.GREATER_THAN, value=0.0, description="FCF > 0 Cr"),
            FilterCriterion("interest_coverage", FilterOperator.GREATER_EQUAL, value=5.0, description="ICR >= 5.0")
        ],
        handle_financials_de=True,
        handle_zero_debt_icr=True,
        sort_by="composite_score",
        ascending=False
    )

def get_turnaround_watch_preset() -> ScreenerConfig:
    """
    Turnaround Watch Preset:
    Identifies recovering companies displaying improving earnings CAGR, positive FCF conversion, and manageable net debt.
    Criteria:
    - PAT 5Yr CAGR >= 5%
    - Free Cash Flow > 0 Cr
    - Net Debt <= 5000 Cr
    - OPM >= 8%
    """
    return ScreenerConfig(
        name="Turnaround Watch",
        description="Operational recovery candidates with positive cash flows and debt deleveraging",
        criteria=[
            FilterCriterion("pat_cagr_5yr", FilterOperator.GREATER_EQUAL, value=5.0, description="PAT CAGR 5Yr >= 5%"),
            FilterCriterion("free_cash_flow_cr", FilterOperator.GREATER_THAN, value=0.0, description="FCF > 0 Cr"),
            FilterCriterion("net_debt_cr", FilterOperator.LESS_EQUAL, value=5000.0, description="Net Debt <= 5000 Cr"),
            FilterCriterion("operating_profit_margin_pct", FilterOperator.GREATER_EQUAL, value=8.0, description="OPM >= 8%")
        ],
        handle_financials_de=True,
        handle_zero_debt_icr=True,
        sort_by="composite_score",
        ascending=False
    )

ALL_PRESETS: Dict[str, ScreenerConfig] = {
    "quality_compounder": get_quality_compounder_preset(),
    "value_pick": get_value_pick_preset(),
    "growth_accelerator": get_growth_accelerator_preset(),
    "dividend_champion": get_dividend_champion_preset(),
    "debt_free_bluechip": get_debt_free_bluechip_preset(),
    "turnaround_watch": get_turnaround_watch_preset()
}





