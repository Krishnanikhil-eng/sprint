"""
Home Screen - KPI Dashboard
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

from src.dashboard.utils.db import get_latest_ratios_all, get_sectors
from src.dashboard.config import LABEL_NA

st.header("Home Dashboard")

# Load data
try:
    ratios_df = get_latest_ratios_all()
    sectors_df = get_sectors()
except Exception as e:
    st.error(f"Error loading data: {e}")
    st.stop()

if ratios_df.empty:
    st.warning("No data available. Please ensure the database is populated.")
    st.stop()

# Calculate KPIs
def safe_median(series):
    """Calculate median handling None/NaN values."""
    clean_series = series.dropna()
    if len(clean_series) == 0:
        return None
    return clean_series.median()

def safe_mean(series):
    """Calculate mean handling None/NaN values."""
    clean_series = series.dropna()
    if len(clean_series) == 0:
        return None
    return clean_series.mean()

# KPI calculations
avg_roe = safe_mean(ratios_df['return_on_equity_pct'])
median_pe = safe_median(ratios_df['debt_to_equity'])  # Using D/E as placeholder until market_cap loaded
median_de = safe_median(ratios_df['debt_to_equity'])
total_companies = len(ratios_df)
median_revenue_cagr = safe_median(ratios_df['revenue_cagr_5yr'])

# Count debt-free companies (D/E < 0.1)
debt_free_count = len(ratios_df[ratios_df['debt_to_equity'] < 0.1])

# Display KPIs
col1, col2, col3, col4 = st.columns(4)
col5, col6 = st.columns(2)

with col1:
    st.metric(
        "Average ROE",
        f"{avg_roe:.2f}%" if avg_roe is not None else LABEL_NA,
        help="Average Return on Equity across all companies"
    )

with col2:
    st.metric(
        "Median D/E",
        f"{median_de:.2f}" if median_de is not None else LABEL_NA,
        help="Median Debt to Equity ratio"
    )

with col3:
    st.metric(
        "Total Companies",
        total_companies,
        help="Total number of companies in database"
    )

with col4:
    st.metric(
        "Median Revenue CAGR (5yr)",
        f"{median_revenue_cagr:.2f}%" if median_revenue_cagr is not None else LABEL_NA,
        help="Median 5-year revenue compound annual growth rate"
    )

with col5:
    st.metric(
        "Debt-Free Companies",
        debt_free_count,
        help="Companies with D/E < 0.1"
    )

with col6:
    st.metric(
        "Median P/E",
        LABEL_NA,  # Will be updated when market_cap data integrated
        help="Median Price to Earnings ratio (pending market cap integration)"
    )

st.markdown("---")

# Sector Breakdown Chart
st.subheader("Sector Breakdown")

if not sectors_df.empty:
    sector_counts = sectors_df['broad_sector'].value_counts().reset_index()
    sector_counts.columns = ['Sector', 'Count']
    
    fig = px.pie(
        sector_counts,
        values='Count',
        names='Sector',
        hole=0.4,
        title='Company Distribution by Sector'
    )
    fig.update_traces(textposition='inside', textinfo='percent+label')
    fig.update_layout(
        height=400,
        showlegend=True,
        margin=dict(l=20, r=20, t=40, b=20)
    )
    st.plotly_chart(fig, use_container_width=True)
else:
    st.warning("No sector data available")
