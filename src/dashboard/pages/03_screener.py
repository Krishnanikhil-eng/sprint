"""
Screener Screen
"""

import streamlit as st
import pandas as pd

from src.dashboard.utils.db import get_latest_ratios_all
from src.dashboard.config import SCREENER_DEFAULTS, LABEL_NA

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

min_roe = st.sidebar.number_input(
    "ROE Minimum (%)",
    value=SCREENER_DEFAULTS['min_roe'],
    min_value=0.0,
    max_value=100.0,
    step=0.5,
    help="Minimum Return on Equity percentage"
)

max_de = st.sidebar.number_input(
    "D/E Maximum",
    value=SCREENER_DEFAULTS['max_de'],
    min_value=0.0,
    max_value=50.0,
    step=0.1,
    help="Maximum Debt to Equity ratio"
)

min_fcf = st.sidebar.number_input(
    "FCF Minimum (Cr)",
    value=SCREENER_DEFAULTS['min_fcf'],
    min_value=0.0,
    max_value=10000.0,
    step=10.0,
    help="Minimum Free Cash Flow in Crores"
)

min_revenue_cagr = st.sidebar.number_input(
    "Revenue CAGR Minimum (%)",
    value=SCREENER_DEFAULTS['min_revenue_cagr'],
    min_value=-50.0,
    max_value=100.0,
    step=1.0,
    help="Minimum 5-year Revenue CAGR percentage"
)

min_pat_cagr = st.sidebar.number_input(
    "PAT CAGR Minimum (%)",
    value=SCREENER_DEFAULTS['min_pat_cagr'],
    min_value=-50.0,
    max_value=100.0,
    step=1.0,
    help="Minimum 5-year PAT CAGR percentage"
)

min_opm = st.sidebar.number_input(
    "OPM Minimum (%)",
    value=SCREENER_DEFAULTS['min_opm'],
    min_value=0.0,
    max_value=100.0,
    step=0.5,
    help="Minimum Operating Profit Margin percentage"
)

max_pe = st.sidebar.number_input(
    "P/E Maximum",
    value=SCREENER_DEFAULTS['max_pe'],
    min_value=0.0,
    max_value=1000.0,
    step=1.0,
    help="Maximum Price to Earnings ratio"
)

max_pb = st.sidebar.number_input(
    "P/B Maximum",
    value=SCREENER_DEFAULTS['max_pb'],
    min_value=0.0,
    max_value=100.0,
    step=0.5,
    help="Maximum Price to Book ratio"
)

min_dividend_yield = st.sidebar.number_input(
    "Dividend Yield Minimum (%)",
    value=SCREENER_DEFAULTS['min_dividend_yield'],
    min_value=0.0,
    max_value=20.0,
    step=0.1,
    help="Minimum Dividend Yield percentage"
)

min_icr = st.sidebar.number_input(
    "ICR Minimum",
    value=SCREENER_DEFAULTS['min_icr'],
    min_value=0.0,
    max_value=50.0,
    step=0.5,
    help="Minimum Interest Coverage Ratio"
)

# Apply filters
filtered_df = ratios_df.copy()

if 'return_on_equity_pct' in filtered_df.columns:
    filtered_df = filtered_df[filtered_df['return_on_equity_pct'] >= min_roe]

if 'debt_to_equity' in filtered_df.columns:
    filtered_df = filtered_df[filtered_df['debt_to_equity'] <= max_de]

if 'free_cash_flow_cr' in filtered_df.columns:
    filtered_df = filtered_df[filtered_df['free_cash_flow_cr'] >= min_fcf]

if 'revenue_cagr_5yr' in filtered_df.columns:
    filtered_df = filtered_df[filtered_df['revenue_cagr_5yr'] >= min_revenue_cagr]

if 'pat_cagr_5yr' in filtered_df.columns:
    filtered_df = filtered_df[filtered_df['pat_cagr_5yr'] >= min_pat_cagr]

if 'operating_profit_margin_pct' in filtered_df.columns:
    filtered_df = filtered_df[filtered_df['operating_profit_margin_pct'] >= min_opm]

if 'net_profit_margin_pct' in filtered_df.columns:
    filtered_df = filtered_df[filtered_df['net_profit_margin_pct'] >= min_opm]

if 'interest_coverage' in filtered_df.columns:
    filtered_df = filtered_df[filtered_df['interest_coverage'] >= min_icr]

# Display results count
st.info(f"{len(filtered_df)} companies match your filters")
