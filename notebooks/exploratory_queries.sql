-- Exploratory SQL Queries for Nifty 100 Data Foundation Pipeline
-- Database Target: nifty100.db

-- Query 1: Total Company Count & Category Summary
SELECT 
    COUNT(*) AS total_companies,
    COUNT(DISTINCT company_id) AS unique_tickers
FROM companies;

-- Query 2: Year Coverage per Financial Statement Table
SELECT 
    'profitandloss' AS table_name, MIN(year) AS min_year, MAX(year) AS max_year, COUNT(DISTINCT year) AS total_years FROM profitandloss
UNION ALL
SELECT 
    'balancesheet' AS table_name, MIN(year) AS min_year, MAX(year) AS max_year, COUNT(DISTINCT year) AS total_years FROM balancesheet
UNION ALL
SELECT 
    'cashflow' AS table_name, MIN(year) AS min_year, MAX(year) AS max_year, COUNT(DISTINCT year) AS total_years FROM cashflow
UNION ALL
SELECT 
    'financial_ratios' AS table_name, MIN(year) AS min_year, MAX(year) AS max_year, COUNT(DISTINCT year) AS total_years FROM financial_ratios
UNION ALL
SELECT 
    'market_cap' AS table_name, MIN(year) AS min_year, MAX(year) AS max_year, COUNT(DISTINCT year) AS total_years FROM market_cap;

-- Query 3: Financial Statement Row Counts Across All 12 Database Tables
SELECT 'companies' AS table_name, COUNT(*) AS row_count FROM companies
UNION ALL SELECT 'profitandloss', COUNT(*) FROM profitandloss
UNION ALL SELECT 'balancesheet', COUNT(*) FROM balancesheet
UNION ALL SELECT 'cashflow', COUNT(*) FROM cashflow
UNION ALL SELECT 'analysis', COUNT(*) FROM analysis
UNION ALL SELECT 'documents', COUNT(*) FROM documents
UNION ALL SELECT 'prosandcons', COUNT(*) FROM prosandcons
UNION ALL SELECT 'sectors', COUNT(*) FROM sectors
UNION ALL SELECT 'peer_groups', COUNT(*) FROM peer_groups
UNION ALL SELECT 'financial_ratios', COUNT(*) FROM financial_ratios
UNION ALL SELECT 'stock_prices', COUNT(*) FROM stock_prices
UNION ALL SELECT 'market_cap', COUNT(*) FROM market_cap;

-- Query 4: Companies with Missing Years or Historical Gaps (< 10 Years P&L Data)
SELECT 
    c.company_id,
    c.company_name,
    COUNT(p.year) AS years_recorded
FROM companies c
LEFT JOIN profitandloss p ON c.company_id = p.company_id
GROUP BY c.company_id, c.company_name
HAVING years_recorded < 10
ORDER BY years_recorded ASC;

-- Query 5: Revenue / Sales Analysis — Top 10 Revenue Generators in Latest Year (2024)
SELECT 
    c.company_id,
    c.company_name,
    p.year,
    p.sales AS revenue_crores,
    p.net_profit AS net_profit_crores
FROM profitandloss p
JOIN companies c ON p.company_id = c.company_id
WHERE p.year = 2024
ORDER BY p.sales DESC
LIMIT 10;

-- Query 6: Profitability Analysis — Highest Operating Profit Margin (OPM %) Companies (2024)
SELECT 
    c.company_id,
    c.company_name,
    p.year,
    p.opm_percentage,
    p.sales,
    p.operating_profit
FROM profitandloss p
JOIN companies c ON p.company_id = c.company_id
WHERE p.year = 2024 AND p.sales > 1000
ORDER BY p.opm_percentage DESC
LIMIT 10;

-- Query 7: Balance Sheet Accounting Equation Validation (Assets = Liabilities Check)
SELECT 
    company_id,
    year,
    total_assets,
    total_liabilities,
    ABS(total_assets - total_liabilities) AS discrepancy
FROM balancesheet
WHERE ABS(total_assets - total_liabilities) > 0.01
ORDER BY discrepancy DESC;

-- Query 8: Stock Price Coverage & Price Statistics
SELECT 
    company_id,
    COUNT(*) AS total_monthly_quotes,
    MIN(date) AS start_date,
    MAX(date) AS end_date,
    ROUND(MIN(low_price), 2) AS min_price,
    ROUND(MAX(high_price), 2) AS max_price,
    ROUND(AVG(close_price), 2) AS avg_close_price
FROM stock_prices
GROUP BY company_id
ORDER BY total_monthly_quotes DESC
LIMIT 10;

-- Query 9: Financial Ratio Analysis — Return on Equity & Debt-to-Equity Multiples (2024)
SELECT 
    c.company_id,
    c.company_name,
    r.year,
    r.return_on_equity_pct,
    r.debt_to_equity,
    r.operating_profit_margin_pct
FROM financial_ratios r
JOIN companies c ON r.company_id = c.company_id
WHERE r.year = 2024
ORDER BY r.return_on_equity_pct DESC
LIMIT 10;

-- Query 10: Multi-Table Comprehensive Financial & Market Valuation Join
SELECT 
    c.company_id,
    c.company_name,
    p.year,
    p.sales AS revenue,
    p.net_profit,
    b.total_assets,
    m.market_cap_crore,
    m.pe_ratio,
    r.return_on_equity_pct
FROM companies c
JOIN profitandloss p ON c.company_id = p.company_id
JOIN balancesheet b ON c.company_id = b.company_id AND p.year = b.year
JOIN market_cap m ON c.company_id = m.company_id AND p.year = m.year
JOIN financial_ratios r ON c.company_id = r.company_id AND p.year = r.year
WHERE p.year = 2024
ORDER BY m.market_cap_crore DESC
LIMIT 15;
