"""
Sector Analysis Screen
"""

import streamlit as st
import pandas as pd
import plotly.express as px

from src.dashboard.utils.db import get_latest_ratios_all, get_sectors
from src.dashboard.config import LABEL_NA

st.header("Sector Analysis")

# Load data
try:
    ratios_df = get_latest_ratios_all()
    sectors_df = get_sectors()
except Exception as e:
    st.error(f"Error loading data: {e}")
    st.stop()

if ratios_df.empty or sectors_df.empty:
    st.warning("No data available for sector analysis")
    st.stop()

# Merge ratios with sector info
merged_df = pd.merge(ratios_df, sectors_df, on='company_id', how='left')

# Sector dropdown
available_sectors = sorted(merged_df['broad_sector'].dropna().unique().tolist())
selected_sector = st.selectbox(
    "Select Sector",
    options=available_sectors,
    help="Select a sector for analysis"
)

if not selected_sector:
    st.info("Please select a sector")
    st.stop()

# Filter by selected sector
sector_df = merged_df[merged_df['broad_sector'] == selected_sector].copy()

if sector_df.empty:
    st.warning(f"No data available for sector: {selected_sector}")
    st.stop()

st.info(f"Analyzing {len(sector_df)} companies in {selected_sector}")

# Bubble/scatter chart
st.subheader(f"{selected_sector} - Revenue vs ROE")

# Prepare data for bubble chart
bubble_data = sector_df.copy()

# Get revenue from P&L if available, otherwise use a placeholder
if 'sales' in bubble_data.columns:
    revenue_col = 'sales'
else:
    revenue_col = None

if revenue_col and 'return_on_equity_pct' in bubble_data.columns:
    # Handle missing values
    bubble_data = bubble_data.dropna(subset=[revenue_col, 'return_on_equity_pct'])
    
    if not bubble_data.empty:
        fig = px.scatter(
            bubble_data,
            x=revenue_col,
            y='return_on_equity_pct',
            size='total_debt_cr' if 'total_debt_cr' in bubble_data.columns else None,
            color='sub_sector' if 'sub_sector' in bubble_data.columns else None,
            hover_data=['company_name'],
            title=f"{selected_sector}: Revenue vs ROE",
            labels={
                revenue_col: 'Revenue (Cr)',
                'return_on_equity_pct': 'ROE (%)',
                'sub_sector': 'Sub-Sector'
            }
        )
        fig.update_layout(
            height=500,
            margin=dict(l=20, r=20, t=40, b=20)
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("Insufficient data for bubble chart")
else:
    st.warning("Required columns (Revenue, ROE) not available for bubble chart")
