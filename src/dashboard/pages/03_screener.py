"""
Stock Screener Screen
"""

import streamlit as st
import pandas as pd

from src.dashboard.utils.db import get_latest_ratios_all
from src.dashboard.config import SCREENER_DEFAULTS, PRESET_STRATEGIES

st.header("Stock Screener")

# Load data
try:
    ratios_df = get_latest_ratios_all()
except Exception as e:
    st.error(f"Error loading data: {e}")
    st.stop()

if ratios_df.empty:
    st.warning("No data available for screening")
    st.stop()

# Sidebar filters
st.sidebar.header("Filter Criteria")

# Initialize session state for filters if not present
filter_keys = [
    "min_roe",
    "max_de",
    "min_fcf",
    "min_revenue_cagr",
    "min_pat_cagr",
    "min_opm",
    "max_pe",
    "max_pb",
    "min_dividend_yield",
    "min_icr",
]

for key in filter_keys:
    if f"filter_{key}" not in st.session_state:
        st.session_state[f"filter_{key}"] = SCREENER_DEFAULTS.get(key, 0.0)


# Preset strategy handler
def apply_preset():
    selected_preset = st.session_state.preset_selector
    if selected_preset in PRESET_STRATEGIES:
        preset_dict = PRESET_STRATEGIES[selected_preset]
        for key in filter_keys:
            if key in preset_dict:
                st.session_state[f"filter_{key}"] = float(preset_dict[key])
            else:
                st.session_state[f"filter_{key}"] = float(
                    SCREENER_DEFAULTS.get(key, 0.0)
                )


# Preset selector dropdown
st.sidebar.subheader("Preset Strategies")
st.sidebar.selectbox(
    "Select a preset strategy",
    options=["Custom"] + list(PRESET_STRATEGIES.keys()),
    key="preset_selector",
    on_change=apply_preset,
    help="Pre-defined filter combinations for quick stock screening",
)

st.sidebar.markdown("---")

# 10 Filter Inputs
min_roe = st.sidebar.number_input(
    "ROE Minimum (%)",
    min_value=-50.0,
    max_value=100.0,
    step=0.5,
    key="filter_min_roe",
    help="Minimum Return on Equity percentage",
)

max_de = st.sidebar.number_input(
    "D/E Maximum",
    min_value=0.0,
    max_value=50.0,
    step=0.1,
    key="filter_max_de",
    help="Maximum Debt to Equity ratio",
)

min_fcf = st.sidebar.number_input(
    "FCF Minimum (Cr)",
    min_value=-50000.0,
    max_value=100000.0,
    step=10.0,
    key="filter_min_fcf",
    help="Minimum Free Cash Flow in Crores",
)

min_revenue_cagr = st.sidebar.number_input(
    "Revenue CAGR Minimum (%)",
    min_value=-50.0,
    max_value=100.0,
    step=1.0,
    key="filter_min_revenue_cagr",
    help="Minimum 5-year Revenue CAGR percentage",
)

min_pat_cagr = st.sidebar.number_input(
    "PAT CAGR Minimum (%)",
    min_value=-50.0,
    max_value=100.0,
    step=1.0,
    key="filter_min_pat_cagr",
    help="Minimum 5-year PAT CAGR percentage",
)

min_opm = st.sidebar.number_input(
    "OPM Minimum (%)",
    min_value=-50.0,
    max_value=100.0,
    step=0.5,
    key="filter_min_opm",
    help="Minimum Operating Profit Margin percentage",
)

max_pe = st.sidebar.number_input(
    "P/E Maximum",
    min_value=0.0,
    max_value=1000.0,
    step=1.0,
    key="filter_max_pe",
    help="Maximum Price to Earnings ratio",
)

max_pb = st.sidebar.number_input(
    "P/B Maximum",
    min_value=0.0,
    max_value=100.0,
    step=0.5,
    key="filter_max_pb",
    help="Maximum Price to Book ratio",
)

min_dividend_yield = st.sidebar.number_input(
    "Dividend Yield Minimum (%)",
    min_value=0.0,
    max_value=20.0,
    step=0.1,
    key="filter_min_dividend_yield",
    help="Minimum Dividend Yield percentage",
)

min_icr = st.sidebar.number_input(
    "ICR Minimum",
    min_value=0.0,
    max_value=100.0,
    step=0.5,
    key="filter_min_icr",
    help="Minimum Interest Coverage Ratio",
)

# Apply filters dynamically
filtered_df = ratios_df.copy()

if "return_on_equity_pct" in filtered_df.columns:
    filtered_df = filtered_df[
        filtered_df["return_on_equity_pct"].fillna(-999) >= min_roe
    ]

if "debt_to_equity" in filtered_df.columns:
    filtered_df = filtered_df[filtered_df["debt_to_equity"].fillna(999) <= max_de]

if "free_cash_flow_cr" in filtered_df.columns:
    filtered_df = filtered_df[
        filtered_df["free_cash_flow_cr"].fillna(-99999) >= min_fcf
    ]

if "revenue_cagr_5yr" in filtered_df.columns:
    filtered_df = filtered_df[
        filtered_df["revenue_cagr_5yr"].fillna(-999) >= min_revenue_cagr
    ]

if "pat_cagr_5yr" in filtered_df.columns:
    filtered_df = filtered_df[filtered_df["pat_cagr_5yr"].fillna(-999) >= min_pat_cagr]

if "operating_profit_margin_pct" in filtered_df.columns:
    filtered_df = filtered_df[
        filtered_df["operating_profit_margin_pct"].fillna(-999) >= min_opm
    ]

if "pe_ratio" in filtered_df.columns and max_pe < 1000.0:
    filtered_df = filtered_df[filtered_df["pe_ratio"].fillna(9999) <= max_pe]

if "pb_ratio" in filtered_df.columns and max_pb < 100.0:
    filtered_df = filtered_df[filtered_df["pb_ratio"].fillna(9999) <= max_pb]

if "dividend_yield_pct" in filtered_df.columns:
    filtered_df = filtered_df[
        filtered_df["dividend_yield_pct"].fillna(0) >= min_dividend_yield
    ]

if "interest_coverage" in filtered_df.columns:
    filtered_df = filtered_df[filtered_df["interest_coverage"].fillna(0) >= min_icr]

# Display results count
st.info(f"{len(filtered_df)} companies match your filters")

# Results table
if not filtered_df.empty:
    display_cols = [
        "company_id",
        "company_name",
        "broad_sector",
        "composite_quality_score",
        "return_on_equity_pct",
        "debt_to_equity",
        "pe_ratio",
        "pb_ratio",
        "dividend_yield_pct",
        "free_cash_flow_cr",
        "revenue_cagr_5yr",
        "pat_cagr_5yr",
        "operating_profit_margin_pct",
        "interest_coverage",
    ]

    available_cols = [col for col in display_cols if col in filtered_df.columns]
    results_df = filtered_df[available_cols].copy()

    # Format columns for display
    numeric_cols = [
        "composite_quality_score",
        "return_on_equity_pct",
        "debt_to_equity",
        "pe_ratio",
        "pb_ratio",
        "dividend_yield_pct",
        "free_cash_flow_cr",
        "revenue_cagr_5yr",
        "pat_cagr_5yr",
        "operating_profit_margin_pct",
        "interest_coverage",
    ]
    for col in numeric_cols:
        if col in results_df.columns:
            results_df[col] = pd.to_numeric(results_df[col], errors="coerce").round(2)

    # Column rename mapping
    column_rename = {
        "company_id": "Company ID",
        "company_name": "Company Name",
        "broad_sector": "Sector",
        "composite_quality_score": "Composite Score",
        "return_on_equity_pct": "ROE (%)",
        "debt_to_equity": "D/E",
        "pe_ratio": "P/E",
        "pb_ratio": "P/B",
        "dividend_yield_pct": "Div Yield (%)",
        "free_cash_flow_cr": "FCF (Cr)",
        "revenue_cagr_5yr": "Rev CAGR 5Y (%)",
        "pat_cagr_5yr": "PAT CAGR 5Y (%)",
        "operating_profit_margin_pct": "OPM (%)",
        "interest_coverage": "ICR",
    }
    results_df = results_df.rename(columns=column_rename)

    st.dataframe(results_df.fillna("N/A"), use_container_width=True, height=450)

    # CSV Export
    csv_data = results_df.to_csv(index=False)
    st.download_button(
        label="Download Filtered Results (CSV)",
        data=csv_data,
        file_name="screener_results.csv",
        mime="text/csv",
        help="Download currently filtered stock screener results as a CSV file",
    )
else:
    st.warning(
        "No companies match your current filters. Try relaxing criteria or choosing a preset."
    )
