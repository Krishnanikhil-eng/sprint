"""
Sector Analysis Screen
"""

import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
from pathlib import Path

from src.dashboard.utils.db import get_latest_ratios_all, get_sectors, get_connection
from src.dashboard.config import LABEL_NA

st.header("Sector Analysis")

# Load latest ratios, sectors, and sales revenue
try:
    ratios_df = get_latest_ratios_all()
    sectors_df = get_sectors()
    
    # Fetch latest sales revenue from profitandloss
    conn = get_connection()
    try:
        pl_query = """
        WITH LatestPL AS (
            SELECT company_id, sales,
                   ROW_NUMBER() OVER (PARTITION BY company_id ORDER BY year DESC) as rn
            FROM profitandloss
        )
        SELECT company_id, sales FROM LatestPL WHERE rn = 1
        """
        pl_df = pd.read_sql_query(pl_query, conn)
    finally:
        conn.close()
        
    merged_df = pd.merge(ratios_df, pl_df, on='company_id', how='left')
except Exception as e:
    st.error(f"Error loading data for sector analysis: {e}")
    st.stop()

if merged_df.empty or sectors_df.empty:
    st.warning("No data available for sector analysis")
    st.stop()

# Sector dropdown
available_sectors = sorted(merged_df['broad_sector'].dropna().unique().tolist())
selected_sector = st.selectbox(
    "Select Sector",
    options=available_sectors,
    help="Select a sector for comparative bubble chart & median analysis"
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

# Bubble chart: X = Revenue, Y = ROE, Bubble size = Market Cap, Colour = sub-sector
st.subheader(f"{selected_sector} — Revenue vs ROE (Bubble Size = Market Cap)")

bubble_data = sector_df.dropna(subset=['sales', 'return_on_equity_pct']).copy()
bubble_data['sales'] = pd.to_numeric(bubble_data['sales'], errors='coerce')
bubble_data['return_on_equity_pct'] = pd.to_numeric(bubble_data['return_on_equity_pct'], errors='coerce')

# Ensure positive market cap for bubble sizing
if 'market_cap_crore' in bubble_data.columns:
    bubble_data['market_cap_size'] = pd.to_numeric(bubble_data['market_cap_crore'], errors='coerce').fillna(1000.0)
    bubble_data['market_cap_size'] = bubble_data['market_cap_size'].apply(lambda x: max(100.0, float(x)))
else:
    bubble_data['market_cap_size'] = 1000.0

if not bubble_data.empty:
    fig = px.scatter(
        bubble_data,
        x='sales',
        y='return_on_equity_pct',
        size='market_cap_size',
        color='sub_sector' if 'sub_sector' in bubble_data.columns else None,
        hover_name='company_name',
        hover_data=['company_id', 'market_cap_crore', 'pe_ratio'],
        title=f"{selected_sector}: Revenue vs ROE",
        labels={
            'sales': 'Revenue (₹ Cr)',
            'return_on_equity_pct': 'ROE (%)',
            'sub_sector': 'Sub-Sector',
            'market_cap_size': 'Market Cap'
        }
    )
    fig.update_layout(
        height=500,
        margin=dict(l=20, r=20, t=40, b=20)
    )
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("Insufficient data to render bubble chart for this sector")

st.markdown("---")

# Sector median KPIs bar chart
st.subheader(f"{selected_sector} — Sector Median KPIs")

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
    median_values = {}
    for metric in available_kpis:
        val_series = pd.to_numeric(sector_df[metric], errors='coerce').dropna()
        if not val_series.empty:
            median_values[kpi_labels.get(metric, metric)] = float(val_series.median())
    
    if median_values:
        median_df = pd.DataFrame(list(median_values.items()), columns=['KPI', 'Median Value'])
        
        fig2 = px.bar(
            median_df,
            x='KPI',
            y='Median Value',
            title=f"{selected_sector} Median Performance Indicators",
            color='Median Value',
            color_continuous_scale='Viridis',
            labels={'Median Value': 'Median Value', 'KPI': 'Indicator'}
        )
        fig2.update_layout(
            height=400,
            margin=dict(l=20, r=20, t=40, b=20)
        )
        st.plotly_chart(fig2, use_container_width=True)
    else:
        st.info("No valid KPI data available for median calculation")
else:
    st.info("No KPI metrics available for sector analysis")

