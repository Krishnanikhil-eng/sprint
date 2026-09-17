"""
Nifty 100 Analytics Dashboard
Main Streamlit application entry point
"""

import streamlit as st
import sys
from pathlib import Path

# Ensure src is in Python path for absolute imports if needed
root_dir = Path(__file__).resolve().parent.parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

st.set_page_config(
    page_title="Nifty 100 Analytics", 
    layout="wide", 
    initial_sidebar_state="expanded"
)

# Main Navigation Setup using st.navigation (Streamlit >= 1.36)
pages = {
    "Dashboards": [
        st.Page("pages/01_home.py", title="Home", icon="🏠"),
        st.Page("pages/02_profile.py", title="Company Profile", icon="🏢"),
    ],
    "Analytics": [
        st.Page("pages/03_screener.py", title="Screener", icon="🔍"),
        st.Page("pages/04_peers.py", title="Peer Comparison", icon="📊"),
        st.Page("pages/05_trends.py", title="Trends", icon="📈"),
        st.Page("pages/06_sectors.py", title="Sector Intelligence", icon="🏭"),
        st.Page("pages/07_capital.py", title="Capital Allocation", icon="💰"),
    ],
    "Documents": [
        st.Page("pages/08_reports.py", title="Report Center", icon="📄"),
    ]
}

pg = st.navigation(pages)

# Global Sidebar Elements
st.sidebar.markdown("---")
st.sidebar.markdown("### NIFTY 100")
st.sidebar.caption("Financial Analytics & Intelligence Platform")
st.sidebar.caption("92 Companies | 11 Sectors")

pg.run()
