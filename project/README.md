# Nifty 100 Data Foundation — ETL Pipeline & Normalisation

Sprint 1 ETL Data Foundation pipeline for processing Nifty 100 financial datasets. This repository contains the core normalisation engine, Excel data loader, unit test suite, and project structure for ETL pipeline development.

---

## 📁 Directory Structure

```text
project/
├── src/
│   └── etl/
│       ├── loader.py        # Excel data loading & header cleaning
│       ├── normaliser.py    # Year & Ticker normalisation logic
│       └── validator.py     # Schema & data validation (Sprint 1)
├── db/
│   └── schema.sql           # Database schema definition
├── tests/
│   └── etl/
│       ├── test_loader.py   # Unit tests for loader module
│       └── test_normaliser.py # 43+ unit tests for normaliser module
├── output/                  # Directory for generated outputs & logs
├── notebooks/               # Data exploration & analysis notebooks
├── data/                    # Raw input Excel data files (.xlsx)
├── .env                     # Environment variables configuration
├── .gitignore               # Git exclusion patterns
├── Makefile                 # Automation task commands
├── requirements.txt         # Project dependencies (pinned)
└── nifty100.db              # SQLite target database
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

## ⚙️ Core Modules

### 1. `src/etl/normaliser.py`

Contains normalisation functions for cleaning raw dataset fields:

- **`normalize_year(value)`**:
  Converts standard years (`2023`, `"2023"`), floats (`2023.0`), and date strings (`"Dec 2012"`, `"Mar-13"`, `"FY 2023"`) into consistent 4-digit integer years within `1900`–`2100`. Returns `None` for invalid or missing values (`None`, `NaN`, empty strings, invalid text, negative values, booleans).

- **`normalize_ticker(value)`**:
  Trims whitespace and converts stock ticker symbols to uppercase format (e.g., `" reliance "` → `"RELIANCE"`). Preserves exchange suffixes like `.NS` or `.BO` (e.g., `"tcs.ns"` → `"TCS.NS"`). Returns `None` for invalid or non-string inputs.

### 2. `src/etl/loader.py`

- **`load_excel(file_path)`**:
  Loads source `.xlsx` files using `pandas` and `openpyxl`. Automatically detects top-row banner headers (e.g. *"Bluestock Fintech..."*), cleans column names to lowercase `snake_case`, and applies `normalize_year()` and `normalize_ticker()` rules to relevant columns (`year`, `company_id`, `ticker`).

---

## 🧪 Testing

The repository features a test suite with 48 unit tests covering edge cases and real dataset verification.

Run tests using `pytest`:

```bash
pytest
```

Or using `make`:

```bash
make test
```

### Test Coverage Highlights
- **24 tests** for `normalize_year()` (integers, strings, floats, date strings, `None`, `NaN`, invalid text, range bounds, booleans).
- **19 tests** for `normalize_ticker()` (case sensitivity, whitespace trimming, `.NS`/`.BO` exchange suffixes, invalid types).
- **5 tests** for `load_excel()` (missing files, column cleaning, banner header stripping, fixture data, real Excel loading).

---

## 🛠️ Makefile Commands

| Command | Description |
| :--- | :--- |
| `make install` | Install dependencies from `requirements.txt` |
| `make test` | Run the complete unit test suite (`pytest`) |
| `make run` | Execute the ETL loader pipeline |
| `make clean` | Remove Python cache and compiled files |

---

## 🔑 Environment Configuration

Key settings are configured in `.env`:

```env
DB_NAME=nifty100.db
DB_PATH=./nifty100.db
ENVIRONMENT=development
LOG_LEVEL=INFO
```
