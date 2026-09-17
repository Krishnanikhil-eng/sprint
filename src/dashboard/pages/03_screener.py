"""
Stock Screener Screen
"""

import streamlit as st
import pandas as pd
from pathlib import Path

from src.dashboard.utils.db import get_latest_ratios_all
from src.dashboard.config import SCREENER_DEFAULTS, PRESET_STRATEGIES
from src.dashboard.utils.ui import safe_render

st.title("Financial Screener")

@safe_render()
def render_screener():
    ratios_df = get_latest_ratios_all()
    if ratios_df.empty:
        st.warning("No financial data available for screening.")
        return

    # Sidebar Filter Presets
    st.sidebar.markdown("### Screener Presets")
    
    filter_keys = [
        "min_roe", "max_de", "min_fcf", "min_revenue_cagr", 
        "min_pat_cagr", "min_opm", "max_pe", "max_pb", 
        "min_dividend_yield", "min_icr"
    ]

    for key in filter_keys:
        if f"filter_{key}" not in st.session_state:
            st.session_state[f"filter_{key}"] = SCREENER_DEFAULTS.get(key, 0.0)

    def apply_preset():
        selected_preset = st.session_state.preset_selector
        if selected_preset in PRESET_STRATEGIES:
            preset_dict = PRESET_STRATEGIES[selected_preset]
            for key in filter_keys:
                st.session_state[f"filter_{key}"] = float(preset_dict.get(key, SCREENER_DEFAULTS.get(key, 0.0)))

    selected_preset = st.sidebar.selectbox(
        "Institutional Strategies",
        options=["Custom"] + list(PRESET_STRATEGIES.keys()),
        key="preset_selector",
        on_change=apply_preset,
        help="Pre-defined filter combinations based on classic institutional strategies."
    )
    
    if selected_preset != "Custom":
        st.sidebar.caption(f"Applied: {selected_preset}")

    st.sidebar.markdown("---")
    st.sidebar.markdown("### Manual Filters")

    with st.sidebar.expander("Profitability & Return", expanded=True):
        min_roe = st.number_input("Min ROE (%)", min_value=-50.0, max_value=100.0, step=0.5, key="filter_min_roe")
        min_opm = st.number_input("Min OPM (%)", min_value=-50.0, max_value=100.0, step=0.5, key="filter_min_opm")

    with st.sidebar.expander("Valuation", expanded=False):
        max_pe = st.number_input("Max P/E", min_value=0.0, max_value=1000.0, step=1.0, key="filter_max_pe")
        max_pb = st.number_input("Max P/B", min_value=0.0, max_value=100.0, step=0.5, key="filter_max_pb")
        min_dividend_yield = st.number_input("Min Div Yield (%)", min_value=0.0, max_value=20.0, step=0.1, key="filter_min_dividend_yield")

    with st.sidebar.expander("Financial Health", expanded=False):
        max_de = st.number_input("Max D/E", min_value=0.0, max_value=50.0, step=0.1, key="filter_max_de")
        min_icr = st.number_input("Min ICR", min_value=0.0, max_value=100.0, step=0.5, key="filter_min_icr")
        min_fcf = st.number_input("Min FCF (Cr)", min_value=-50000.0, max_value=100000.0, step=10.0, key="filter_min_fcf")

    with st.sidebar.expander("Growth (5-Year CAGR)", expanded=False):
        min_revenue_cagr = st.number_input("Min Revenue CAGR (%)", min_value=-50.0, max_value=100.0, step=1.0, key="filter_min_revenue_cagr")
        min_pat_cagr = st.number_input("Min PAT CAGR (%)", min_value=-50.0, max_value=100.0, step=1.0, key="filter_min_pat_cagr")

    # Apply filters
    filtered_df = ratios_df.copy()

    if "return_on_equity_pct" in filtered_df.columns:
        filtered_df = filtered_df[filtered_df["return_on_equity_pct"].fillna(-999) >= min_roe]
    if "debt_to_equity" in filtered_df.columns:
        filtered_df = filtered_df[filtered_df["debt_to_equity"].fillna(999) <= max_de]
    if "free_cash_flow_cr" in filtered_df.columns:
        filtered_df = filtered_df[filtered_df["free_cash_flow_cr"].fillna(-99999) >= min_fcf]
    if "revenue_cagr_5yr" in filtered_df.columns:
        filtered_df = filtered_df[filtered_df["revenue_cagr_5yr"].fillna(-999) >= min_revenue_cagr]
    if "pat_cagr_5yr" in filtered_df.columns:
        filtered_df = filtered_df[filtered_df["pat_cagr_5yr"].fillna(-999) >= min_pat_cagr]
    if "operating_profit_margin_pct" in filtered_df.columns:
        filtered_df = filtered_df[filtered_df["operating_profit_margin_pct"].fillna(-999) >= min_opm]
    if "pe_ratio" in filtered_df.columns and max_pe < 1000.0:
        filtered_df = filtered_df[filtered_df["pe_ratio"].fillna(9999) <= max_pe]
    if "pb_ratio" in filtered_df.columns and max_pb < 100.0:
        filtered_df = filtered_df[filtered_df["pb_ratio"].fillna(9999) <= max_pb]
    if "dividend_yield_pct" in filtered_df.columns:
        filtered_df = filtered_df[filtered_df["dividend_yield_pct"].fillna(0) >= min_dividend_yield]
    if "interest_coverage" in filtered_df.columns:
        filtered_df = filtered_df[filtered_df["interest_coverage"].fillna(0) >= min_icr]

    # Main content
    count = len(filtered_df)
    st.markdown(f"### Results: {count} Companies")
    
    if not filtered_df.empty:
        display_cols = [
            "company_name", "broad_sector", "composite_quality_score", 
            "return_on_equity_pct", "debt_to_equity", "pe_ratio", 
            "pb_ratio", "dividend_yield_pct", "free_cash_flow_cr", 
            "revenue_cagr_5yr", "pat_cagr_5yr", "operating_profit_margin_pct", 
            "interest_coverage"
        ]
        
        available_cols = [c for c in display_cols if c in filtered_df.columns]
        results_df = filtered_df[available_cols].copy()
        
        # Format metrics cleanly
        numeric_cols = [c for c in available_cols if c not in ["company_name", "broad_sector"]]
        for col in numeric_cols:
            results_df[col] = pd.to_numeric(results_df[col], errors="coerce").round(2)
            
        column_rename = {
            "company_name": "Company",
            "broad_sector": "Sector",
            "composite_quality_score": "Score",
            "return_on_equity_pct": "ROE(%)",
            "debt_to_equity": "D/E",
            "pe_ratio": "P/E",
            "pb_ratio": "P/B",
            "dividend_yield_pct": "Div Yield(%)",
            "free_cash_flow_cr": "FCF(Cr)",
            "revenue_cagr_5yr": "Rev CAGR(%)",
            "pat_cagr_5yr": "PAT CAGR(%)",
            "operating_profit_margin_pct": "OPM(%)",
            "interest_coverage": "ICR",
        }
        results_df = results_df.rename(columns=column_rename)
        
        # Display styled dataframe
        st.dataframe(
            results_df,
            use_container_width=True,
            hide_index=True,
            height=500
        )
        
        # Export Actions
        col1, col2 = st.columns([1, 4])
        with col1:
            csv_data = results_df.to_csv(index=False)
            st.download_button(
                label="📥 Download Displayed Results (CSV)",
                data=csv_data,
                file_name="custom_screener_results.csv",
                mime="text/csv",
                use_container_width=True
            )
        
        with col2:
            # Provide link to the official pipeline generated report if it exists
            report_path = Path("reports/screener_output.xlsx")
            if report_path.exists():
                with open(report_path, "rb") as f:
                    st.download_button(
                        label="📥 Download Official Institutional Report (XLSX)",
                        data=f,
                        file_name="screener_output.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=False,
                        type="secondary"
                    )
    else:
        st.info("No companies match the current filter criteria. Try relaxing the constraints.")

render_screener()
