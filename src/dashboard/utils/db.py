"""
Dashboard Database Utilities
Cached database loaders for Streamlit dashboard
"""

import sqlite3
import streamlit as st
import pandas as pd
from typing import Optional, List, Dict, Any
from pathlib import Path

from src.dashboard.config import DB_PATH


def get_connection() -> sqlite3.Connection:
    """Get SQLite database connection."""
    db_path = Path(DB_PATH)
    if not db_path.exists():
        db_path = Path(f"../{DB_PATH}")
    return sqlite3.connect(str(db_path))


@st.cache_data(ttl=600)
def get_companies() -> pd.DataFrame:
    """Get all companies with basic info."""
    conn = get_connection()
    try:
        query = """
        SELECT 
            c.company_id,
            c.company_name,
            c.nse_profile,
            s.broad_sector,
            s.sub_sector,
            c.about_company
        FROM companies c
        LEFT JOIN sectors s ON c.company_id = s.company_id
        ORDER BY c.company_name
        """
        df = pd.read_sql_query(query, conn)
        return df
    finally:
        conn.close()


@st.cache_data(ttl=600)
def get_ratios(ticker: str, year: Optional[int] = None) -> pd.DataFrame:
    """Get financial ratios for a company."""
    conn = get_connection()
    try:
        if year:
            query = """
            SELECT * FROM financial_ratios 
            WHERE company_id = ? AND year = ?
            """
            df = pd.read_sql_query(query, conn, params=(ticker, year))
        else:
            query = """
            SELECT * FROM financial_ratios 
            WHERE company_id = ?
            ORDER BY year DESC
            """
            df = pd.read_sql_query(query, conn, params=(ticker,))
        return df
    finally:
        conn.close()


@st.cache_data(ttl=600)
def get_pl(ticker: str) -> pd.DataFrame:
    """Get profit & loss data for a company."""
    conn = get_connection()
    try:
        query = """
        SELECT * FROM profitandloss 
        WHERE company_id = ?
        ORDER BY year DESC
        """
        df = pd.read_sql_query(query, conn, params=(ticker,))
        return df
    finally:
        conn.close()


@st.cache_data(ttl=600)
def get_bs(ticker: str) -> pd.DataFrame:
    """Get balance sheet data for a company."""
    conn = get_connection()
    try:
        query = """
        SELECT * FROM balancesheet 
        WHERE company_id = ?
        ORDER BY year DESC
        """
        df = pd.read_sql_query(query, conn, params=(ticker,))
        return df
    finally:
        conn.close()


@st.cache_data(ttl=600)
def get_cf(ticker: str) -> pd.DataFrame:
    """Get cash flow data for a company."""
    conn = get_connection()
    try:
        query = """
        SELECT * FROM cashflow 
        WHERE company_id = ?
        ORDER BY year DESC
        """
        df = pd.read_sql_query(query, conn, params=(ticker,))
        return df
    finally:
        conn.close()


@st.cache_data(ttl=600)
def get_sectors() -> pd.DataFrame:
    """Get all sector classifications."""
    conn = get_connection()
    try:
        query = """
        SELECT 
            company_id,
            broad_sector,
            sub_sector,
            market_cap_category
        FROM sectors
        """
        df = pd.read_sql_query(query, conn)
        return df
    finally:
        conn.close()


@st.cache_data(ttl=600)
def get_peers(group_name: str) -> pd.DataFrame:
    """Get companies in a peer group."""
    conn = get_connection()
    try:
        query = """
        WITH LatestRatios AS (
            SELECT f.*,
                   ROW_NUMBER() OVER (PARTITION BY f.company_id ORDER BY f.year DESC) as rn
            FROM financial_ratios f
        )
        SELECT 
            c.company_id,
            c.company_name,
            s.broad_sector,
            s.sub_sector,
            pg.peer_group_name,
            pg.is_benchmark,
            lr.*
        FROM companies c
        LEFT JOIN sectors s ON c.company_id = s.company_id
        LEFT JOIN peer_groups pg ON c.company_id = pg.company_id
        LEFT JOIN LatestRatios lr ON c.company_id = lr.company_id AND lr.rn = 1
        WHERE pg.peer_group_name = ? OR s.sub_sector = ? OR s.broad_sector = ?
        """
        df = pd.read_sql_query(query, conn, params=(group_name, group_name, group_name))
        return df
    finally:
        conn.close()


@st.cache_data(ttl=600)
def get_valuation(ticker: str) -> pd.DataFrame:
    """Get valuation data for a company."""
    conn = get_connection()
    try:
        query = """
        SELECT * FROM market_cap 
        WHERE company_id = ?
        ORDER BY year DESC
        """
        df = pd.read_sql_query(query, conn, params=(ticker,))
        return df
    finally:
        conn.close()


@st.cache_data(ttl=600)
def get_latest_ratios_all() -> pd.DataFrame:
    """Get latest financial ratios for all companies with optimized query."""
    conn = get_connection()
    try:
        query = """
        WITH LatestRatios AS (
            SELECT f.*,
                   ROW_NUMBER() OVER (PARTITION BY f.company_id ORDER BY f.year DESC) as rn
            FROM financial_ratios f
        )
        SELECT 
            lr.company_id,
            c.company_name,
            s.broad_sector,
            s.sub_sector,
            lr.year,
            lr.return_on_equity_pct,
            lr.roce_pct,
            lr.debt_to_equity,
            lr.net_profit_margin_pct,
            lr.operating_profit_margin_pct,
            lr.asset_turnover,
            lr.free_cash_flow_cr,
            lr.revenue_cagr_5yr,
            lr.pat_cagr_5yr,
            lr.interest_coverage,
            lr.composite_quality_score,
            lr.capital_allocation_pattern
        FROM LatestRatios lr
        JOIN companies c ON lr.company_id = c.company_id
        LEFT JOIN sectors s ON lr.company_id = s.company_id
        WHERE lr.rn = 1
        """
        df = pd.read_sql_query(query, conn)
        return df
    finally:
        conn.close()


@st.cache_data(ttl=600)
def get_documents(ticker: str) -> pd.DataFrame:
    """Get annual report documents for a company."""
    conn = get_connection()
    try:
        query = """
        SELECT * FROM documents 
        WHERE company_id = ?
        ORDER BY year DESC
        """
        df = pd.read_sql_query(query, conn, params=(ticker,))
        return df
    finally:
        conn.close()


@st.cache_data(ttl=600)
def get_pros_cons(ticker: str) -> pd.DataFrame:
    """Get pros and cons for a company."""
    conn = get_connection()
    try:
        query = """
        SELECT * FROM prosandcons 
        WHERE company_id = ?
        """
        df = pd.read_sql_query(query, conn, params=(ticker,))
        return df
    finally:
        conn.close()
