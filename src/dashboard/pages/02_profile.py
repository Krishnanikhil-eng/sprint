"""
Company Profile Screen
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go

from src.dashboard.utils.db import get_ratios, get_pl, get_pros_cons
from src.dashboard.utils.ui import (
    company_selector,
    format_percentage,
    format_ratio,
    format_currency,
    safe_render
)
from src.dashboard.config import LABEL_NA

st.title("Company Profile")

# Unified Company Selector
ticker, company_data = company_selector()

if not ticker or company_data is None:
    st.stop()

@safe_render()
def render_profile(ticker_id: str, comp_data: pd.Series):
    # Company Header
    st.markdown("---")
    
    col1, col2 = st.columns([3, 1])
    with col1:
        st.subheader(comp_data.get("company_name", LABEL_NA))
        sector = comp_data.get("broad_sector", LABEL_NA)
        sub_sector = comp_data.get("sub_sector", LABEL_NA)
        st.caption(f"{sector} | {sub_sector}")
    with col2:
        nse_ticker = comp_data.get("nse_profile", comp_data.get("company_id", LABEL_NA))
        st.markdown(f"**Ticker:** `{nse_ticker}`")
    
    about = comp_data.get("about_company", LABEL_NA)
    if pd.isna(about) or not about:
        about = "No description available."
    with st.expander("About Company", expanded=False):
        st.write(about)

    # Load financial ratios
    ratios_data = get_ratios(ticker_id)
    
    if ratios_data.empty:
        st.warning("No financial ratios available for this company.")
        return

    latest_ratios = ratios_data.iloc[0]
    fy = latest_ratios.get("year", "N/A")

    st.markdown("---")
    st.subheader(f"Key Performance Indicators (FY{fy})")
    
    # Financial Overview Tiles
    k1, k2, k3, k4 = st.columns(4)
    with k1:
        st.metric("ROE", format_percentage(latest_ratios.get("return_on_equity_pct")))
        st.metric("5Yr Rev CAGR", format_percentage(latest_ratios.get("revenue_cagr_5yr")))
    with k2:
        st.metric("ROCE", format_percentage(latest_ratios.get("roce_pct")))
        st.metric("5Yr PAT CAGR", format_percentage(latest_ratios.get("pat_cagr_5yr")))
    with k3:
        st.metric("Net Profit Margin", format_percentage(latest_ratios.get("net_profit_margin_pct")))
        st.metric("Asset Turnover", format_ratio(latest_ratios.get("asset_turnover"), "x"))
    with k4:
        st.metric("D/E Ratio", format_ratio(latest_ratios.get("debt_to_equity"), "x"))
        st.metric("Free Cash Flow", format_currency(latest_ratios.get("free_cash_flow_cr")))

    st.markdown("---")
    st.subheader("Financial Performance Trends")

    # Load P&L
    pl_data = get_pl(ticker_id)
    
    chart_col1, chart_col2 = st.columns(2)
    
    with chart_col1:
        st.markdown("**Revenue & Net Profit (10-Year)**")
        if not pl_data.empty and "sales" in pl_data.columns:
            pl_sorted = pl_data.sort_values("year").tail(10)
            pl_sorted["sales"] = pd.to_numeric(pl_sorted["sales"], errors="coerce").fillna(0)
            pl_sorted["net_profit"] = pd.to_numeric(pl_sorted["net_profit"], errors="coerce").fillna(0)
            
            if len(pl_sorted) > 0:
                fig1 = go.Figure()
                fig1.add_trace(go.Bar(x=pl_sorted["year"], y=pl_sorted["sales"], name="Revenue", marker_color="#1f77b4"))
                fig1.add_trace(go.Bar(x=pl_sorted["year"], y=pl_sorted["net_profit"], name="Net Profit", marker_color="#2ca02c"))
                fig1.update_layout(
                    barmode="group",
                    height=350,
                    margin=dict(l=20, r=20, t=30, b=20),
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
                )
                st.plotly_chart(fig1, use_container_width=True)
            else:
                st.info("Insufficient P&L data for visualization.")
        else:
            st.info("P&L data unavailable.")

    with chart_col2:
        st.markdown("**Return Ratios (10-Year)**")
        ratios_sorted = ratios_data.sort_values("year").tail(10)
        
        if not ratios_sorted.empty:
            ratios_sorted["return_on_equity_pct"] = pd.to_numeric(ratios_sorted["return_on_equity_pct"], errors="coerce")
            ratios_sorted["roce_pct"] = pd.to_numeric(ratios_sorted["roce_pct"], errors="coerce")
            
            # Remove entirely null rows for graphing
            graph_df = ratios_sorted.dropna(subset=["return_on_equity_pct", "roce_pct"], how="all")
            
            if len(graph_df) > 0:
                fig2 = go.Figure()
                fig2.add_trace(go.Scatter(x=graph_df["year"], y=graph_df["return_on_equity_pct"], mode="lines+markers", name="ROE (%)", line=dict(color="#1f77b4", width=3)))
                fig2.add_trace(go.Scatter(x=graph_df["year"], y=graph_df["roce_pct"], mode="lines+markers", name="ROCE (%)", line=dict(color="#ff7f0e", width=3)))
                fig2.update_layout(
                    height=350,
                    margin=dict(l=20, r=20, t=30, b=20),
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
                )
                st.plotly_chart(fig2, use_container_width=True)
            else:
                st.info("Insufficient ratios data for visualization.")
        else:
            st.info("Ratios data unavailable.")

    st.markdown("---")
    st.subheader("NLP Qualitative Analysis")
    
    pros_cons_data = get_pros_cons(ticker_id)
    if not pros_cons_data.empty:
        pc_row = pros_cons_data.iloc[0]
        pc_col1, pc_col2 = st.columns(2)
        
        with pc_col1:
            st.markdown("#### ✅ Strengths / Pros")
            pros_text = pc_row.get("pros", "")
            if pd.notna(pros_text) and pros_text:
                for pro in [p.strip() for p in str(pros_text).split("\n") if p.strip()]:
                    st.success(pro)
            else:
                st.info("No positive analytical signals reported.")

        with pc_col2:
            st.markdown("#### ❌ Weaknesses / Cons")
            cons_text = pc_row.get("cons", "")
            if pd.notna(cons_text) and cons_text:
                for con in [c.strip() for c in str(cons_text).split("\n") if c.strip()]:
                    st.error(con)
            else:
                st.info("No negative analytical warnings reported.")
    else:
        st.info("NLP Analysis is not available for this company.")

# Render page
render_profile(ticker, company_data)
