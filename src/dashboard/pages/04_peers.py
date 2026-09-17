"""
Peer Comparison Screen
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from pathlib import Path

from src.dashboard.utils.db import get_sectors, get_peers
from src.dashboard.utils.ui import company_selector, safe_render, render_simulated_warning

st.title("Peer Comparison")

@safe_render()
def render_peer_comparison():
    # Peer group dropdown
    sectors_df = get_sectors()
    if sectors_df.empty:
        st.warning("No sector data available.")
        return
        
    peer_groups = sorted(sectors_df["broad_sector"].dropna().unique().tolist())
    
    col1, col2 = st.columns([1, 2])
    with col1:
        selected_group = st.selectbox(
            "Select Peer Group",
            options=peer_groups,
            help="Select a sector/peer group for comparison",
        )
    
    if not selected_group:
        st.info("Please select a peer group to begin.")
        return

    # Load peer data
    peer_data = get_peers(selected_group)
    if peer_data.empty:
        st.warning(f"No data available for peer group: {selected_group}")
        return

    with col2:
        company_options = ["Select a benchmark company..."] + sorted(peer_data["company_name"].tolist())
        selected_company = st.selectbox(
            "Select Benchmark Company",
            options=company_options,
            index=0,
            help="Select a company to compare against its peer group average",
        )

    st.markdown("---")
    
    count = len(peer_data)
    st.markdown(f"### {selected_group} ({count} Companies)")

    # Prepare peer comparison data
    if selected_company and selected_company != "Select a benchmark company...":
        benchmark = peer_data[peer_data["company_name"] == selected_company]
        if benchmark.empty:
            st.error("Selected company not found in this peer group.")
            return
        benchmark_data = benchmark.iloc[0]
        peers_excluding_benchmark = peer_data[peer_data["company_name"] != benchmark_data["company_name"]]
    else:
        benchmark_data = peer_data.iloc[0]
        peers_excluding_benchmark = peer_data.iloc[1:]

    peer_avg = peers_excluding_benchmark.mean(numeric_only=True) if not peers_excluding_benchmark.empty else benchmark_data
    
    # Display simple comparison metrics
    metric_cols = st.columns(4)
    compare_fields = [
        ("return_on_equity_pct", "ROE (%)"),
        ("roce_pct", "ROCE (%)"),
        ("debt_to_equity", "D/E Ratio"),
        ("net_profit_margin_pct", "Net Profit Margin (%)")
    ]
    
    for idx, (col_key, col_label) in enumerate(compare_fields):
        b_val = benchmark_data.get(col_key, 0)
        p_val = peer_avg.get(col_key, 0)
        
        with metric_cols[idx]:
            if pd.notna(b_val) and pd.notna(p_val):
                diff = b_val - p_val
                if col_key == "debt_to_equity":
                    # Lower D/E is better
                    delta_color = "inverse"
                else:
                    delta_color = "normal"
                st.metric(f"Benchmark {col_label}", f"{b_val:.2f}", delta=f"{diff:+.2f} vs Peers", delta_color=delta_color)
            else:
                st.metric(f"Benchmark {col_label}", "N/A")

    st.markdown("---")
    
    # Radar chart comparison
    st.subheader("Multidimensional Performance Profile")

    metric_labels = [
        "ROE", "ROCE", "D/E", "NPM", "OPM", 
        "Asset Turnover", "FCF (norm)", "Rev CAGR"
    ]

    def normalize_for_radar(value, metric_name):
        try:
            val = float(value) if pd.notna(value) else 0.0
        except (ValueError, TypeError):
            val = 0.0

        if metric_name == "D/E":
            return max(0.0, float(100.0 - min(val * 20.0, 100.0)))
        elif metric_name == "FCF (norm)":
            return max(0.0, float(min(val / 50.0, 100.0)))
        else:
            return max(0.0, float(min(val, 100.0)))

    def build_radar_array(data_source):
        return [
            normalize_for_radar(data_source.get("return_on_equity_pct", 0), "ROE"),
            normalize_for_radar(data_source.get("roce_pct", 0), "ROCE"),
            normalize_for_radar(data_source.get("debt_to_equity", 0), "D/E"),
            normalize_for_radar(data_source.get("net_profit_margin_pct", 0), "NPM"),
            normalize_for_radar(data_source.get("operating_profit_margin_pct", 0), "OPM"),
            normalize_for_radar(data_source.get("asset_turnover", 0), "Asset Turnover"),
            normalize_for_radar(data_source.get("free_cash_flow_cr", 0), "FCF (norm)"),
            normalize_for_radar(data_source.get("revenue_cagr_5yr", 0), "Rev CAGR"),
        ]

    b_radar = build_radar_array(benchmark_data)
    p_radar = build_radar_array(peer_avg)

    # Close polygon
    b_radar.append(b_radar[0])
    p_radar.append(p_radar[0])
    radar_labels = metric_labels + [metric_labels[0]]

    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=b_radar, theta=radar_labels, fill="toself",
        name=f"⭐ {benchmark_data['company_name']}",
        line_color="#1f77b4"
    ))
    fig.add_trace(go.Scatterpolar(
        r=p_radar, theta=radar_labels, fill="toself",
        name=f"🌐 {selected_group} Average",
        line_color="#ff7f0e"
    ))
    fig.update_layout(
        polar=dict(radialaxis=dict(visible=False, range=[0, 100])),
        showlegend=True, height=500, margin=dict(l=20, r=20, t=20, b=20),
        legend=dict(orientation="h", yanchor="bottom", y=1.05, xanchor="center", x=0.5)
    )
    
    st.plotly_chart(fig, use_container_width=True)

    # KPI comparison table
    st.markdown("---")
    st.subheader("Detailed Peer Group Rankings")

    table_cols = [
        "company_name", "return_on_equity_pct", "roce_pct", "debt_to_equity",
        "net_profit_margin_pct", "operating_profit_margin_pct", 
        "asset_turnover", "free_cash_flow_cr", "revenue_cagr_5yr"
    ]
    
    available_table_cols = [col for col in table_cols if col in peer_data.columns]
    comparison_df = peer_data[available_table_cols].copy()

    for col in available_table_cols:
        if col != "company_name":
            comparison_df[col] = pd.to_numeric(comparison_df[col], errors="coerce").round(2)

    # Highlight benchmark row
    benchmark_name = benchmark_data["company_name"]
    def highlight_row(row):
        return ['background-color: rgba(31, 119, 180, 0.2)' if row['Company Name'] == benchmark_name else '' for _ in row]

    col_rename = {
        "company_name": "Company Name",
        "return_on_equity_pct": "ROE (%)",
        "roce_pct": "ROCE (%)",
        "debt_to_equity": "D/E",
        "net_profit_margin_pct": "NPM (%)",
        "operating_profit_margin_pct": "OPM (%)",
        "asset_turnover": "Asset Turnover",
        "free_cash_flow_cr": "FCF (Cr)",
        "revenue_cagr_5yr": "Rev CAGR (%)",
    }
    comparison_df = comparison_df.rename(columns=col_rename)
    
    # Render with Pandas Styler for row highlighting
    styler = comparison_df.style.apply(highlight_row, axis=1)
    st.dataframe(styler, use_container_width=True, height=400, hide_index=True)

    st.markdown("---")
    report_path = Path("reports/peer_comparison.xlsx")
    if report_path.exists():
        with open(report_path, "rb") as f:
            st.download_button(
                label="📥 Download Complete Peer Comparison Report (XLSX)",
                data=f,
                file_name="peer_comparison.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
    else:
        st.info("The official Peer Comparison report file is currently unavailable.")

render_peer_comparison()
