"""
Company Profile Screen
"""

import streamlit as st
import pandas as pd

from src.dashboard.utils.db import get_companies, get_ratios
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

# Company Card
st.markdown("---")
st.subheader("Company Information")

col1, col2 = st.columns(2)

with col1:
    st.markdown(f"**Company Name:** {company_data.get('company_name', LABEL_NA)}")
    st.markdown(f"**Sector:** {company_data.get('broad_sector', LABEL_NA)}")
    st.markdown(f"**Sub-Sector:** {company_data.get('sub_sector', LABEL_NA)}")

with col2:
    st.markdown(f"**NSE Ticker:** {company_data.get('nse_profile', LABEL_NA)}")
    
about = company_data.get('about_company', LABEL_NA)
if pd.isna(about) or about is None:
    about = LABEL_NA
st.markdown(f"**About:** {about}")

# Load financial ratios
try:
    ratios_data = get_ratios(ticker)
except Exception as e:
    st.error(f"Error loading financial ratios: {e}")
    ratios_data = pd.DataFrame()

# KPI Tiles
st.markdown("---")
st.subheader("Key Performance Indicators")

if not ratios_data.empty:
    latest_ratios = ratios_data.iloc[0]
    
    kpi1, kpi2, kpi3 = st.columns(3)
    kpi4, kpi5, kpi6 = st.columns(3)
    
    def format_kpi(value, metric_type="percentage"):
        if pd.isna(value) or value is None:
            return LABEL_NA
        if metric_type == "percentage":
            return f"{value:.2f}%"
        elif metric_type == "currency":
            return f"₹{value:.2f} Cr"
        else:
            return f"{value:.2f}"
    
    with kpi1:
        roe = latest_ratios.get('return_on_equity_pct')
        st.metric("ROE", format_kpi(roe, "percentage"))
    
    with kpi2:
        roce = latest_ratios.get('roce_pct')
        st.metric("ROCE", format_kpi(roce, "percentage"))
    
    with kpi3:
        npm = latest_ratios.get('net_profit_margin_pct')
        st.metric("Net Profit Margin", format_kpi(npm, "percentage"))
    
    with kpi4:
        de = latest_ratios.get('debt_to_equity')
        st.metric("D/E", format_kpi(de, "ratio"))
    
    with kpi5:
        rev_cagr = latest_ratios.get('revenue_cagr_5yr')
        st.metric("Revenue CAGR (5yr)", format_kpi(rev_cagr, "percentage"))
    
    with kpi6:
        fcf = latest_ratios.get('free_cash_flow_cr')
        st.metric("FCF (Latest)", format_kpi(fcf, "currency"))
else:
    st.warning("No financial ratios available for this company")
