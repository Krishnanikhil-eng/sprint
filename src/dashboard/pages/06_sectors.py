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

# Sector median KPIs bar chart
st.subheader(f"{selected_sector} - Median KPIs")

kpi_metrics = [
    'return_on_equity_pct',
    'roce_pct',
    'debt_to_equity',
    'net_profit_margin_pct',
    'operating_profit_margin_pct',
    'revenue_cagr_5yr',
    'pat_cagr_5yr'
]

kpi_labels = {
    'return_on_equity_pct': 'ROE (%)',
    'roce_pct': 'ROCE (%)',
    'debt_to_equity': 'D/E',
    'net_profit_margin_pct': 'NPM (%)',
    'operating_profit_margin_pct': 'OPM (%)',
    'revenue_cagr_5yr': 'Rev CAGR (%)',
    'pat_cagr_5yr': 'PAT CAGR (%)'
}

available_kpis = [m for m in kpi_metrics if m in sector_df.columns]

if available_kpis:
    # Calculate medians
    median_values = {}
    for metric in available_kpis:
        median_val = sector_df[metric].median()
        median_values[kpi_labels.get(metric, metric)] = median_val
    
    # Create bar chart
    median_df = pd.DataFrame(list(median_values.items()), columns=['KPI', 'Median'])
    median_df = median_df.dropna(subset=['Median'])
    
    if not median_df.empty:
        fig = px.bar(
            median_df,
            x='KPI',
            y='Median',
            title=f"{selected_sector} - Median KPIs",
            labels={'Median': 'Median Value', 'KPI': 'Key Performance Indicator'}
        )
        fig.update_layout(
            height=400,
            margin=dict(l=20, r=20, t=40, b=20)
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("No median data available")
else:
    st.warning("No KPI metrics available for sector analysis")
