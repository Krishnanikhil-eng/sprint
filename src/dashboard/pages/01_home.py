"""
Home Screen - KPI Dashboard
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

from src.dashboard.utils.db import get_latest_ratios_all, get_sectors, get_ratios
from src.dashboard.config import LABEL_NA, SUPPORTED_YEARS, DEFAULT_YEAR

st.header("Home Dashboard")

# Year selector
selected_year = st.selectbox(
    "Select Year",
    options=SUPPORTED_YEARS,
    index=len(SUPPORTED_YEARS) - 1,
    help="Filter metrics by fiscal year"
)

# Load data for selected year
try:
    ratios_df = get_latest_ratios_all(selected_year)
    sectors_df = get_sectors()
except Exception as e:
    st.error(f"Error loading data: {e}")
    st.stop()

if ratios_df.empty:
    st.warning(f"No data available for year {selected_year}. Please select another year.")
    st.stop()

# Calculate KPIs
def safe_median(series):
    """Calculate median handling None/NaN values."""
    if series is None or series.empty:
        return None
    clean_series = series.dropna()
    clean_series = clean_series[np.isfinite(clean_series)]
    if len(clean_series) == 0:
        return None
    return clean_series.median()

def safe_mean(series):
    """Calculate mean handling None/NaN values."""
    if series is None or series.empty:
        return None
    clean_series = series.dropna()
    clean_series = clean_series[np.isfinite(clean_series)]
    if len(clean_series) == 0:
        return None
    return clean_series.mean()

# KPI calculations
avg_roe = safe_mean(ratios_df.get('return_on_equity_pct'))
median_pe = safe_median(ratios_df.get('pe_ratio'))
median_de = safe_median(ratios_df.get('debt_to_equity'))
total_companies = len(ratios_df)
median_revenue_cagr = safe_median(ratios_df.get('revenue_cagr_5yr'))

# Count debt-free companies (D/E < 0.1)
if 'debt_to_equity' in ratios_df.columns:
    debt_free_count = len(ratios_df[ratios_df['debt_to_equity'].dropna() < 0.1])
else:
    debt_free_count = 0

# Display KPIs (6 tiles)
col1, col2, col3 = st.columns(3)
col4, col5, col6 = st.columns(3)

with col1:
    st.metric(
        "Average ROE",
        f"{avg_roe:.2f}%" if avg_roe is not None else LABEL_NA,
        help="Average Return on Equity across companies"
    )

with col2:
    st.metric(
        "Median P/E",
        f"{median_pe:.2f}" if median_pe is not None else LABEL_NA,
        help="Median Price to Earnings ratio"
    )

with col3:
    st.metric(
        "Median D/E",
        f"{median_de:.2f}" if median_de is not None else LABEL_NA,
        help="Median Debt to Equity ratio"
    )

with col4:
    st.metric(
        "Total Companies",
        total_companies,
        help="Total number of companies with data for selected year"
    )

with col5:
    st.metric(
        "Median Revenue CAGR (5yr)",
        f"{median_revenue_cagr:.2f}%" if median_revenue_cagr is not None else LABEL_NA,
        help="Median 5-year revenue compound annual growth rate"
    )

with col6:
    st.metric(
        "Debt-Free Companies",
        debt_free_count,
        help="Companies with D/E < 0.1"
    )

st.markdown("---")

# Sector Breakdown Donut Chart
st.subheader("Sector Breakdown")

if not sectors_df.empty:
    sector_counts = sectors_df['broad_sector'].value_counts().reset_index()
    sector_counts.columns = ['Sector', 'Count']
    
    fig = px.pie(
        sector_counts,
        values='Count',
        names='Sector',
        hole=0.4,
        title='Company Distribution across 11 Sectors'
    )
    fig.update_traces(textposition='inside', textinfo='percent+label')
    fig.update_layout(
        height=450,
        showlegend=True,
        margin=dict(l=20, r=20, t=40, b=20)
    )
    st.plotly_chart(fig, use_container_width=True)
else:
    st.warning("No sector data available")

st.markdown("---")

# Quality Ranking
st.subheader("Top 5 Companies by Quality Score")

if 'composite_quality_score' in ratios_df.columns:
    top_quality = ratios_df.dropna(subset=['composite_quality_score']).nlargest(5, 'composite_quality_score')
    
    if not top_quality.empty:
        for idx, row in top_quality.reset_index().iterrows():
            score = row['composite_quality_score']
            sector_name = row.get('broad_sector', LABEL_NA)
            st.markdown(f"**{idx + 1}. {row['company_name']}** ({sector_name}) — Composite Score: `{score:.2f}`")
    else:
        st.info("No quality scores available for selected year")
else:
    st.info("Quality score data not available")

