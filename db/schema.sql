-- Database Schema Definition for Nifty 100 ETL Pipeline
-- Database: nifty100.db
-- Enables foreign keys by default in SQLite

PRAGMA foreign_keys = ON;

-- 1. Companies (Parent Table)
CREATE TABLE IF NOT EXISTS companies (
    company_id TEXT PRIMARY KEY,
    company_logo TEXT,
    company_name TEXT,
    chart_link TEXT,
    about_company TEXT,
    website TEXT,
    nse_profile TEXT,
    bse_profile TEXT,
    face_value REAL,
    book_value REAL,
    roce_percentage REAL,
    roe_percentage REAL
);

-- 2. Profit & Loss
CREATE TABLE IF NOT EXISTS profitandloss (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_id TEXT NOT NULL,
    year INTEGER NOT NULL,
    sales REAL,
    expenses REAL,
    operating_profit REAL,
    opm_percentage REAL,
    other_income REAL,
    interest REAL,
    depreciation REAL,
    profit_before_tax REAL,
    tax_percentage REAL,
    net_profit REAL,
    eps REAL,
    dividend_payout REAL,
    FOREIGN KEY (company_id) REFERENCES companies (company_id) ON DELETE CASCADE,
    UNIQUE(company_id, year)
);

-- 3. Balance Sheet
CREATE TABLE IF NOT EXISTS balancesheet (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_id TEXT NOT NULL,
    year INTEGER NOT NULL,
    equity_capital REAL,
    reserves REAL,
    borrowings REAL,
    other_liabilities REAL,
    total_liabilities REAL,
    fixed_assets REAL,
    cwip REAL,
    investments REAL,
    other_asset REAL,
    total_assets REAL,
    FOREIGN KEY (company_id) REFERENCES companies (company_id) ON DELETE CASCADE,
    UNIQUE(company_id, year)
);

-- 4. Cash Flow
CREATE TABLE IF NOT EXISTS cashflow (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_id TEXT NOT NULL,
    year INTEGER NOT NULL,
    operating_activity REAL,
    investing_activity REAL,
    financing_activity REAL,
    net_cash_flow REAL,
    FOREIGN KEY (company_id) REFERENCES companies (company_id) ON DELETE CASCADE,
    UNIQUE(company_id, year)
);

-- 5. Analysis
CREATE TABLE IF NOT EXISTS analysis (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_id TEXT NOT NULL,
    compounded_sales_growth TEXT,
    compounded_profit_growth TEXT,
    stock_price_cagr TEXT,
    roe TEXT,
    FOREIGN KEY (company_id) REFERENCES companies (company_id) ON DELETE CASCADE
);

-- 6. Documents
CREATE TABLE IF NOT EXISTS documents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_id TEXT NOT NULL,
    year INTEGER,
    annual_report TEXT,
    FOREIGN KEY (company_id) REFERENCES companies (company_id) ON DELETE CASCADE
);

-- 7. Pros & Cons
CREATE TABLE IF NOT EXISTS prosandcons (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_id TEXT NOT NULL,
    pros TEXT,
    cons TEXT,
    FOREIGN KEY (company_id) REFERENCES companies (company_id) ON DELETE CASCADE
);

-- 8. Sectors
CREATE TABLE IF NOT EXISTS sectors (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_id TEXT NOT NULL,
    broad_sector TEXT,
    sub_sector TEXT,
    index_weight_pct REAL,
    market_cap_category TEXT,
    FOREIGN KEY (company_id) REFERENCES companies (company_id) ON DELETE CASCADE
);

-- 9. Peer Groups
CREATE TABLE IF NOT EXISTS peer_groups (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    peer_group_name TEXT,
    company_id TEXT NOT NULL,
    is_benchmark INTEGER,
    FOREIGN KEY (company_id) REFERENCES companies (company_id) ON DELETE CASCADE
);

-- 10. Financial Ratios
CREATE TABLE IF NOT EXISTS financial_ratios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_id TEXT NOT NULL,
    year INTEGER NOT NULL,
    net_profit_margin_pct REAL,
    operating_profit_margin_pct REAL,
    return_on_equity_pct REAL,
    debt_to_equity REAL,
    interest_coverage REAL,
    asset_turnover REAL,
    free_cash_flow_cr REAL,
    capex_cr REAL,
    earnings_per_share REAL,
    book_value_per_share REAL,
    dividend_payout_ratio_pct REAL,
    total_debt_cr REAL,
    cash_from_operations_cr REAL,
    FOREIGN KEY (company_id) REFERENCES companies (company_id) ON DELETE CASCADE,
    UNIQUE(company_id, year)
);

-- 11. Stock Prices
CREATE TABLE IF NOT EXISTS stock_prices (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_id TEXT NOT NULL,
    date TEXT NOT NULL,
    open_price REAL,
    high_price REAL,
    low_price REAL,
    close_price REAL,
    volume INTEGER,
    adjusted_close REAL,
    FOREIGN KEY (company_id) REFERENCES companies (company_id) ON DELETE CASCADE,
    UNIQUE(company_id, date)
);

-- 12. Market Cap (Valuation Ratios & Multiples)
CREATE TABLE IF NOT EXISTS market_cap (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_id TEXT NOT NULL,
    year INTEGER NOT NULL,
    market_cap_crore REAL,
    enterprise_value_crore REAL,
    pe_ratio REAL,
    pb_ratio REAL,
    ev_ebitda REAL,
    dividend_yield_pct REAL,
    FOREIGN KEY (company_id) REFERENCES companies (company_id) ON DELETE CASCADE,
    UNIQUE(company_id, year)
);

-- Performance Indexes
CREATE INDEX IF NOT EXISTS idx_pnl_comp_yr ON profitandloss(company_id, year);
CREATE INDEX IF NOT EXISTS idx_bs_comp_yr ON balancesheet(company_id, year);
CREATE INDEX IF NOT EXISTS idx_cf_comp_yr ON cashflow(company_id, year);
CREATE INDEX IF NOT EXISTS idx_ratios_comp_yr ON financial_ratios(company_id, year);
CREATE INDEX IF NOT EXISTS idx_mktcap_comp_yr ON market_cap(company_id, year);
CREATE INDEX IF NOT EXISTS idx_prices_comp_dt ON stock_prices(company_id, date);
