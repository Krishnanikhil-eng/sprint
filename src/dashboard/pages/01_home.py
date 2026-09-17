"""
Home Screen - Executive Overview
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

from src.dashboard.utils.db import get_latest_ratios_all, get_sectors, get_companies
from src.dashboard.utils.ui import (
    format_percentage, 
    format_ratio, 
    format_currency,
    render_simulated_warning,
    safe_render
)
from src.dashboard.config import SUPPORTED_YEARS, LABEL_NA

st.title("Executive Overview")
st.markdown("NIFTY 100 Financial Analytics & Intelligence Platform")

# Year selector
selected_year = st.selectbox(
    "Financial Period",
    options=SUPPORTED_YEARS,
    index=len(SUPPORTED_YEARS) - 1,
    help="Filter aggregate metrics by fiscal year"
)

st.markdown("---")

@safe_render()
def render_dashboard():
    # Load Data
    ratios_df = get_latest_ratios_all(selected_year)
    sectors_df = get_sectors()
    companies_df = get_companies()
    
    if ratios_df.empty:
        st.warning(f"No financial ratio data available for FY{selected_year}.")
        return

    # Section A: Platform Overview
    st.subheader("Platform Coverage")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Companies", len(companies_df))
    with col2:
        st.metric("Sectors Covered", sectors_df['broad_sector'].nunique() if not sectors_df.empty else 0)
    with col3:
        st.metric("Peer Groups", 56) # From spec/existing DB
    with col4:
        st.metric("Active Financial Period", f"FY{selected_year}")

    st.markdown("---")

    # Metrics Calculations
    def safe_median(series):
        if series is None or series.empty: return None
        clean = series.dropna()
        clean = clean[np.isfinite(clean)]
        return clean.median() if len(clean) > 0 else None

    # Section C & D & E: Financial Snapshots
    st.subheader(f"Financial Health Snapshot (FY{selected_year})")
    
    snap1, snap2, snap3 = st.columns(3)
    
    with snap1:
        st.markdown("### Profitability")
        med_roe = safe_median(ratios_df.get("return_on_equity_pct"))
        med_roce = safe_median(ratios_df.get("roce_pct"))
        med_npm = safe_median(ratios_df.get("net_profit_margin_pct"))
        
        st.metric("Median ROE", format_percentage(med_roe))
        st.metric("Median ROCE", format_percentage(med_roce))
        st.metric("Median Net Profit Margin", format_percentage(med_npm))

    with snap2:
        st.markdown("### Growth & Valuation")
        render_simulated_warning()
        
        med_rev_cagr = safe_median(ratios_df.get("revenue_cagr_5yr"))
        med_pe = safe_median(ratios_df.get("pe_ratio"))
        total_mc = ratios_df.get("market_cap_crore").sum() if "market_cap_crore" in ratios_df else 0
        
        st.metric("Median 5Yr Revenue CAGR", format_percentage(med_rev_cagr))
        st.metric("Median P/E Ratio", format_ratio(med_pe, "x"))
        st.metric("Total Market Cap", format_currency(total_mc))

    with snap3:
        st.markdown("### Leverage & Efficiency")
        med_de = safe_median(ratios_df.get("debt_to_equity"))
        med_ic = safe_median(ratios_df.get("interest_coverage"))
        
        if "debt_to_equity" in ratios_df.columns:
            debt_free = (ratios_df["debt_to_equity"] < 0.1).sum()
        else:
            debt_free = 0
            
        st.metric("Median D/E Ratio", format_ratio(med_de, "x"))
        st.metric("Median Interest Coverage", format_ratio(med_ic, "x"))
        st.metric("Debt-Free Companies (D/E < 0.1)", debt_free)

    st.markdown("---")

    # Section B: Sector Distribution
    st.subheader("Sector Distribution")
    if not sectors_df.empty:
        sector_counts = sectors_df["broad_sector"].value_counts().reset_index()
        sector_counts.columns = ["Sector", "Count"]

        fig = px.pie(
            sector_counts,
            values="Count",
            names="Sector",
            hole=0.4,
            color_discrete_sequence=px.colors.qualitative.Prism
        )
        fig.update_traces(textposition="inside", textinfo="percent+label")
        fig.update_layout(height=450, showlegend=False, margin=dict(l=20, r=20, t=20, b=20))
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Sector data is unavailable.")

    st.markdown("---")

    # Quality Highlights
    st.subheader("Top Rated Companies by Composite Quality")
    if "composite_quality_score" in ratios_df.columns:
        top_quality = ratios_df.dropna(subset=["composite_quality_score"]).nlargest(10, "composite_quality_score")
        if not top_quality.empty:
            display_cols = ["company_name", "broad_sector", "composite_quality_score", "return_on_equity_pct", "debt_to_equity"]
            
            # Use safe get to handle missing columns gracefully
            available_cols = [c for c in display_cols if c in top_quality.columns]
            
            view_df = top_quality[available_cols].copy()
            view_df.columns = [c.replace("_", " ").title() for c in view_df.columns]
            
            st.dataframe(
                view_df,
                use_container_width=True,
                hide_index=True
            )
        else:
            st.info("No quality scores available.")
    else:
        st.info("Quality score data is currently unavailable.")

# Execute safe render
render_dashboard()
