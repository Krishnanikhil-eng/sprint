"""
Company Profile Screen
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

from src.dashboard.utils.db import get_companies, get_ratios, get_pl, get_pros_cons
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

# Charts
st.markdown("---")
st.subheader("Financial Performance Charts")

# Load P&L data for charts
try:
    pl_data = get_pl(ticker)
except Exception as e:
    st.error(f"Error loading P&L data: {e}")
    pl_data = pd.DataFrame()

if not pl_data.empty:
    # Revenue and Net Profit bar chart
    chart_col1, chart_col2 = st.columns(2)
    
    with chart_col1:
        st.markdown("**Revenue & Net Profit (10 Years)**")
        pl_sorted = pl_data.sort_values('year').tail(10)
        
        fig1 = go.Figure()
        fig1.add_trace(go.Bar(
            x=pl_sorted['year'],
            y=pl_sorted['sales'],
            name='Revenue',
            marker_color='blue'
        ))
        fig1.add_trace(go.Bar(
            x=pl_sorted['year'],
            y=pl_sorted['net_profit'],
            name='Net Profit',
            marker_color='green'
        ))
        fig1.update_layout(
            barmode='group',
            height=400,
            xaxis_title='Year',
            yaxis_title='Amount (Cr)',
            margin=dict(l=20, r=20, t=40, b=20)
        )
        st.plotly_chart(fig1, use_container_width=True)
    
    with chart_col2:
        st.markdown("**ROE & ROCE Trend**")
        ratios_sorted = ratios_data.sort_values('year').tail(10)
        
        fig2 = go.Figure()
        fig2.add_trace(go.Scatter(
            x=ratios_sorted['year'],
            y=ratios_sorted['return_on_equity_pct'],
            mode='lines+markers',
            name='ROE',
            line=dict(color='blue')
        ))
        fig2.add_trace(go.Scatter(
            x=ratios_sorted['year'],
            y=ratios_sorted['roce_pct'],
            mode='lines+markers',
            name='ROCE',
            line=dict(color='orange'),
            yaxis='y2'
        ))
        fig2.update_layout(
            height=400,
            xaxis_title='Year',
            yaxis_title='ROE (%)',
            yaxis2=dict(
                title='ROCE (%)',
                overlaying='y',
                side='right'
            ),
            margin=dict(l=20, r=20, t=40, b=20)
        )
        st.plotly_chart(fig2, use_container_width=True)
else:
    st.warning("No P&L data available for charts")

# Pros and Cons
st.markdown("---")
st.subheader("Pros and Cons")

try:
    pros_cons_data = get_pros_cons(ticker)
except Exception as e:
    st.error(f"Error loading pros and cons: {e}")
    pros_cons_data = pd.DataFrame()

if not pros_cons_data.empty:
    pc_row = pros_cons_data.iloc[0]
    pros_col, cons_col = st.columns(2)
    
    with pros_col:
        st.markdown("### ✅ Pros")
        pros_text = pc_row.get('pros', '')
        if pd.notna(pros_text) and pros_text:
            pros_list = [p.strip() for p in str(pros_text).split('\n') if p.strip()]
            for pro in pros_list:
                st.markdown(f"✅ {pro}")
        else:
            st.info("No pros data available")
    
    with cons_col:
        st.markdown("### ❌ Cons")
        cons_text = pc_row.get('cons', '')
        if pd.notna(cons_text) and cons_text:
            cons_list = [c.strip() for c in str(cons_text).split('\n') if c.strip()]
            for con in cons_list:
                st.markdown(f"❌ {con}")
        else:
            st.info("No cons data available")
else:
    st.info("No pros and cons data available for this company")
