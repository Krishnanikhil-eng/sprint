"""
Trend Analysis Screen
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go

from src.dashboard.utils.db import get_companies, get_ratios
from src.dashboard.config import LABEL_NA

st.header("Trend Analysis")

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
        help="Type company name to search",
    )

with search_col2:
    company_options = ["Select a company..."] + sorted(
        companies_df["company_name"].tolist()
    )
    selected_company = st.selectbox(
        "Or select from list", options=company_options, index=0
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
    match = companies_df[
        companies_df["company_name"].str.lower() == search_query.lower()
    ]
    if match.empty:
        match = companies_df[
            companies_df["company_name"].str.contains(
                search_query, case=False, na=False
            )
        ]

    if not match.empty:
        ticker = match.iloc[0]["company_id"]
        company_name = match.iloc[0]["company_name"]
    else:
        st.error("Company not found")
        st.stop()
else:
    st.info("Please search or select a company")
    st.stop()

# Load ratio data
try:
    ratios_data = get_ratios(ticker)
except Exception as e:
    st.error(f"Error loading ratio data: {e}")
    ratios_data = pd.DataFrame()

if ratios_data.empty:
    st.warning("No ratio data available for this company")
    st.stop()

# Metric selector (max 3 metrics)
available_metrics = [
    "return_on_equity_pct",
    "roce_pct",
    "debt_to_equity",
    "net_profit_margin_pct",
    "operating_profit_margin_pct",
    "asset_turnover",
    "free_cash_flow_cr",
    "revenue_cagr_5yr",
    "pat_cagr_5yr",
]

metric_labels = {
    "return_on_equity_pct": "ROE (%)",
    "roce_pct": "ROCE (%)",
    "debt_to_equity": "D/E",
    "net_profit_margin_pct": "NPM (%)",
    "operating_profit_margin_pct": "OPM (%)",
    "asset_turnover": "Asset Turnover",
    "free_cash_flow_cr": "FCF (Cr)",
    "revenue_cagr_5yr": "Revenue CAGR (%)",
    "pat_cagr_5yr": "PAT CAGR (%)",
}

available_display_metrics = [m for m in available_metrics if m in ratios_data.columns]

selected_metrics = st.multiselect(
    "Select Metrics (max 3)",
    options=available_display_metrics,
    format_func=lambda x: metric_labels.get(x, x),
    max_selections=3,
    default=(
        ["return_on_equity_pct", "debt_to_equity"]
        if "return_on_equity_pct" in available_display_metrics
        else available_display_metrics[:2]
    ),
)

if not selected_metrics:
    st.warning("Please select at least one metric")
    st.stop()

# 10-year trend chart
st.subheader(f"10-Year Trend: {company_name}")

ratios_sorted = ratios_data.sort_values("year").tail(10)

fig = go.Figure()

colors = ["blue", "green", "orange", "red", "purple"]
for i, metric in enumerate(selected_metrics):
    fig.add_trace(
        go.Scatter(
            x=ratios_sorted["year"],
            y=ratios_sorted[metric],
            mode="lines+markers",
            name=metric_labels.get(metric, metric),
            line=dict(color=colors[i % len(colors)]),
        )
    )

fig.update_layout(
    xaxis_title="Year",
    yaxis_title="Value",
    height=400,
    hovermode="x unified",
    margin=dict(l=20, r=20, t=40, b=20),
)

st.plotly_chart(fig, use_container_width=True)

# YoY change annotations
st.subheader("Year-over-Year Changes (%)")


def calculate_yoy_change(current, previous):
    """Calculate YoY percentage change safely."""
    if pd.isna(current) or pd.isna(previous) or current is None or previous is None:
        return None
    try:
        curr_val = float(current)
        prev_val = float(previous)
        if prev_val == 0:
            return None
        return ((curr_val - prev_val) / abs(prev_val)) * 100.0
    except (ValueError, TypeError):
        return None


# Create YoY change table
yoy_data = []
ratios_sorted = ratios_data.sort_values("year")

for i in range(len(ratios_sorted)):
    if i == 0:
        continue  # Skip first year (no previous year available)

    current_row = ratios_sorted.iloc[i]
    prev_row = ratios_sorted.iloc[i - 1]

    row_data = {"Year": f"{current_row['year']} (vs {prev_row['year']})"}
    for metric in selected_metrics:
        current_val = current_row.get(metric)
        prev_val = prev_row.get(metric)
        yoy_change = calculate_yoy_change(current_val, prev_val)
        row_data[metric_labels.get(metric, metric)] = yoy_change

    yoy_data.append(row_data)

if yoy_data:
    yoy_df = pd.DataFrame(yoy_data)

    # Format for display
    for metric in selected_metrics:
        label = metric_labels.get(metric, metric)
        if label in yoy_df.columns:
            yoy_df[label] = yoy_df[label].apply(
                lambda x: f"{x:+.2f}%" if pd.notna(x) and x is not None else LABEL_NA
            )

    st.dataframe(yoy_df, use_container_width=True, height=350)
else:
    st.info("Insufficient historical data for Year-over-Year analysis")
