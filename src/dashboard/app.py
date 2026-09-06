"""
Nifty 100 Analytics Dashboard
Main Streamlit application entry point
"""

import streamlit as st
from pathlib import Path

st.set_page_config(
    page_title="Nifty 100 Analytics",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("Nifty 100 Analytics Dashboard")
st.markdown("---")

PAGES = {
    "Home": "pages/01_home.py",
    "Company Profile": "pages/02_profile.py",
    "Screener": "pages/03_screener.py",
    "Peer Comparison": "pages/04_peers.py",
    "Trend Analysis": "pages/05_trends.py",
    "Sector Analysis": "pages/06_sectors.py",
    "Capital Allocation": "pages/07_capital.py",
    "Annual Reports": "pages/08_reports.py"
}

st.sidebar.title("Navigation")
selection = st.sidebar.radio("Go to", list(PAGES.keys()))

if selection:
    page_path = Path(__file__).parent / PAGES[selection]
    try:
        with open(page_path, "r", encoding="utf-8") as f:
            exec(f.read())
    except FileNotFoundError:
        st.error(f"Page not found: {page_path}")
    except Exception as e:
        st.error(f"Error loading page: {e}")
