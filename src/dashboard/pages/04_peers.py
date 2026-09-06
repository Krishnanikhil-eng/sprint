"""
Peer Comparison Screen
"""

import streamlit as st
import pandas as pd

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
