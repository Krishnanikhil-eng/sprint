"""
Report Center Screen
"""

import streamlit as st
import pandas as pd
import requests
from pathlib import Path
import os

from src.dashboard.utils.db import get_companies, get_documents
from src.dashboard.utils.ui import company_selector, safe_render
from src.dashboard.config import LABEL_NA

st.title("Report Center")
st.markdown("Download generated financial analysis reports, institutional tearsheets, and external documents.")

@st.cache_data(ttl=3600)
def validate_url(url: str) -> bool:
    if not isinstance(url, str) or not url.strip(): return False
    url = url.strip()
    if not (url.startswith("http://") or url.startswith("https://")): return False
    try:
        res = requests.head(url, timeout=1.5, allow_redirects=True)
        if res.status_code == 200: return True
        if res.status_code == 404: return False
        res_get = requests.get(url, timeout=1.5, stream=True)
        return res_get.status_code == 200
    except Exception:
        return len(url) > 12 and "bseindia.com" in url

def render_file_download(filepath: str, label: str, help_text: str = ""):
    path = Path(filepath)
    if path.exists():
        with open(path, "rb") as f:
            st.download_button(
                label=f"📥 {label}",
                data=f,
                file_name=path.name,
                help=help_text,
                use_container_width=True,
                type="primary"
            )
    else:
        st.button(f"🚫 {label} (File Missing)", disabled=True, use_container_width=True, help=f"Expected at {filepath}")

def render_directory_downloads(dirpath: str, ext: str = ".pdf"):
    path = Path(dirpath)
    if path.exists() and path.is_dir():
        files = list(path.glob(f"*{ext}"))
        if not files:
            st.info(f"No {ext} files found in {dirpath}.")
            return
        
        # Display in columns for neatness
        cols = st.columns(3)
        for idx, f in enumerate(sorted(files)):
            with cols[idx % 3]:
                with open(f, "rb") as file_data:
                    st.download_button(
                        label=f"📄 {f.name}",
                        data=file_data,
                        file_name=f.name,
                        use_container_width=True
                    )
    else:
        st.warning(f"Directory {dirpath} does not exist.")

@safe_render()
def render_report_center():
    tabs = st.tabs([
        "🏢 Company Reports",
        "🏭 Sector Reports",
        "📈 Portfolio Reports",
        "💰 Valuation & Screening",
        "💸 Cash Flow & Capital",
        "🧠 NLP Analysis",
        "🕸️ Radar Charts"
    ])

    with tabs[0]:
        st.subheader("Official Company Tearsheets")
        render_directory_downloads("reports/tearsheets", ".pdf")
        
        st.markdown("---")
        st.subheader("BSE Annual Report Links")
        
        ticker, company_data = company_selector()
        if ticker:
            docs = get_documents(ticker)
            if not docs.empty:
                for _, row in docs.iterrows():
                    year = row.get("year", LABEL_NA)
                    url = str(row.get("annual_report", "")).strip()
                    c1, c2 = st.columns([3, 1])
                    c1.markdown(f"**FY{year} Annual Report**")
                    if validate_url(url):
                        c2.markdown(f"🔗 [Download PDF]({url})")
                    else:
                        c2.markdown("🔴 *Link Broken/Unavailable*")
                    st.markdown("---")
            else:
                st.info("No BSE links available for this company.")

    with tabs[1]:
        st.subheader("Sector Analysis Reports")
        render_directory_downloads("reports/sector", ".pdf")

    with tabs[2]:
        st.subheader("Portfolio & Thematic Reports")
        render_directory_downloads("reports/portfolio", ".pdf")
        st.markdown("---")
        col1, col2 = st.columns(2)
        with col1:
            render_file_download("output/portfolio_stats.csv", "Portfolio Stats CSV")
        with col2:
            render_file_download("reports/correlation_heatmap.png", "Correlation Heatmap PNG")

    with tabs[3]:
        st.subheader("Valuation & Screening Data")
        c1, c2 = st.columns(2)
        with c1:
            render_file_download("output/screener_output.xlsx", "Screener Results XLSX", "Filtered institutional screener results")
            render_file_download("output/peer_comparison.xlsx", "Peer Comparison XLSX", "Detailed peer metrics")
        with c2:
            render_file_download("output/valuation_summary.xlsx", "Valuation Summary XLSX", "Intrinsic valuation models")
            render_file_download("output/valuation_flags.csv", "Valuation Flags CSV", "Overvalued/Undervalued flags")

    with tabs[4]:
        st.subheader("Cash Flow & Capital Allocation")
        c1, c2 = st.columns(2)
        with c1:
            render_file_download("output/cashflow_intelligence.xlsx", "Cashflow Intelligence XLSX")
        with c2:
            render_file_download("output/capital_allocation.csv", "Capital Allocation Models CSV")

    with tabs[5]:
        st.subheader("NLP Qualitative Analysis")
        render_file_download("output/pros_cons_generated.csv", "Pros & Cons Analysis CSV", "Generated strengths and weaknesses")
        render_file_download("output/distress_alerts.csv", "Distress Alerts CSV", "Flagged financial risks")

    with tabs[6]:
        st.subheader("Radar Chart Visualizations")
        render_directory_downloads("reports/radar_charts", ".png")

render_report_center()
