"""
Annual Reports Screen
"""

import streamlit as st
import pandas as pd
import requests

from src.dashboard.utils.db import get_companies, get_documents
from src.dashboard.config import LABEL_NA

st.header("Annual Reports")

# Load companies
try:
    companies_df = get_companies()
except Exception as e:
    st.error(f"Error loading companies: {e}")
    st.stop()

if companies_df.empty:
    st.warning("No companies available")
    st.stop()

# Search functionality
search_col1, search_col2 = st.columns([2, 1])

with search_col1:
    search_term = st.text_input(
        "Search Company",
        placeholder="e.g., Reliance or TCS",
        help="Type company name or ticker to search"
    )

with search_col2:
    company_options = ["Select a company..."] + sorted(companies_df['company_name'].dropna().unique().tolist())
    selected_company = st.selectbox(
        "Or select from list",
        options=company_options,
        index=0
    )

# Determine selected company
search_query = None
if selected_company and selected_company != "Select a company...":
    search_query = selected_company
elif search_term:
    search_query = search_term.strip()

# Find matching company
ticker = None
company_name = None

if search_query:
    query_lower = search_query.lower()
    match = companies_df[
        (companies_df['company_name'].str.lower() == query_lower) |
        (companies_df['nse_profile'].astype(str).str.lower() == query_lower) |
        (companies_df['company_id'].astype(str).str.lower() == query_lower)
    ]
    if match.empty:
        match = companies_df[
            companies_df['company_name'].str.contains(search_query, case=False, na=False) |
            companies_df['nse_profile'].astype(str).str.contains(search_query, case=False, na=False) |
            companies_df['company_id'].astype(str).str.contains(search_query, case=False, na=False)
        ]
    
    if not match.empty:
        ticker = match.iloc[0]['company_id']
        company_name = match.iloc[0]['company_name']
    else:
        st.error("Company not found — please try another search")
        st.stop()
else:
    st.info("Please search or select a company to view annual reports")
    st.stop()

# Load documents for company
try:
    documents_df = get_documents(ticker)
except Exception as e:
    st.error(f"Error loading documents: {e}")
    documents_df = pd.DataFrame()

st.subheader(f"Annual Reports — {company_name} ({ticker})")

@st.cache_data(ttl=3600)
def validate_url(url: str) -> bool:
    """Validate report URL format and accessibility."""
    if not isinstance(url, str) or not url.strip():
        return False
    url = url.strip()
    if not (url.startswith("http://") or url.startswith("https://")):
        return False
    try:
        res = requests.head(url, timeout=1.5, allow_redirects=True)
        if res.status_code == 200:
            return True
        if res.status_code == 404:
            return False
        # Try quick GET if server rejects HEAD
        res_get = requests.get(url, timeout=1.5, stream=True)
        return res_get.status_code == 200
    except Exception:
        # Fallback for valid BSE URLs if network blocked
        return len(url) > 12 and "bseindia.com" in url

if documents_df.empty:
    st.warning("No annual reports recorded for this company")
else:
    for idx, row in documents_df.iterrows():
        year = row.get('year', LABEL_NA)
        report_url = str(row.get('annual_report', '')).strip()
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.markdown(f"**Fiscal Year {year} Annual Report**")
        
        with col2:
            if validate_url(report_url):
                st.markdown(f"🔗 [📄 Download BSE PDF]({report_url})")
            else:
                st.markdown('<span style="background-color:#ffdddd; color:#cc0000; padding:4px 8px; border-radius:4px; font-weight:bold;">🔴 Report unavailable</span>', unsafe_allow_html=True)
        
        st.markdown("---")

