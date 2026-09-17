"""
Sector Analysis Screen
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from src.dashboard.utils.db import get_latest_ratios_all, get_sectors, get_connection
from src.dashboard.utils.ui import safe_render, render_simulated_warning

st.title("Sector Intelligence")

@safe_render()
def render_sector_intelligence():
    ratios_df = get_latest_ratios_all()
    sectors_df = get_sectors()

    if ratios_df.empty or sectors_df.empty:
        st.warning("Data is unavailable for sector analysis.")
        return

    # Fetch latest sales revenue
    conn = get_connection()
    try:
        pl_df = pd.read_sql_query("""
            WITH LatestPL AS (
                SELECT company_id, sales,
                       ROW_NUMBER() OVER (PARTITION BY company_id ORDER BY year DESC) as rn
                FROM profitandloss
            )
            SELECT company_id, sales FROM LatestPL WHERE rn = 1
        """, conn)
        merged_df = pd.merge(ratios_df, pl_df, on="company_id", how="left")
    finally:
        conn.close()

    # Sector dropdown
    available_sectors = sorted(merged_df["broad_sector"].dropna().unique().tolist())
    
    col1, col2 = st.columns([1, 2])
    with col1:
        selected_sector = st.selectbox(
            "Select Sector",
            options=available_sectors,
            help="Select a sector to analyze aggregated financials and distributions."
        )

    if not selected_sector:
        st.info("Please select a sector to begin.")
        return

    sector_df = merged_df[merged_df["broad_sector"] == selected_sector].copy()
    
    if sector_df.empty:
        st.warning(f"No valid data available for {selected_sector}.")
        return

    st.markdown("---")
    st.markdown(f"### {selected_sector} Sector Overview")
    
    comp_count = len(sector_df)
    sub_sectors = sector_df["sub_sector"].nunique()
    total_mc = pd.to_numeric(sector_df.get("market_cap_crore", pd.Series()), errors="coerce").sum()
    med_pe = pd.to_numeric(sector_df.get("pe_ratio", pd.Series()), errors="coerce").median()

    ov1, ov2, ov3, ov4 = st.columns(4)
    ov1.metric("Constituent Companies", comp_count)
    ov2.metric("Sub-Sectors", sub_sectors)
    ov3.metric("Total Market Cap (Cr)", f"₹{total_mc:,.0f}" if total_mc else "N/A")
    ov4.metric("Median P/E", f"{med_pe:.2f}x" if pd.notna(med_pe) else "N/A")

    st.markdown("---")
    
    st.subheader("Financial Distributions")
    dist_metrics = {
        "return_on_equity_pct": "ROE (%)",
        "roce_pct": "ROCE (%)",
        "net_profit_margin_pct": "Net Profit Margin (%)",
        "debt_to_equity": "D/E Ratio",
        "pe_ratio": "P/E Ratio",
        "revenue_cagr_5yr": "Revenue CAGR 5Yr (%)"
    }
    
    avail_dist = [m for m in dist_metrics.keys() if m in sector_df.columns]
    
    if avail_dist:
        dist_col1, dist_col2 = st.columns([1, 3])
        with dist_col1:
            selected_dist = st.selectbox("Select Distribution Metric", options=avail_dist, format_func=lambda x: dist_metrics[x])
            
        with dist_col2:
            clean_series = pd.to_numeric(sector_df[selected_dist], errors="coerce").dropna()
            if not clean_series.empty:
                fig_box = go.Figure()
                fig_box.add_trace(go.Box(
                    x=clean_series,
                    name=dist_metrics[selected_dist],
                    boxpoints='all',
                    jitter=0.3,
                    pointpos=-1.8,
                    marker_color='#1f77b4'
                ))
                fig_box.update_layout(
                    height=300,
                    margin=dict(l=20, r=20, t=20, b=20),
                    xaxis_title=dist_metrics[selected_dist]
                )
                st.plotly_chart(fig_box, use_container_width=True)
            else:
                st.info("Insufficient data for distribution plot.")

    st.markdown("---")
    
    st.subheader("Company Mapping (Revenue vs ROE)")
    render_simulated_warning()
    
    bubble_data = sector_df.dropna(subset=["sales", "return_on_equity_pct"]).copy()
    if not bubble_data.empty:
        bubble_data["sales"] = pd.to_numeric(bubble_data["sales"], errors="coerce")
        bubble_data["return_on_equity_pct"] = pd.to_numeric(bubble_data["return_on_equity_pct"], errors="coerce")
        
        # Ensure positive market cap for bubble sizing
        if "market_cap_crore" in bubble_data.columns:
            bubble_data["mc_size"] = pd.to_numeric(bubble_data["market_cap_crore"], errors="coerce").fillna(1000.0)
            bubble_data["mc_size"] = bubble_data["mc_size"].apply(lambda x: max(100.0, float(x)))
        else:
            bubble_data["mc_size"] = 1000.0

        fig_scatter = px.scatter(
            bubble_data,
            x="sales", y="return_on_equity_pct",
            size="mc_size",
            color="sub_sector" if "sub_sector" in bubble_data.columns else None,
            hover_name="company_name",
            hover_data=["company_id", "market_cap_crore", "pe_ratio"],
            labels={
                "sales": "Revenue (₹ Cr)",
                "return_on_equity_pct": "ROE (%)",
                "sub_sector": "Sub-Sector",
                "mc_size": "Market Cap",
                "market_cap_crore": "Market Cap (Cr)",
            },
            color_discrete_sequence=px.colors.qualitative.Prism
        )
        fig_scatter.update_layout(height=500, margin=dict(l=20, r=20, t=40, b=20))
        st.plotly_chart(fig_scatter, use_container_width=True)
    else:
        st.info("Insufficient data for company mapping scatter plot.")

render_sector_intelligence()
