# Nifty 100 Data Foundation — ETL Pipeline & Normalisation

Sprint 1 ETL Data Foundation pipeline for processing Nifty 100 financial datasets. This repository contains the core normalisation engine, Excel data loader, unit test suite, SQLite database schema (`nifty100.db`), data quality validation engine (DQ-01 to DQ-16), and project structure for ETL pipeline development.

---

## 📄 Sprint 1 Complete Audit Report
For the complete, independent audit report of Sprint 1 (Data Foundation), including schema design details, ingestion statistics, data quality results, and Definition of Done verification, see:
👉 **[`docs/sprint1_data_foundation_audit.md`](docs/sprint1_data_foundation_audit.md)**

---

## 📁 Directory Structure

```text
project/
├── src/
│   └── etl/
│       ├── loader.py        # Excel data loading & full ETL pipeline execution
│       ├── normaliser.py    # Year & Ticker normalisation logic
│       └── validator.py     # Schema & DQ-01..DQ-16 data quality validator
├── db/
│   └── schema.sql           # 12-table database schema definition
├── docs/
│   └── sprint1_data_foundation_audit.md # Complete Sprint 1 Audit Report
├── tests/
│   └── etl/
│       ├── test_loader.py   # Unit tests for loader module
│       ├── test_normaliser.py # Unit tests for normaliser module
│       ├── test_validator.py  # Unit tests for validator engine & DQ rules
│       └── test_db_loader.py  # Unit tests for database loading & audit CSV
├── output/                  # Generated audit CSVs & validation logs
├── notebooks/               # SQL exploratory queries (`exploratory_queries.sql`)
├── data/                    # Raw input Excel data files (.xlsx & zip)
├── .env                     # Environment variables configuration
├── .gitignore               # Git exclusion patterns
├── Makefile                 # Automation task commands
├── pyproject.toml           # Pytest & package configuration
├── requirements.txt         # Project dependencies (pinned)
└── nifty100.db              # SQLite target database (12 tables)
```

---

## 🚀 Quick Start

### 1. Environment Setup

Activate the virtual environment:

**Windows (PowerShell):**
```powershell
.venv\Scripts\Activate.ps1
```

**Linux / macOS:**
```bash
source .venv/bin/activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

---

## ⚙️ Core Commands & Tasks

| Command | Target | Description |
| :--- | :--- | :--- |
| `make load` | `python -m src.etl.loader` | Run full ETL pipeline and populate `nifty100.db` |
| `make test` | `pytest` | Run complete unit test suite (59 passing tests) |
| `make report` | `python -m src.etl.validator` | Run DQ validator engine & export validation report |
| `make clean` | `clean` | Remove temporary cache files |

---

## 🧪 Testing

The repository features a unit test suite with 59 tests covering normalization edge cases, loader pipeline execution, validator rules, and database schema referential integrity.

Run tests using `pytest`:

```bash
pytest
```

---

## 🔑 Environment Configuration

Key settings are configured in `.env`:

```env
DB_NAME=nifty100.db
DB_PATH=./nifty100.db
ENVIRONMENT=development
LOG_LEVEL=INFO
```
