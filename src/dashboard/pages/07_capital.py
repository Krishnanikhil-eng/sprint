"""
Capital Allocation Screen
"""

import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path

from src.dashboard.utils.db import get_latest_ratios_all, get_companies
from src.dashboard.utils.ui import safe_render

st.title("Capital Allocation Map")

@safe_render()
def render_capital_allocation():
    ratios_df = get_latest_ratios_all()
    companies_df = get_companies()

    if ratios_df.empty:
        st.warning("Capital allocation data is currently unavailable.")
        return

    # Merge with company names accurately
    merged_df = pd.merge(
        ratios_df, 
        companies_df[["company_id", "company_name"]], 
        on="company_id", 
        how="left"
    )

    if "company_name_y" in merged_df.columns:
        merged_df["company_name"] = merged_df["company_name_y"].fillna(merged_df["company_name_x"])
    elif "company_name_x" in merged_df.columns:
        merged_df["company_name"] = merged_df["company_name_x"]

    if "capital_allocation_pattern" not in merged_df.columns:
        st.warning("Capital allocation classification data is missing.")
        return

    merged_df["capital_allocation_pattern"] = merged_df["capital_allocation_pattern"].fillna("Unclassified")
    
    pattern_counts = merged_df["capital_allocation_pattern"].value_counts().reset_index()
    pattern_counts.columns = ["Pattern", "Count"]

    st.markdown("### Strategic Capital Deployment Patterns")
    st.markdown(f"Analyzing {len(merged_df)} companies categorized by free cash flow and reinvestment characteristics.")

    # Treemap
    treemap_df = merged_df.copy()
    treemap_df["Count"] = 1
    
    # Custom color mapping for common patterns (optional, Plotly does fine if not exact)
    fig = px.treemap(
        treemap_df,
        path=["capital_allocation_pattern", "broad_sector", "company_name"],
        values="Count",
        color="capital_allocation_pattern",
        color_discrete_sequence=px.colors.qualitative.Pastel,
    )
    fig.update_layout(
        height=600,
        margin=dict(l=10, r=10, t=10, b=10)
    )
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")
    
    col1, col2 = st.columns([1, 2])
    with col1:
        st.subheader("Strategy Filter")
        selected_pattern = st.selectbox(
            "Select Allocation Pattern",
            options=pattern_counts["Pattern"].tolist(),
            help="Filter companies by their identified capital allocation strategy."
        )

        st.markdown(f"**Total Companies:** {pattern_counts[pattern_counts['Pattern'] == selected_pattern]['Count'].iloc[0]}")
        
    with col2:
        st.subheader(f"Companies: {selected_pattern}")
        pattern_companies = merged_df[merged_df["capital_allocation_pattern"] == selected_pattern]

        if not pattern_companies.empty:
            display_cols = [
                "company_name", "broad_sector", "return_on_equity_pct",
                "debt_to_equity", "free_cash_flow_cr", "composite_quality_score"
            ]
            
            avail_cols = [c for c in display_cols if c in pattern_companies.columns]
            results_df = pattern_companies[avail_cols].copy()
            
            num_cols = ["return_on_equity_pct", "debt_to_equity", "free_cash_flow_cr", "composite_quality_score"]
            for c in num_cols:
                if c in results_df.columns:
                    results_df[c] = pd.to_numeric(results_df[c], errors="coerce").round(2)

            col_rename = {
                "company_name": "Company",
                "broad_sector": "Sector",
                "return_on_equity_pct": "ROE (%)",
                "debt_to_equity": "D/E",
                "free_cash_flow_cr": "FCF (Cr)",
                "composite_quality_score": "Quality Score"
            }
            results_df = results_df.rename(columns=col_rename)

            st.dataframe(results_df, use_container_width=True, hide_index=True, height=400)
            
            # Export
            report_path = Path("output/capital_allocation.csv")
            if report_path.exists():
                with open(report_path, "rb") as f:
                    st.download_button(
                        label="📥 Download Full Capital Allocation Report (CSV)",
                        data=f,
                        file_name="capital_allocation.csv",
                        mime="text/csv",
                        use_container_width=True
                    )
        else:
            st.info("No companies found for this pattern.")

render_capital_allocation()
