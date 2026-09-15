"""
Dashboard Shared Configuration
Centralized constants and settings for all dashboard pages
"""

# Page titles
PAGE_TITLES = {
    "home": "Home",
    "profile": "Company Profile",
    "screener": "Stock Screener",
    "peers": "Peer Comparison",
    "trends": "Trend Analysis",
    "sectors": "Sector Analysis",
    "capital": "Capital Allocation",
    "reports": "Annual Reports"
}

# Supported years for analysis
SUPPORTED_YEARS = [2019, 2020, 2021, 2022, 2023, 2024]
DEFAULT_YEAR = 2024

# Sector names (11 broad sectors)
SECTORS = [
    "Financials",
    "IT",
    "FMCG",
    "Healthcare",
    "Energy",
    "Consumer Durables",
    "Automobile",
    "Capital Goods",
    "Metals & Mining",
    "Chemicals",
    "Telecom"
]

# Display settings
CHART_HEIGHT = 400
CHART_WIDTH = None  # Auto-fit
TABLE_HEIGHT = 400
MAX_WIDTH = 1200  # Maximum container width for responsiveness

# Common labels
LABEL_NA = "N/A"
LABEL_NOT_AVAILABLE = "Not Available"
LABEL_NO_DATA = "No data available"

# Metric display formatting
METRIC_FORMATS = {
    "percentage": "{:.2f}%",
    "currency": "₹{:.2f} Cr",
    "ratio": "{:.2f}",
    "cagr": "{:.2f}%",
    "integer": "{:.0f}"
}

# Screener filter defaults
SCREENER_DEFAULTS = {
    "min_roe": 10.0,
    "max_de": 2.0,
    "min_fcf": 0.0,
    "min_revenue_cagr": 5.0,
    "min_pat_cagr": 5.0,
    "min_opm": 10.0,
    "max_pe": 30.0,
    "max_pb": 5.0,
    "min_dividend_yield": 0.0,
    "min_icr": 2.0
}

# Preset strategies
PRESET_STRATEGIES = {
    "Quality": {"min_roe": 15.0, "max_de": 1.0, "min_opm": 15.0},
    "Value": {"max_pe": 20.0, "max_pb": 3.0, "min_dividend_yield": 2.0},
    "Growth": {"min_revenue_cagr": 10.0, "min_pat_cagr": 10.0, "min_roe": 12.0},
    "Dividend": {"min_dividend_yield": 3.0, "max_de": 1.5, "min_roe": 10.0},
    "Debt-Free": {"max_de": 0.1, "min_fcf": 0.0},
    "Turnaround": {"min_revenue_cagr": -5.0, "min_pat_cagr": -5.0, "min_roe": 5.0}
}

# Database path
DB_PATH = "nifty100.db"
