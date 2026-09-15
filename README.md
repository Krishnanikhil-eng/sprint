# Nifty 100 Financial Analytics Platform & REST API

Comprehensive production-grade financial analytics platform, FastAPI REST web service, KMeans archetype clustering engine, NLP pros & cons generator, and Streamlit dashboard for Nifty 100 equity research, ratio analysis, peer benchmarking, capital allocation mapping, stock screening, and valuation modeling (Sprints 1–6).

---

## 🚀 Quick Start & CLI Reference

### 1. Run FastAPI REST Web Service
```bash
uvicorn src.api.main:app --reload --port 8000
```
- Interactive Swagger UI Docs: `http://localhost:8000/docs`
- ReDoc API Documentation: `http://localhost:8000/redoc`
- Health Endpoint: `http://localhost:8000/api/v1/health`

### 2. Run Interactive Streamlit Dashboard
```bash
streamlit run src/dashboard/app.py
```
Starts local interactive web application on `http://localhost:8501`.

### 3. Run Automated Test Suite with HTML Report
```bash
pytest tests/ --html=reports/pytest_report.html --self-contained-html
```

### 4. Run Core Analytics Pipelines
- **KMeans Archetype Clustering**: `python src/analytics/clustering.py`
- **Cluster Profiling & Portfolio KPIs**: `python src/analytics/cluster_profiler.py`
- **SQLite Database Index Optimization**: `python scripts/optimize_db_indexes.py`
- **Export OpenAPI & Postman Schemas**: `python scripts/export_api_docs.py`
- **Generate Analyst Guide PDF**: `python scripts/generate_analyst_guide.py`
- **Execute 20 Acceptance Gates Validation**: `python src/analytics/acceptance_gates_validator.py`

---

## 📁 Deliverables & Repository Structure

```text
├── src/
│   ├── analytics/
│   │   ├── clustering.py               # KMeans 5-archetype clustering engine
│   │   ├── cluster_profiler.py         # Cluster financial profiling & correlation heatmap
│   │   ├── ratio_engine.py             # 20 financial ratios calculation pipeline
│   │   ├── screener_engine.py          # Screener filtering & composite scoring
│   │   ├── peer_engine.py              # Peer percentile & comparison engine
│   │   └── valuation.py                # Valuation engine & flag classification
│   ├── api/
│   │   ├── main.py                     # FastAPI application scaffold & middleware
│   │   ├── database.py                 # SQLite connection pooling & helpers
│   │   └── routers/                    # REST API routers (companies, screener, sectors, etc.)
│   ├── dashboard/                      # 8-screen Streamlit interactive application
│   ├── nlp/                            # NLP Pros & Cons inference engine & parsers
│   └── reports/                        # ReportLab PDF tearsheets & batch generators
├── docs/
│   ├── openapi.json                    # Exported OpenAPI 3.0 REST API schema
│   ├── postman_collection.json         # Postman Collection v2.1 for API testing
│   ├── analyst_guide.pdf               # 10-page comprehensive Financial Analyst Guide
│   └── acceptance_checklist.pdf        # Final Sprint 6 20 Acceptance Gates sign-off
├── output/
│   ├── cluster_labels.csv              # 92-company cluster assignments & distance
│   ├── outlier_report.csv              # Sector Z-score outlier detection report
│   ├── portfolio_stats.csv             # P10-P90 portfolio statistical KPI distributions
│   ├── perf_notes.md                   # SQLite indexing benchmarks & API performance
│   └── final_deliverables/             # Final archived project deliverables
├── reports/
│   ├── elbow_plot.png                  # KMeans inertia elbow curve visualization
│   ├── correlation_heatmap.png         # 10-metric Pearson correlation heatmap
│   └── pytest_report.html              # HTML test execution report (248 tests)
├── scripts/                            # Automation scripts (DB indexing, PDF generators)
├── tests/                              # 248 pytest unit, integration, and performance tests
├── nifty100.db                         # Canonical 10-table SQLite database (92 companies)
└── README.md                           # Master project documentation
```

---

## 📡 REST API Endpoints Overview (`/api/v1`)

| Method | Endpoint Path | Description |
| :--- | :--- | :--- |
| **GET** | `/api/v1/health` | System health status, version, uptime, and database row counts |
| **GET** | `/api/v1/companies` | List 92 companies with sector, market cap, and ROE filters |
| **GET** | `/api/v1/companies/{ticker}` | Detailed financial profile for specific company |
| **GET** | `/api/v1/companies/{ticker}/pl` | Historical Profit & Loss statement time series |
| **GET** | `/api/v1/companies/{ticker}/bs` | Historical Balance Sheet statement time series |
| **GET** | `/api/v1/companies/{ticker}/cashflow` | Historical Cash Flow statement time series |
| **GET** | `/api/v1/companies/{ticker}/ratios` | Calculated annual financial ratios |
| **GET** | `/api/v1/companies/{ticker}/tearsheet` | Stream binary 2-page tearsheet PDF report |
| **GET** | `/api/v1/screener` | Multi-metric custom stock screening |
| **GET** | `/api/v1/sectors` | Broad sector aggregate financial statistics |
| **GET** | `/api/v1/sectors/{sector}/companies` | List companies within specified broad sector |
| **GET** | `/api/v1/peers` | List available peer benchmark groups |
| **GET** | `/api/v1/peers/{group_name}` | Members & financial metrics for specified peer group |
| **GET** | `/api/v1/companies/{ticker}/peers/compare` | Peer relative percentile scores and comparison |
| **GET** | `/api/v1/market-cap/{ticker}` | Annual Market Cap, EV, PE, PB, and yield history |
| **GET** | `/api/v1/portfolio/stats` | Portfolio-wide KPI percentile distributions (P10-P90) |
| **GET** | `/api/v1/companies/{ticker}/documents` | Filing document metadata and annual report URLs |

---

## 🧪 Testing & Data Quality Assurance

- **Total Test Cases**: **248 passed, 0 failures**
- **Test Framework**: `pytest` with `pytest-html`
- **Execution Report**: Available at `reports/pytest_report.html`
- **Test Categories**:
  - `tests/analytics/`: KMeans clustering and profiling tests
  - `tests/api/`: FastAPI unit & multi-step integration flow tests
  - `tests/etl/`: Year/ticker normalizer & loader tests
  - `tests/kpi/`: 20 financial ratios, CAGR engine, and leverage tests
  - `tests/dq/`: 14 Data Quality validation & schema integrity tests
  - `tests/performance/`: API load performance & latency tests
