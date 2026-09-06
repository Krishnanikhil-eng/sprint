"""
Capital Allocation Screen
"""

import streamlit as st
import pandas as pd
import plotly.express as px

from src.dashboard.utils.db import get_latest_ratios_all, get_companies
from src.dashboard.config import LABEL_NA

st.header("Capital Allocation Map")

# Load data
try:
    ratios_df = get_latest_ratios_all()
    companies_df = get_companies()
except Exception as e:
    st.error(f"Error loading data: {e}")
    st.stop()

if ratios_df.empty:
    st.warning("No data available for capital allocation analysis")
    st.stop()

# Merge with company names
merged_df = pd.merge(ratios_df, companies_df[['company_id', 'company_name']], on='company_id', how='left')

# Check for capital allocation pattern column
if 'capital_allocation_pattern' not in merged_df.columns:
    st.warning("Capital allocation pattern data not available in ratios")
    st.stop()

# Group by capital allocation pattern
pattern_counts = merged_df['capital_allocation_pattern'].value_counts().reset_index()
pattern_counts.columns = ['Pattern', 'Count']

st.info(f"Analyzing {len(merged_df)} companies across {len(pattern_counts)} capital allocation patterns")

# Treemap visualization
st.subheader("Capital Allocation Patterns")

fig = px.treemap(
    pattern_counts,
    path=['Pattern'],
    values='Count',
    title='Capital Allocation Pattern Distribution',
    color='Count',
    color_continuous_scale='Viridis'
)
fig.update_layout(
    height=500,
    margin=dict(l=20, r=20, t=40, b=20)
)
st.plotly_chart(fig, use_container_width=True)

# Pattern details
st.subheader("Pattern Details")

selected_pattern = st.selectbox(
    "Select a pattern to view companies",
    options=pattern_counts['Pattern'].tolist(),
    help="View companies in each capital allocation pattern"
)

if selected_pattern:
    pattern_companies = merged_df[merged_df['capital_allocation_pattern'] == selected_pattern]
    
    if not pattern_companies.empty:
        st.info(f"{len(pattern_companies)} companies in '{selected_pattern}' pattern")
        
        display_cols = ['company_name', 'capital_allocation_pattern', 'return_on_equity_pct', 'debt_to_equity', 'free_cash_flow_cr']
        available_cols = [col for col in display_cols if col in pattern_companies.columns]
        
        results_df = pattern_companies[available_cols].copy()
        
        # Format for display
        for col in available_cols:
            if col != 'company_name' and col != 'capital_allocation_pattern':
                results_df[col] = results_df[col].round(2)
        
        # Rename columns
        col_rename = {
            'company_name': 'Company',
            'capital_allocation_pattern': 'Pattern',
            'return_on_equity_pct': 'ROE (%)',
            'debt_to_equity': 'D/E',
            'free_cash_flow_cr': 'FCF (Cr)'
        }
        results_df = results_df.rename(columns=col_rename)
        
        st.dataframe(results_df, use_container_width=True, height=400)
    else:
        st.warning(f"No companies found for pattern: {selected_pattern}")
