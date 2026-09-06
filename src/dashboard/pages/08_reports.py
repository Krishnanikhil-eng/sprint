"""
Annual Reports Screen
"""

import streamlit as st
import pandas as pd

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

# Company search
search_col1, search_col2 = st.columns([2, 1])

with search_col1:
    search_term = st.text_input(
        "Search Company",
        placeholder="e.g., Reliance",
        help="Type company name to search"
    )

with search_col2:
    company_options = ["Select a company..."] + sorted(companies_df['company_name'].tolist())
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
if search_query:
    match = companies_df[companies_df['company_name'].str.lower() == search_query.lower()]
    if match.empty:
        match = companies_df[companies_df['company_name'].str.contains(search_query, case=False, na=False)]
    
    if not match.empty:
        ticker = match.iloc[0]['company_id']
        company_name = match.iloc[0]['company_name']
    else:
        st.error("Company not found")
        st.stop()
else:
    st.info("Please search or select a company")
    st.stop()

# Load documents
try:
    documents_df = get_documents(ticker)
except Exception as e:
    st.error(f"Error loading documents: {e}")
    documents_df = pd.DataFrame()

st.subheader(f"Annual Reports - {company_name}")

if documents_df.empty:
    st.warning("No annual reports available for this company")
else:
    # Display available reports
    for idx, row in documents_df.iterrows():
        year = row.get('year', 'N/A')
        report_url = row.get('annual_report', '')
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.markdown(f"**Year:** {year}")
        
        with col2:
            if pd.notna(report_url) and report_url:
                st.markdown(f"[📄 Download PDF]({report_url})")
            else:
                st.markdown("🔴 Report unavailable", unsafe_allow_html=True)
        
        st.markdown("---")
