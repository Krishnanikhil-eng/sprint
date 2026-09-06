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
