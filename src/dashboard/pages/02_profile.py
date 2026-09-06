"""
Company Profile Screen
"""

import streamlit as st
import pandas as pd

from src.dashboard.utils.db import get_companies
from src.dashboard.config import LABEL_NA

st.header("Company Profile")

# Load companies
try:
    companies_df = get_companies()
except Exception as e:
    st.error(f"Error loading companies: {e}")
    st.stop()

if companies_df.empty:
    st.warning("No companies available in database")
    st.stop()

# Search functionality
search_col1, search_col2 = st.columns([2, 1])

with search_col1:
    search_term = st.text_input(
        "Search by Company Name or Ticker",
        placeholder="e.g., Reliance or RELIANCE",
        help="Type company name or NSE ticker to search"
    )

with search_col2:
    if not companies_df.empty:
        company_options = ["Select a company..."] + sorted(companies_df['company_name'].tolist())
        selected_company = st.selectbox(
            "Or select from list",
            options=company_options,
            index=0
        )
    else:
        selected_company = None

# Determine search query
search_query = None
if selected_company and selected_company != "Select a company...":
    search_query = selected_company
elif search_term:
    search_query = search_term.strip()

# Find matching company
ticker = None
if search_query:
    # Try exact match on company name
    match = companies_df[companies_df['company_name'].str.lower() == search_query.lower()]
    if match.empty:
        # Try exact match on ticker
        match = companies_df[companies_df['nse_profile'].str.lower() == search_query.lower()]
    if match.empty:
        # Try partial match on company name
        match = companies_df[companies_df['company_name'].str.contains(search_query, case=False, na=False)]
    
    if not match.empty:
        ticker = match.iloc[0]['company_id']
        company_data = match.iloc[0]
    else:
        st.error("Ticker not found — please try another")
        st.stop()
else:
    st.info("Please search or select a company to view profile")
    st.stop()
