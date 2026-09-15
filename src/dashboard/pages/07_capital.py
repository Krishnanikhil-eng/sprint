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

if 'company_name_y' in merged_df.columns:
    merged_df['company_name'] = merged_df['company_name_y'].fillna(merged_df['company_name_x'])
elif 'company_name_x' in merged_df.columns:
    merged_df['company_name'] = merged_df['company_name_x']

# Check for capital allocation pattern column
if 'capital_allocation_pattern' not in merged_df.columns:
    st.warning("Capital allocation pattern data not available in ratios")
    st.stop()

# Fill missing patterns cleanly
merged_df['capital_allocation_pattern'] = merged_df['capital_allocation_pattern'].fillna('Unclassified')

pattern_counts = merged_df['capital_allocation_pattern'].value_counts().reset_index()
pattern_counts.columns = ['Pattern', 'Count']

st.info(f"Analyzing {len(merged_df)} companies across {len(pattern_counts)} capital allocation patterns")

# Treemap visualization grouped by Pattern and Company
st.subheader("Capital Allocation Pattern Treemap")

treemap_df = merged_df.copy()
treemap_df['Count'] = 1

fig = px.treemap(
    treemap_df,
    path=['capital_allocation_pattern', 'company_name'],
    values='Count',
    title='Capital Allocation Pattern Breakdown (Click pattern to expand companies)',
    color='capital_allocation_pattern',
    color_discrete_sequence=px.colors.qualitative.Prism
)
fig.update_layout(
    height=550,
    margin=dict(l=20, r=20, t=40, b=20)
)
st.plotly_chart(fig, use_container_width=True)

st.markdown("---")

# Pattern details
st.subheader("Companies by Capital Allocation Pattern")

selected_pattern = st.selectbox(
    "Select a pattern to view member companies",
    options=pattern_counts['Pattern'].tolist(),
    help="View details for all companies belonging to a specific capital allocation strategy"
)

if selected_pattern:
    pattern_companies = merged_df[merged_df['capital_allocation_pattern'] == selected_pattern]
    
    if not pattern_companies.empty:
        st.info(f"{len(pattern_companies)} companies classified under '{selected_pattern}'")
        
        display_cols = ['company_id', 'company_name', 'broad_sector', 'return_on_equity_pct', 'debt_to_equity', 'free_cash_flow_cr', 'composite_quality_score']
        available_cols = [col for col in display_cols if col in pattern_companies.columns]
        
        results_df = pattern_companies[available_cols].copy()
        
        # Format numeric columns
        for col in available_cols:
            if col not in ['company_id', 'company_name', 'broad_sector']:
                results_df[col] = pd.to_numeric(results_df[col], errors='coerce').round(2)
        
        # Rename columns for table
        col_rename = {
            'company_id': 'Ticker',
            'company_name': 'Company Name',
            'broad_sector': 'Sector',
            'return_on_equity_pct': 'ROE (%)',
            'debt_to_equity': 'D/E',
            'free_cash_flow_cr': 'FCF (Cr)',
            'composite_quality_score': 'Quality Score'
        }
        results_df = results_df.rename(columns=col_rename)
        
        st.dataframe(results_df.fillna("N/A"), use_container_width=True, height=400)
    else:
        st.warning(f"No companies found for pattern: {selected_pattern}")

