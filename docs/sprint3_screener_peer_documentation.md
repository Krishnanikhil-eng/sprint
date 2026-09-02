# Sprint 3 Architecture & Technical Documentation
## Equity Screener Engine & Peer Comparison System

---

### Executive Summary

Sprint 3 delivers the institutional-grade **Equity Screener Engine** and **Peer Comparison Engine** for Nifty 100 stocks. The architecture supports dynamic configuration-driven metric filtering, special sector exemptions (Financials D/E carve-outs, Debt-Free ICR handling), composite scoring with Min-Max normalization, 6 production screening presets, SQLite `peer_percentiles` database persistence, multi-dimensional radar chart visualization, and automated Excel reporting with openpyxl styling.

---

### Key Architectural Components

```
                    ┌──────────────────────────────────────────────┐
                    │            SQLite Database (nifty100.db)     │
                    └──────────────────────┬───────────────────────┘
                                           │
                    ┌──────────────────────▼───────────────────────┐
                    │         Screener Engine & Presets            │
                    │   - Quality Compounder    - Value Pick       │
                    │   - Growth Accelerator    - Dividend Champion│
                    │   - Debt-Free Blue Chip   - Turnaround Watch │
                    └──────────────────────┬───────────────────────┘
                                           │
          ┌────────────────────────────────┴────────────────────────────────┐
          │                                                                 │
┌─────────▼───────────────────────────┐           ┌─────────────────────────▼─────────────────────────┐
│        Screener Exporter            │           │             Peer Comparison Engine               │
│ - Composite Min-Max Normalization   │           │ - Metric Percentiles (0-100)                      │
│ - Sector Relative Scoring           │           │ - Inverse Debt Percentile Logic (Lower D/E = Top) │
│ - Excel Multi-Tab Report & Formatting│           │ - SQLite `peer_percentiles` Database Integration  │
└─────────────────────────────────────┘           │ - Multi-dimensional Radar Chart Generator         │
                                                  │ - Peer Comparison Excel Report Exporter          │
                                                  └───────────────────────────────────────────────────┘
```

---

### 1. Screener Engine Specifications

- **Configuration Engine (`src/analytics/screener_config.py`)**:
  - `FilterCriterion`: Dataclass encapsulating metric name, operator (`>`, `>=`, `<`, `<=`, `==`, `BETWEEN`), target value, min/max thresholds, weight, and evaluate method.
  - `ScreenerConfig`: Configuration container supporting JSON serialization/deserialization and preset management.

- **Special Sector & Zero-Debt Rules**:
  - **Financial Sector D/E Carve-Out**: Commercial Banks and Financial Services operate under high structural leverage. When `handle_financials_de=True`, D/E filter thresholds are waived for Financials companies.
  - **Debt-Free ICR Handling**: Companies with zero total debt (`icr_label == 'DEBT_FREE'`) automatically pass interest coverage requirements (`handle_zero_debt_icr=True`).

- **Composite Scoring & Normalization**:
  - Raw score calculation across 4 pillars: Quality/Profitability (35%), Growth (25%), Financial Health (25%), Capital Efficiency (15%).
  - Standardized Min-Max scaling (0.0 to 100.0) applied across the screened stock universe.
  - Sector-relative percentile ranking within broad sectors.

---

### 2. The 6 Screener Presets

| Preset Name | Target Strategy | Key Filter Thresholds |
| :--- | :--- | :--- |
| **Quality Compounder** | High Return, Low Debt | ROE >= 15%, ROCE >= 15%, D/E <= 0.5, FCF > 0 Cr, 5Yr Rev CAGR >= 8% |
| **Value Pick** | Attractively Priced Value | D/E <= 1.0, ROE >= 12%, Net Profit Margin >= 8%, FCF > 0 Cr, Book Value > 0 |
| **Growth Accelerator** | Revenue & Earnings Compounders | 5Yr Rev CAGR >= 10%, 5Yr PAT CAGR >= 10%, ROE >= 14%, OPM >= 10% |
| **Dividend Champion** | Yield & Cash Flow Generative | Dividend Payout >= 20%, FCF > 0 Cr, D/E <= 1.0, ROE >= 12% |
| **Debt-Free Blue Chip** | Zero Debt Quality Giants | D/E <= 0.1, ROE >= 15%, FCF > 0 Cr, ICR >= 5.0 (Debt-Free exempt) |
| **Turnaround Watch** | Earnings Recovery Candidates | 5Yr PAT CAGR >= 5%, FCF > 0 Cr, Net Debt <= 5000 Cr, OPM >= 8% |

---

### 3. Peer Engine & Percentile Mechanics

- **Percentile Calculation**:
  - Standard metrics (ROE, ROCE, ROA, NPM, OPM, Asset Turnover, FCF, CAGRs) compute percentile ranks from 0.0 to 100.0 within each company's `effective_peer_group`.
- **Inverse Debt Percentile Logic**:
  - For leverage metrics (`debt_to_equity` and `net_debt_cr`), lower numeric values represent superior financial health.
  - Inverted percentile rank equation: $\text{Percentile}_{\text{inv}} = \text{Rank}_{\text{descending}} \times 100.0$.
- **Database Schema (`peer_percentiles`)**:
  - Persisted in SQLite `nifty100.db` with primary key `company_id`, effective peer group, individual metric percentiles, inverse D/E rank, overall peer percentile, and automated timestamp.

---

### 4. Excel Exporters & Radar Visualizations

- **Screener Excel Exporter (`output/screener_results.xlsx`)**:
  - Multi-sheet workbook containing a Summary Overview tab and 6 preset result tabs.
  - Formatted headers (Navy `#1F497D`), auto-adjusted column widths, gridlines enabled, green conditional fills for high ROE/scores, and red/yellow warning fills for high leverage.
- **Peer Comparison Excel Exporter (`output/peer_comparison_report.xlsx`)**:
  - Full matrix of all peer group percentiles and sector-specific ranking tabs.
- **Radar Chart Generator (`output/charts/radar_<company>.png`)**:
  - Spider chart visualization plotting company percentiles vs peer median benchmark (50th percentile) across 6 core pillars.
