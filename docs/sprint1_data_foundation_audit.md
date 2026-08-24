# Sprint 1 Data Foundation Audit & Verification Report

## 1. Sprint 1 Objective
The objective of Sprint 1 (Data Foundation) is to establish a fully loaded and validated SQLite database (`nifty100.db`) containing all 12 source datasets, with all 16 Data Quality (DQ) rules executed and zero CRITICAL failures remaining.

---

## 2. 12-Table Schema Strategy & Market Cap Isolation
The database model contains **12 dedicated tables** corresponding 1-to-1 to the 12 source datasets: `companies`, `profitandloss`, `balancesheet`, `cashflow`, `analysis`, `documents`, `prosandcons`, `sectors`, `peer_groups`, `financial_ratios`, `stock_prices`, and `market_cap`.

### Why `market_cap` is a Separate Table:
- `market_cap.xlsx` contains annual market valuation metrics (`market_cap_crore`, `pe_ratio`, `pb_ratio`, `ev_ebitda`, `dividend_yield_pct`) covering years 2019–2024 for 92 companies (552 rows).
- Merging `market_cap` into `companies` would violate 3NF normalization, as `companies` holds static entity details while `market_cap` contains multi-year time-series records.
- Merging `market_cap` into `financial_ratios` would mix accounting/statement ratios with market valuation metrics, introducing sparse NULL padding for earlier historical years.

---

## 3. Final Database Row Counts (`nifty100.db`)
- `companies`: 92
- `profitandloss`: 1,073
- `balancesheet`: 1,058
- `cashflow`: 1,056
- `analysis`: 16
- `documents`: 1,457
- `prosandcons`: 14
- `sectors`: 92
- `peer_groups`: 56
- `financial_ratios`: 1,041
- `stock_prices`: 5,520
- `market_cap`: 552

---

## 4. Load Rejection Summary & Reasons (`output/load_audit.csv`)

| Table | Rows Read | Loaded | Rejected | Rejection Reasons |
| :--- | :---: | :---: | :---: | :--- |
| **companies** | 92 | 92 | 0 | None |
| **profitandloss** | 1,276 | 1,073 | 203 | `NULL_YEAR_SUMMARY_ROW` (100) \| `FK_VIOLATION_MISSING_PARENT_COMPANY` (86) \| `DUP_YEARS` (17) |
| **balancesheet** | 1,312 | 1,058 | 254 | `FK_VIOLATION_MISSING_PARENT_COMPANY` (85) \| `DUP_YEARS` (169) |
| **cashflow** | 1,187 | 1,056 | 131 | `FK_VIOLATION_MISSING_PARENT_COMPANY` (96) \| `DUP_YEARS` (35) |
| **analysis** | 20 | 16 | 4 | `FK_VIOLATION_MISSING_PARENT_COMPANY` (4) |
| **documents** | 1,585 | 1,457 | 128 | `FK_VIOLATION_MISSING_PARENT_COMPANY` (128) |
| **prosandcons** | 16 | 14 | 2 | `FK_VIOLATION_MISSING_PARENT_COMPANY` (2) |
| **sectors** | 92 | 92 | 0 | None |
| **peer_groups** | 56 | 56 | 0 | None |
| **financial_ratios** | 1,184 | 1,041 | 143 | `FK_VIOLATION_MISSING_PARENT_COMPANY` (24) \| `DUP_YEARS` (119) |
| **stock_prices** | 5,520 | 5,520 | 0 | None |
| **market_cap** | 552 | 552 | 0 | None |

---

## 5. DQ-01 through DQ-16 Final Results

| Rule | Description | Status | Severity | Failures | Message / Details |
| :--- | :--- | :---: | :---: | :---: | :--- |
| **DQ-01** | Ticker Format & Validation | **PASS** | CRITICAL | 0 | All company IDs are uppercase alphanumeric tickers |
| **DQ-02** | Missing / Null Ticker Check | **PASS** | CRITICAL | 0 | Zero null/blank tickers found |
| **DQ-03** | Duplicate Company ID Check | **PASS** | CRITICAL | 0 | Primary key uniqueness verified on `companies` |
| **DQ-04** | Year Range Check (1900–2100) | **PASS** | WARNING | 0 | All statement years within 1900–2100 range |
| **DQ-05** | Missing / Null Year Check | **PASS** | CRITICAL | 0 | Zero null years in loaded time-series tables |
| **DQ-06** | Duplicate Year per Company Check | **PASS** | CRITICAL | 0 | Composite key `(company_id, year)` uniqueness verified |
| **DQ-07** | Financial Value Numeric Check | **PASS** | WARNING | 0 | Zero infinite or non-numeric float values |
| **DQ-08** | Financial Value Range / Sanity Check | **PASS** | WARNING | 0 | Total Assets non-negative across balance sheets |
| **DQ-09** | Balance Sheet Accounting Equation | **PASS** | CRITICAL | 0 | `Total Assets == Total Liabilities` across 1,058 balance sheets |
| **DQ-10** | Revenue / Sales Non-Negativity | **PASS** | CRITICAL | 0 | Zero negative sales values found |
| **DQ-11** | Cash Flow Net Change Consistency | **WARNING** | WARNING | 1 | `TVSMOTOR 2022` source cash flow variance logged |
| **DQ-12** | Required Fields / Columns Presence | **PASS** | CRITICAL | 0 | All mandatory schema columns present across all 12 tables |
| **DQ-13** | Foreign Key / Parent Integrity | **PASS** | CRITICAL | 0 | 100% referential integrity (`PRAGMA foreign_key_check` = 0) |
| **DQ-14** | Duplicate Financial Records Check | **PASS** | WARNING | 0 | Zero full-row duplicate records |
| **DQ-15** | Outlier / Extreme Value Detection | **WARNING** | WARNING | 10 | 10 mega-cap sales outliers (>5 std dev from mean) logged |
| **DQ-16** | Stock Price Sanity Check | **PASS** | CRITICAL | 0 | `low_price <= high_price`, positive prices across 5,520 records |

---

## 6. DQ-11 Warning Explanation (TVSMOTOR 2022)
- **Company**: `TVSMOTOR` (2022)
- **Values**: `operating_activity = -1575.0`, `investing_activity = -1471.0`, `financing_activity = 2918.0`, `net_cash_flow = 532.0`.
- **Calculated Sum**: `-128.0` (Variance = `660.0`).
- **Explanation**: Confirmed directly in raw `cashflow.xlsx` row 1167. This variance exists in the raw source dataset from BSE/Screener. The loader preserved raw values accurately, and DQ-11 correctly flagged it as a `WARNING`.

---

## 7. DQ-15 Outlier Explanation
- **Companies**: `IOC` (2023, 2024), `LICI` (2021, 2022, 2023, 2024), `ONGC` (2023), `RELIANCE` (2022, 2023, 2024).
- **Values**: Sales ranging from ₹632,291 Crore to ₹899,041 Crore.
- **Explanation**: These represent India's largest corporate conglomerates with sales >5 std dev above the Nifty 100 average. They are legitimate financial numbers, correctly flagged as `WARNING` statistical notifications without discarding valid data.

---

## 8. Five-Company Manual Review

| Company | Name | Year Coverage | P&L Rows | BS Rows | CF Rows | Foreign Keys | Duplicate Years |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **ABB** | Abbott India Ltd | 2012–2024 | 12 | 12 | 12 | Valid (0 errors) | 0 |
| **RELIANCE** | Reliance Industries Ltd | 2013–2024 | 12 | 12 | 12 | Valid (0 errors) | 0 |
| **TCS** | Tata Consultancy Services Ltd | 2013–2024 | 12 | 12 | 12 | Valid (0 errors) | 0 |
| **INFY** | Infosys Ltd | 2013–2024 | 12 | 12 | 12 | Valid (0 errors) | 0 |
| **HDFCBANK** | HDFC Bank Ltd | 2013–2024 | 12 | 12 | 12 | Valid (0 errors) | 0 |

---

## 9. Foreign Key Verification Result
`PRAGMA foreign_keys = ON;` and `PRAGMA foreign_key_check;` executed across `nifty100.db`:
- **Foreign Key Violations**: **0**

---

## 10. Test Result
- **Total Unit Tests Executed**: **59**
- **Passed**: **59**
- **Failed**: **0**

---

## 11. Reproducibility Verification
- Executed `make clean` followed by `make load` and `make test`.
- Re-creation of `nifty100.db` from raw Excel sources is 100% automated and deterministic.

---

## 12. Sprint 1 Definition of Done Checklist

- [x] 12 Database tables created with 3NF referential integrity
- [x] 92 parent Nifty 100 companies loaded
- [x] Zero foreign key violations (`PRAGMA foreign_key_check` = 0)
- [x] Zero CRITICAL DQ rule failures
- [x] 59 unit tests passed (> 35 target)
- [x] 10 exploratory SQL queries verified (`notebooks/exploratory_queries.sql`)
- [x] `load_audit.csv` and `validation_failures.csv` exported
- [x] Reproducible Makefile targets operational

---

## 13. Final Sprint 1 Status
**Sprint 1 Status**: **COMPLETE**
