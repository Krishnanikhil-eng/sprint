"""
Trend Analysis Screen
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go

from src.dashboard.utils.db import get_ratios
from src.dashboard.utils.ui import company_selector, safe_render
from src.dashboard.config import LABEL_NA

st.title("Trend Analysis")

# Unified Company Selector
ticker, company_data = company_selector()

if not ticker or company_data is None:
    st.stop()

@safe_render()
def render_trends(ticker_id: str, comp_data: pd.Series):
    company_name = comp_data.get("company_name", ticker_id)
    st.markdown(f"### {company_name}")
    
    ratios_data = get_ratios(ticker_id)
    if ratios_data.empty:
        st.warning("No ratio data available for this company.")
        return

    # Metric groups
    metrics_config = {
        "Profitability & Returns": {
            "return_on_equity_pct": "ROE (%)",
            "roce_pct": "ROCE (%)"
        },
        "Margins": {
            "net_profit_margin_pct": "NPM (%)",
            "operating_profit_margin_pct": "OPM (%)"
        },
        "Growth": {
            "revenue_cagr_5yr": "Revenue CAGR (%)",
            "pat_cagr_5yr": "PAT CAGR (%)"
        },
        "Health & Efficiency": {
            "debt_to_equity": "D/E Ratio",
            "asset_turnover": "Asset Turnover",
            "free_cash_flow_cr": "FCF (Cr)",
            "interest_coverage": "Interest Coverage"
        }
    }

    # Flat mapping for easy access
    flat_metrics = {}
    for group, items in metrics_config.items():
        flat_metrics.update(items)

    available_metrics = [m for m in flat_metrics.keys() if m in ratios_data.columns]
    
    if not available_metrics:
        st.warning("No trend metrics available.")
        return

    # Selector UI
    col1, col2 = st.columns([1, 3])
    with col1:
        metric_category = st.selectbox("Metric Category", options=list(metrics_config.keys()))
        
        category_metrics = [m for m in metrics_config[metric_category].keys() if m in available_metrics]
        
        selected_metrics = st.multiselect(
            "Select Metrics",
            options=category_metrics,
            format_func=lambda x: flat_metrics.get(x, x),
            default=category_metrics[:2] if category_metrics else []
        )
        
    if not selected_metrics:
        with col2:
            st.info("Please select at least one metric to visualize.")
        return

    # Process data for charting
    ratios_sorted = ratios_data.sort_values("year").tail(10)
    
    with col2:
        st.subheader("10-Year Historical Trend")
        fig = go.Figure()
        colors = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728"]
        
        for i, metric in enumerate(selected_metrics):
            # Clean data for plotting
            clean_series = pd.to_numeric(ratios_sorted[metric], errors="coerce")
            
            fig.add_trace(go.Scatter(
                x=ratios_sorted["year"],
                y=clean_series,
                mode="lines+markers",
                name=flat_metrics.get(metric, metric),
                line=dict(color=colors[i % len(colors)], width=3),
                connectgaps=False # Don't fabricate missing data lines
            ))

        fig.update_layout(
            xaxis_title="Financial Year",
            height=450,
            hovermode="x unified",
            margin=dict(l=20, r=20, t=20, b=20),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")
    
    # YoY Analysis Table
    st.subheader("Year-over-Year Analysis")

    def calculate_yoy(current, previous):
        if pd.isna(current) or pd.isna(previous): return None
        try:
            c = float(current)
            p = float(previous)
            if p == 0: return None
            return ((c - p) / abs(p)) * 100.0
        except (ValueError, TypeError):
            return None

    yoy_data = []
    for i in range(1, len(ratios_sorted)):
        curr = ratios_sorted.iloc[i]
        prev = ratios_sorted.iloc[i-1]
        
        row = {"Year": f"FY{curr['year']} (vs FY{prev['year']})"}
        for metric in selected_metrics:
            val = calculate_yoy(curr.get(metric), prev.get(metric))
            row[flat_metrics.get(metric, metric)] = val
        yoy_data.append(row)

    if yoy_data:
        yoy_df = pd.DataFrame(yoy_data)
        
        # Styler formatting for YoY percentages
        def color_yoy(val):
            if pd.isna(val) or val == LABEL_NA:
                return ''
            try:
                # Remove % sign and convert to float
                v = float(str(val).replace("%", ""))
                if v > 0: return 'color: #2ca02c'
                if v < 0: return 'color: #d62728'
                return ''
            except:
                return ''

        # Format strings
        for metric in selected_metrics:
            label = flat_metrics.get(metric, metric)
            if label in yoy_df.columns:
                yoy_df[label] = yoy_df[label].apply(
                    lambda x: f"{x:+.2f}%" if pd.notna(x) else LABEL_NA
                )
                
        styler = yoy_df.style.applymap(color_yoy, subset=[flat_metrics.get(m) for m in selected_metrics])
        st.dataframe(styler, use_container_width=True, hide_index=True)
    else:
        st.info("Insufficient historical data for Year-over-Year analysis.")

render_trends(ticker, company_data)
