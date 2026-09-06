"""
Screener Screen
"""

import streamlit as st
import pandas as pd

from src.dashboard.utils.db import get_latest_ratios_all
from src.dashboard.config import SCREENER_DEFAULTS, LABEL_NA, PRESET_STRATEGIES

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

# Preset strategies
st.sidebar.subheader("Preset Strategies")
preset = st.sidebar.selectbox(
    "Select a preset strategy",
    options=["Custom"] + list(PRESET_STRATEGIES.keys()),
    index=0,
    help="Pre-defined filter combinations"
)

if preset != "Custom":
    preset_values = PRESET_STRATEGIES[preset]
    if 'min_roe' in preset_values:
        min_roe = preset_values['min_roe']
    if 'max_de' in preset_values:
        max_de = preset_values['max_de']
    if 'min_opm' in preset_values:
        min_opm = preset_values['min_opm']
    if 'max_pe' in preset_values:
        max_pe = preset_values['max_pe']
    if 'max_pb' in preset_values:
        max_pb = preset_values['max_pb']
    if 'min_dividend_yield' in preset_values:
        min_dividend_yield = preset_values['min_dividend_yield']
    if 'min_revenue_cagr' in preset_values:
        min_revenue_cagr = preset_values['min_revenue_cagr']
    if 'min_pat_cagr' in preset_values:
        min_pat_cagr = preset_values['min_pat_cagr']
    if 'min_fcf' in preset_values:
        min_fcf = preset_values['min_fcf']
    
    st.sidebar.info(f"Applied preset: {preset}")

st.sidebar.markdown("---")

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

# Filter validation
validation_errors = []

if min_revenue_cagr > min_pat_cagr:
    validation_errors.append("Revenue CAGR minimum cannot be greater than PAT CAGR minimum")

if max_de < 0:
    validation_errors.append("D/E maximum cannot be negative")

if min_roe < 0:
    validation_errors.append("ROE minimum cannot be negative")

if max_pe < 0:
    validation_errors.append("P/E maximum cannot be negative")

if max_pb < 0:
    validation_errors.append("P/B maximum cannot be negative")

if validation_errors:
    st.error("Filter Validation Errors:")
    for error in validation_errors:
        st.error(f"• {error}")
    st.stop()

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

# Results table
if not filtered_df.empty:
    display_cols = [
        'company_id',
        'company_name',
        'broad_sector',
        'composite_quality_score',
        'return_on_equity_pct',
        'debt_to_equity',
        'free_cash_flow_cr',
        'revenue_cagr_5yr',
        'pat_cagr_5yr',
        'operating_profit_margin_pct',
        'interest_coverage'
    ]
    
    available_cols = [col for col in display_cols if col in filtered_df.columns]
    results_df = filtered_df[available_cols].copy()
    
    # Format columns for display
    if 'composite_quality_score' in results_df.columns:
        results_df['composite_quality_score'] = results_df['composite_quality_score'].round(2)
    if 'return_on_equity_pct' in results_df.columns:
        results_df['return_on_equity_pct'] = results_df['return_on_equity_pct'].round(2)
    if 'debt_to_equity' in results_df.columns:
        results_df['debt_to_equity'] = results_df['debt_to_equity'].round(2)
    if 'free_cash_flow_cr' in results_df.columns:
        results_df['free_cash_flow_cr'] = results_df['free_cash_flow_cr'].round(2)
    if 'revenue_cagr_5yr' in results_df.columns:
        results_df['revenue_cagr_5yr'] = results_df['revenue_cagr_5yr'].round(2)
    if 'pat_cagr_5yr' in results_df.columns:
        results_df['pat_cagr_5yr'] = results_df['pat_cagr_5yr'].round(2)
    if 'operating_profit_margin_pct' in results_df.columns:
        results_df['operating_profit_margin_pct'] = results_df['operating_profit_margin_pct'].round(2)
    if 'interest_coverage' in results_df.columns:
        results_df['interest_coverage'] = results_df['interest_coverage'].round(2)
    
    # Rename columns for display
    column_rename = {
        'company_id': 'ID',
        'company_name': 'Company',
        'broad_sector': 'Sector',
        'composite_quality_score': 'Quality Score',
        'return_on_equity_pct': 'ROE (%)',
        'debt_to_equity': 'D/E',
        'free_cash_flow_cr': 'FCF (Cr)',
        'revenue_cagr_5yr': 'Rev CAGR 5Y (%)',
        'pat_cagr_5yr': 'PAT CAGR 5Y (%)',
        'operating_profit_margin_pct': 'OPM (%)',
        'interest_coverage': 'ICR'
    }
    results_df = results_df.rename(columns=column_rename)
    
    st.dataframe(results_df, use_container_width=True, height=400)
else:
    st.warning("No companies match your current filters. Try adjusting the criteria.")
