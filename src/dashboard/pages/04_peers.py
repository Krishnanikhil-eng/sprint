"""
Peer Comparison Screen
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go

from src.dashboard.utils.db import get_companies, get_sectors, get_peers
from src.dashboard.config import LABEL_NA

st.header("Peer Comparison")

# Load data
try:
    companies_df = get_companies()
    sectors_df = get_sectors()
except Exception as e:
    st.error(f"Error loading data: {e}")
    st.stop()

if companies_df.empty:
    st.warning("No companies available")
    st.stop()

# Get unique peer groups (11 broad sectors)
if not sectors_df.empty:
    peer_groups = sorted(sectors_df['broad_sector'].dropna().unique().tolist())
else:
    peer_groups = []

# Peer group dropdown
selected_group = st.selectbox(
    "Select Peer Group",
    options=peer_groups,
    help="Select a sector/peer group for comparison"
)

if not selected_group:
    st.info("Please select a peer group")
    st.stop()

# Load peer data
try:
    peer_data = get_peers(selected_group)
except Exception as e:
    st.error(f"Error loading peer data: {e}")
    peer_data = pd.DataFrame()

if peer_data.empty:
    st.warning(f"No data available for peer group: {selected_group}")
    st.stop()

st.info(f"Found {len(peer_data)} companies in {selected_group} peer group")

# Select benchmark company
company_options = ["Select a company..."] + sorted(peer_data['company_name'].tolist())
selected_company = st.selectbox(
    "Select Benchmark Company",
    options=company_options,
    index=0,
    help="Select a company to compare against peer group average"
)

# Prepare peer comparison data
def prepare_peer_data(peer_df, selected_company_name):
    """Prepare data for peer comparison with benchmark handling."""
    if peer_df.empty:
        return None, None, None
    
    # Get benchmark company data
    if selected_company_name and selected_company_name != "Select a company...":
        benchmark = peer_df[peer_df['company_name'] == selected_company_name]
        if benchmark.empty:
            return None, None, None
        benchmark_data = benchmark.iloc[0]
    else:
        # Use first company as default benchmark
        benchmark_data = peer_df.iloc[0]
    
    # Calculate peer group averages (excluding benchmark)
    peers_excluding_benchmark = peer_df[peer_df['company_name'] != benchmark_data['company_name']]
    
    if peers_excluding_benchmark.empty:
        peer_avg = benchmark_data
    else:
        peer_avg = peers_excluding_benchmark.mean(numeric_only=True)
    
    # Select key metrics for comparison
    key_metrics = [
        'return_on_equity_pct',
        'roce_pct',
        'debt_to_equity',
        'net_profit_margin_pct',
        'operating_profit_margin_pct',
        'asset_turnover',
        'free_cash_flow_cr',
        'revenue_cagr_5yr'
    ]
    
    # Get benchmark values
    benchmark_values = {}
    for metric in key_metrics:
        val = benchmark_data.get(metric)
        benchmark_values[metric] = val if pd.notna(val) else 0
    
    # Get peer average values
    peer_avg_values = {}
    for metric in key_metrics:
        val = peer_avg.get(metric)
        peer_avg_values[metric] = val if pd.notna(val) else 0
    
    return benchmark_data, peer_avg_values, benchmark_values

benchmark_data, peer_avg_values, benchmark_values = prepare_peer_data(peer_data, selected_company)

# Radar chart comparison
if benchmark_data is not None and peer_avg_values is not None:
    st.subheader("Radar Chart Comparison")
    
    metric_labels = [
        'ROE', 'ROCE', 'D/E', 'NPM', 
        'OPM', 'Asset Turnover', 'FCF', 'Rev CAGR'
    ]
    
    # Normalize values for radar chart (0-100 scale)
    def normalize_for_radar(value, metric_name):
        """Normalize metric values for radar chart display."""
        if metric_name in ['D/E']:
            # Lower is better for D/E, invert
            return max(0, 100 - min(value * 20, 100))
        else:
            # Higher is better
            return max(0, min(value, 100))
    
    benchmark_radar = [
        normalize_for_radar(benchmark_values.get('return_on_equity_pct', 0), 'ROE'),
        normalize_for_radar(benchmark_values.get('roce_pct', 0), 'ROCE'),
        normalize_for_radar(benchmark_values.get('debt_to_equity', 0), 'D/E'),
        normalize_for_radar(benchmark_values.get('net_profit_margin_pct', 0), 'NPM'),
        normalize_for_radar(benchmark_values.get('operating_profit_margin_pct', 0), 'OPM'),
        normalize_for_radar(benchmark_values.get('asset_turnover', 0), 'Asset Turnover'),
        normalize_for_radar(benchmark_values.get('free_cash_flow_cr', 0) / 100, 'FCF'),
        normalize_for_radar(benchmark_values.get('revenue_cagr_5yr', 0), 'Rev CAGR')
    ]
    
    peer_avg_radar = [
        normalize_for_radar(peer_avg_values.get('return_on_equity_pct', 0), 'ROE'),
        normalize_for_radar(peer_avg_values.get('roce_pct', 0), 'ROCE'),
        normalize_for_radar(peer_avg_values.get('debt_to_equity', 0), 'D/E'),
        normalize_for_radar(peer_avg_values.get('net_profit_margin_pct', 0), 'NPM'),
        normalize_for_radar(peer_avg_values.get('operating_profit_margin_pct', 0), 'OPM'),
        normalize_for_radar(peer_avg_values.get('asset_turnover', 0), 'Asset Turnover'),
        normalize_for_radar(peer_avg_values.get('free_cash_flow_cr', 0) / 100, 'FCF'),
        normalize_for_radar(peer_avg_values.get('revenue_cagr_5yr', 0), 'Rev CAGR')
    ]
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatterpolar(
        r=benchmark_radar,
        theta=metric_labels,
        fill='toself',
        name=f"{benchmark_data['company_name']}",
        line_color='blue'
    ))
    
    fig.add_trace(go.Scatterpolar(
        r=peer_avg_radar,
        theta=metric_labels,
        fill='toself',
        name='Peer Group Average',
        line_color='orange'
    ))
    
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 100]
            )),
        showlegend=True,
        height=500,
        margin=dict(l=20, r=20, t=40, b=20)
    )
    
    st.plotly_chart(fig, use_container_width=True)

# KPI comparison table
st.subheader("KPI Comparison Table")

if not peer_data.empty:
    # Select columns for comparison table
    table_cols = [
        'company_name',
        'return_on_equity_pct',
        'roce_pct',
        'debt_to_equity',
        'net_profit_margin_pct',
        'operating_profit_margin_pct',
        'asset_turnover',
        'free_cash_flow_cr',
        'revenue_cagr_5yr'
    ]
    
    available_table_cols = [col for col in table_cols if col in peer_data.columns]
    comparison_df = peer_data[available_table_cols].copy()
    
    # Format values
    for col in available_table_cols:
        if col != 'company_name':
            comparison_df[col] = comparison_df[col].round(2)
    
    # Highlight benchmark row
    if benchmark_data is not None:
        benchmark_name = benchmark_data['company_name']
        comparison_df['is_benchmark'] = comparison_df['company_name'] == benchmark_name
    
    # Rename columns
    col_rename = {
        'company_name': 'Company',
        'return_on_equity_pct': 'ROE (%)',
        'roce_pct': 'ROCE (%)',
        'debt_to_equity': 'D/E',
        'net_profit_margin_pct': 'NPM (%)',
        'operating_profit_margin_pct': 'OPM (%)',
        'asset_turnover': 'Asset Turnover',
        'free_cash_flow_cr': 'FCF (Cr)',
        'revenue_cagr_5yr': 'Rev CAGR (%)'
    }
    comparison_df = comparison_df.rename(columns=col_rename)
    
    # Display with highlighting
    st.dataframe(comparison_df, use_container_width=True, height=400)
else:
    st.warning("No peer data available for comparison")
