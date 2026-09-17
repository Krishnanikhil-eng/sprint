"""
Shared UI Utilities for Streamlit Dashboard
Provides consistent formatting, layouts, and error handling.
"""

import streamlit as st
import pandas as pd
from typing import Optional, Tuple, Any, Callable
from functools import wraps

from src.dashboard.utils.db import get_companies
from src.dashboard.config import LABEL_NA

def format_currency(value: Any, suffix: str = "Cr") -> str:
    """Format large numbers into currency strings."""
    if pd.isna(value) or value is None:
        return LABEL_NA
    try:
        val_float = float(value)
        return f"₹{val_float:,.2f} {suffix}"
    except (ValueError, TypeError):
        return LABEL_NA

def format_percentage(value: Any) -> str:
    """Format numbers into percentage strings."""
    if pd.isna(value) or value is None:
        return LABEL_NA
    try:
        val_float = float(value)
        return f"{val_float:,.2f}%"
    except (ValueError, TypeError):
        return LABEL_NA

def format_ratio(value: Any, suffix: str = "x") -> str:
    """Format numbers into ratio strings."""
    if pd.isna(value) or value is None:
        return LABEL_NA
    try:
        val_float = float(value)
        return f"{val_float:,.2f}{suffix}"
    except (ValueError, TypeError):
        return LABEL_NA

def render_simulated_warning():
    """Render a consistent simulated data warning."""
    st.warning("⚠️ **[SIMULATED DATA]** Market capitalization and stock prices are simulated for demonstration purposes.")

def company_selector() -> Tuple[Optional[str], Optional[pd.Series]]:
    """
    Renders a consistent company selector across pages.
    Returns: (ticker_id, company_data_series)
    """
    try:
        companies_df = get_companies()
    except Exception as e:
        st.error(f"Error loading companies database: {e}")
        return None, None

    if companies_df.empty:
        st.warning("No companies available in database.")
        return None, None

    # Create descriptive options
    companies_df["display_name"] = companies_df.apply(
        lambda x: f"{x['company_id']} — {x['company_name']} ({x.get('broad_sector', 'Unknown Sector')})", 
        axis=1
    )
    
    options = ["Select a company..."] + companies_df["display_name"].tolist()
    
    selected_option = st.selectbox(
        "Select Company",
        options=options,
        index=0,
        help="Search by Ticker or Company Name"
    )
    
    if selected_option and selected_option != "Select a company...":
        ticker = selected_option.split(" — ")[0]
        match = companies_df[companies_df["company_id"] == ticker]
        if not match.empty:
            return ticker, match.iloc[0]
            
    return None, None

def render_error_state(msg: str):
    """Render a clean error state instead of a raw traceback."""
    st.info(f"ℹ️ {msg}")

def safe_render(fallback_msg: str = "Data unavailable for the selected parameters."):
    """Decorator to catch exceptions and render clean UI messages."""
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except KeyError as e:
                render_error_state(f"Missing data column: {e}")
            except Exception as e:
                render_error_state(fallback_msg)
                # Log internally if needed, but don't show traceback
        return wrapper
    return decorator
