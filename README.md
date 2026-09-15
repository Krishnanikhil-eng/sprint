# Nifty 100 Analytics & Interactive Dashboard

Comprehensive analytical platform and interactive Streamlit web dashboard for Nifty 100 equity research, ratio analysis, peer benchmarking, capital allocation mapping, stock screening, and valuation modeling.

---

## 🚀 Quick Start — Streamlit Dashboard Startup

To run the interactive Streamlit dashboard application locally:

```bash
streamlit run src/dashboard/app.py
```

The application will start locally on `http://localhost:8501`.

---

## 📁 Repository Deliverables Structure

```text
├── src/
│   ├── analytics/
│   │   ├── valuation.py                # Valuation engine & flag classification
│   │   ├── screener_engine.py          # Screener filtering & composite scoring
│   │   ├── peer_engine.py              # Peer percentile & comparison engine
│   │   ├── ratio_engine.py            # Financial ratio computation pipeline
│   │   └── presets.py                  # Screener preset strategies definition
│   └── dashboard/
│       ├── app.py                      # Main Streamlit dashboard entry point
│       ├── config.py                   # Centralized configuration & constants
│       ├── utils/
│       │   └── db.py                   # Cached SQLite database loaders (@st.cache_data)
│       └── pages/
│           ├── 01_home.py              # Screen 1: Home KPI Dashboard & Sector Donut
│           ├── 02_profile.py           # Screen 2: Company Profile, KPIs & 10yr Trends
│           ├── 03_screener.py          # Screen 3: 10-Filter Stock Screener & Presets
│           ├── 04_peers.py             # Screen 4: Peer Comparison Radar & KPI Table
│           ├── 05_trends.py            # Screen 5: 10-Year Metric Trend & YoY % Change
│           ├── 06_sectors.py           # Screen 6: Sector Revenue vs ROE Bubble Chart
│           ├── 07_capital.py           # Screen 7: Capital Allocation Treemap
│           └── 08_reports.py           # Screen 8: Annual Reports & BSE Links
├── output/
│   ├── valuation_summary.xlsx          # Full 92-company valuation Excel summary
│   ├── valuation_flags.csv             # Filtered Caution & Discount flags CSV
│   └── screener_results.xlsx           # Generated screener report workbook
├── db/
│   └── schema.sql                      # SQLite 12-table database schema
├── data/                               # Raw market cap & financial ratio Excel datasets
├── tests/                              # Automated test suite (integration & KPI tests)
├── README.md                           # Documentation & Sprint retrospective
└── nifty100.db                         # Target SQLite database (92 companies)
```

---

## 💻 8 Dashboard Screens Overview

1. **Screen 1 — Home Dashboard (`01_home.py`)**:
   - 6 Key Performance Indicator tiles: Average ROE, Median P/E, Median D/E, Total Companies, Median Revenue CAGR (5yr), and Debt-Free Companies count.
   - Interactive Plotly donut chart depicting company distribution across all 11 broad sectors.
   - Top 5 quality rankings by composite quality score.
   - Dynamic fiscal year selector (2019–2024).

2. **Screen 2 — Company Profile (`02_profile.py`)**:
   - Dual search functionality (Company Name or Ticker search + autocomplete selectbox).
   - Detailed company card with Sector, Sub-Sector, Ticker, and Business Description.
   - 6 core KPI metrics (ROE, ROCE, Net Profit Margin, D/E, Revenue CAGR 5yr, Latest Free Cash Flow).
   - Dual performance charts: 10-year Revenue + Net Profit bar chart and ROE + ROCE dual-axis trend line chart.
   - Qualitative Pros (✅) and Cons (❌) analytical signal badges.

3. **Screen 3 — Stock Screener (`03_screener.py`)**:
   - 10 numerical filter controls: ROE min, D/E max, FCF min, Revenue CAGR min, PAT CAGR min, OPM min, P/E max, P/B max, Dividend Yield min, ICR min.
   - 6 pre-configured preset strategies: *Quality*, *Value*, *Growth*, *Dividend*, *Debt-Free*, and *Turnaround*.
   - Dynamic real-time results filtering with matched company count display.
   - One-click CSV Export functionality for filtered screener results.

4. **Screen 4 — Peer Comparison (`04_peers.py`)**:
   - Sector dropdown supporting all 11 Nifty 100 peer groups.
   - Selected benchmark company vs peer group average comparison.
   - 8-metric Plotly radar chart using `Scatterpolar` for visual comparative profile.
   - Side-by-side KPI comparison table with benchmark company highlighted.

5. **Screen 5 — Trend Analysis (`05_trends.py`)**:
   - Searchable company selection for historical metric analysis.
   - Multi-metric selector supporting up to 3 simultaneous performance indicators.
   - Interactive 10-year historical line chart with hover tooltips.
   - Year-over-Year (YoY %) change table with robust error handling for zero/missing values.

6. **Screen 6 — Sector Analysis (`06_sectors.py`)**:
   - Sector selectbox covering all Nifty 100 broad sectors.
   - Interactive 4-dimensional Plotly bubble chart (`X = Revenue`, `Y = ROE`, `Bubble Size = Market Cap`, `Colour = Sub-Sector`).
   - Sector median KPI bar chart highlighting sector-wide benchmark statistics.

7. **Screen 7 — Capital Allocation (`07_capital.py`)**:
   - Full 92-company universe coverage grouped across 8 capital allocation patterns (*Reinvestor*, *Shareholder Returns*, *Growth Funded by Debt*, etc.).
   - Interactive Plotly Treemap visualization with drill-down pattern breakdown.
   - Filterable member company list table upon selecting any capital allocation pattern.

8. **Screen 8 — Annual Reports (`08_reports.py`)**:
   - Searchable annual report catalog by company ticker/name.
   - Clickable BSE official PDF report links.
   - Cached URL validation engine with graceful error handling and red badge (`🔴 Report unavailable`) display for inaccessible links.

---

## 📊 Valuation Engine & Deliverables

The valuation engine (`src/analytics/valuation.py`) computes key valuation ratios and classifies Nifty 100 companies based on sector-relative valuation multiples:

### Generated Valuation Outputs:
- **`output/valuation_summary.xlsx`**: Excel report covering all 92 companies with required columns (`company_id`, `company_name`, `sector`, `P/E`, `P/B`, `EV/EBITDA`, `FCF_yield_pct`, `5yr_median_PE`, `PE_vs_sector_median_pct`, `flag`).
- **`output/valuation_flags.csv`**: Filtered CSV file containing companies flagged with **Caution** (P/E > Sector Median × 1.5) or **Discount** (P/E < Sector Median × 0.7).

To execute the valuation pipeline and generate output files:
```bash
python src/analytics/valuation.py
```

---

## 🛠️ Performance & QA

- **Company Profile Load Time**: Measured across 5 representative tickers (`TCS`, `INFY`, `HDFCBANK`, `RELIANCE`, `SUNPHARMA`). All tickers loaded in under 1.4 seconds (well below the 3.0-second performance target).
- **Test Suite**: Automated unit and integration test suite passing 115 tests covering database loaders, ratio computations, screener presets, peer percentile ranks, and dashboard page imports:
```bash
pytest
```

---

## ⚠️ Known Limitations

1. **Annual Report PDF Availability**: Certain legacy BSE annual report links for specific historical years may return 404/expired statuses on external servers; these are handled safely with visual red error badges.
2. **Missing Sector Financials**: Financial sector companies (e.g. Banks/NBFCs) do not report standard operating profit margin (OPM) or D/E in non-banking formats; standard fallback `N/A` indicators are displayed.

---

## 📝 Sprint 4 Retrospective

- **Accomplishments**: Delivered a complete, end-to-end Nifty 100 analytics Streamlit dashboard with 8 production-grade interactive screens, high-performance database caching (`@st.cache_data`), full 10-filter stock screener, 8-metric radar comparison charts, capital allocation treemaps, and automated valuation export pipeline.
- **Architecture Highlights**: Modular page structure (`src/dashboard/pages/`), centralized config system (`config.py`), cached SQLite query helpers (`db.py`), and robust missing data fallbacks (`LABEL_NA`).

