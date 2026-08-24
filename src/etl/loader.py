"""
ETL Loader Module
Handles loading Excel files, cleaning column names, applying normalization,
and executing the full database load pipeline into nifty100.db.
"""

import io
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union, Any
import pandas as pd
import sqlite3
import zipfile

from src.etl.normaliser import normalize_ticker, normalize_year


def load_excel(file_path: Union[str, Path, io.BytesIO]) -> pd.DataFrame:
    """
    Loads an Excel file, cleans column names, and applies normalization rules.

    Args:
        file_path: Path to the .xlsx file or BytesIO object to be loaded.

    Returns:
        pd.DataFrame: Loaded and normalized DataFrame.

    Raises:
        FileNotFoundError: If the specified Excel file does not exist.
        ValueError: If file is invalid or cannot be read.
    """
    if isinstance(file_path, (str, Path)):
        path_obj = Path(file_path)
        if not path_obj.exists():
            raise FileNotFoundError(f"Excel file not found: {file_path}")
        source_input = path_obj
    else:
        source_input = file_path

    # Inspect first row to detect if row 0 is a title/banner line
    try:
        raw_df = pd.read_excel(source_input, nrows=1, header=None)
        if isinstance(source_input, io.BytesIO):
            source_input.seek(0)
    except Exception as e:
        raise ValueError(f"Failed to read Excel file '{file_path}': {e}") from e

    header_row = 0
    if not raw_df.empty:
        first_val = str(raw_df.iloc[0, 0])
        if "Fintech" in first_val or "records" in first_val or "Nifty 100" in first_val or "Companies" in first_val:
            header_row = 1

    df = pd.read_excel(source_input, header=header_row)

    # Basic column-name cleaning
    df.columns = [
        str(col).strip().lower().replace(" ", "_").replace("-", "_")
        for col in df.columns
    ]

    # Map 'id' column to 'company_id' if 'id' contains string tickers (e.g. in companies.xlsx)
    if "id" in df.columns and "company_id" not in df.columns:
        if not df.empty and isinstance(df["id"].dropna().iloc[0], str):
            df["company_id"] = df["id"]

    # Apply year normalization if 'year' column exists
    if "year" in df.columns:
        df["year"] = df["year"].apply(normalize_year)

    # Apply ticker normalization if 'company_id' or 'ticker' column exists
    for col in ["company_id", "ticker"]:
        if col in df.columns:
            df[col] = df[col].apply(normalize_ticker)

    return df


def load_data(
    db_path: Union[str, Path] = "nifty100.db",
    data_dir: Union[str, Path] = "data",
    schema_path: Union[str, Path] = "db/schema.sql",
    output_dir: Union[str, Path] = "output",
) -> pd.DataFrame:
    """
    Executes full ETL data load pipeline:
    1. Initializes SQLite schema from schema.sql
    2. Processes 7 core Excel files and 5 supplementary zipped files
    3. Loads parent entity table 'companies' first, followed by child tables
    4. Handles foreign key constraint validation and tracks rejected rows
    5. Exports load audit statistics to output/load_audit.csv
    """
    db_path = Path(db_path)
    data_dir = Path(data_dir)
    schema_path = Path(schema_path)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Re-initialize database schema
    if db_path.exists():
        db_path.unlink()

    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON;")

    if schema_path.exists():
        with open(schema_path, "r", encoding="utf-8") as f:
            conn.executescript(f.read())
        conn.commit()

    audit_logs: List[Dict[str, Any]] = []

    dataset_configs = [
        {"table": "companies", "file": data_dir / "companies.xlsx", "is_zip": False},
        {"table": "profitandloss", "file": data_dir / "profitandloss.xlsx", "is_zip": False},
        {"table": "balancesheet", "file": data_dir / "balancesheet.xlsx", "is_zip": False},
        {"table": "cashflow", "file": data_dir / "cashflow.xlsx", "is_zip": False},
        {"table": "analysis", "file": data_dir / "analysis.xlsx", "is_zip": False},
        {"table": "documents", "file": data_dir / "documents.xlsx", "is_zip": False},
        {"table": "prosandcons", "file": data_dir / "prosandcons.xlsx", "is_zip": False},
        {"table": "sectors", "file": "supporting datasets/sectors.xlsx", "is_zip": True},
        {"table": "peer_groups", "file": "supporting datasets/peer_groups.xlsx", "is_zip": True},
        {"table": "financial_ratios", "file": "supporting datasets/financial_ratios.xlsx", "is_zip": True},
        {"table": "stock_prices", "file": "supporting datasets/stock_prices.xlsx", "is_zip": True},
        {"table": "market_cap", "file": "supporting datasets/market_cap.xlsx", "is_zip": True},
    ]

    zip_file_path = None
    for item in data_dir.glob("*.zip"):
        if "supporting datasets" in item.name.lower():
            zip_file_path = item
            break

    valid_company_ids: set = set()

    for config in dataset_configs:
        table_name = config["table"]
        file_target = config["file"]
        is_zip = config["is_zip"]

        rows_read = 0
        rows_loaded = 0
        rows_rejected = 0
        rejection_reason = "None"
        severity = "INFO"

        try:
            if is_zip:
                if not zip_file_path or not zip_file_path.exists():
                    raise FileNotFoundError(f"Supplementary zip archive not found in {data_dir}")
                with zipfile.ZipFile(zip_file_path, "r") as z:
                    bytes_data = io.BytesIO(z.read(str(file_target).replace("\\", "/")))
                    df_raw = load_excel(bytes_data)
                    source_filename = f"{zip_file_path.name}/{file_target}"
            else:
                df_raw = load_excel(file_target)
                source_filename = Path(file_target).name

            rows_read = len(df_raw)

            if table_name == "companies":
                if "id" in df_raw.columns:
                    df_raw["company_id"] = df_raw["id"]
                valid_company_ids = set(df_raw["company_id"].dropna().astype(str).str.strip())
                valid_cols = [
                    "company_id",
                    "company_logo",
                    "company_name",
                    "chart_link",
                    "about_company",
                    "website",
                    "nse_profile",
                    "bse_profile",
                    "face_value",
                    "book_value",
                    "roce_percentage",
                    "roe_percentage",
                ]
                df_to_insert = df_raw[[c for c in valid_cols if c in df_raw.columns]].drop_duplicates(subset=["company_id"])
                rows_rejected = rows_read - len(df_to_insert)
                if rows_rejected > 0:
                    rejection_reason = "DUPLICATE_COMPANY_ID"
                    severity = "WARNING"
                df_to_insert.to_sql(table_name, conn, if_exists="append", index=False)
                rows_loaded = len(df_to_insert)

            else:
                if "company_id" in df_raw.columns:
                    df_working = df_raw.copy()
                    null_year_count = 0

                    if table_name in ["profitandloss", "balancesheet", "cashflow", "financial_ratios", "market_cap"] and "year" in df_working.columns:
                        valid_year_mask = df_working["year"].notna()
                        null_year_count = int((~valid_year_mask).sum())
                        df_working = df_working[valid_year_mask].copy()
                        df_working["year"] = df_working["year"].astype(int)

                    valid_mask = df_working["company_id"].astype(str).str.strip().isin(valid_company_ids)
                    df_valid = df_working[valid_mask].copy()
                    df_invalid = df_working[~valid_mask].copy()

                    fk_rejected = len(df_invalid)
                    rows_rejected = fk_rejected + null_year_count

                    reasons = []
                    if null_year_count > 0:
                        reasons.append(f"NULL_YEAR_SUMMARY_ROW ({null_year_count} rows)")
                    if fk_rejected > 0:
                        reasons.append(f"FK_VIOLATION_MISSING_PARENT_COMPANY ({fk_rejected} rows)")

                    rejection_reason = " | ".join(reasons) if reasons else "None"
                    severity = "WARNING" if rows_rejected > 0 else "INFO"

                    if "id" in df_valid.columns:
                        df_valid = df_valid.drop(columns=["id"])

                    if table_name in ["profitandloss", "balancesheet", "cashflow", "financial_ratios", "market_cap"]:
                        if "year" in df_valid.columns:
                            df_valid = df_valid.drop_duplicates(subset=["company_id", "year"])
                    elif table_name == "stock_prices":
                        if "date" in df_valid.columns:
                            df_valid = df_valid.drop_duplicates(subset=["company_id", "date"])

                    cur = conn.cursor()
                    cur.execute(f"PRAGMA table_info('{table_name}')")
                    db_cols = [r[1] for r in cur.fetchall() if r[1] != "id"]

                    cols_to_use = [c for c in db_cols if c in df_valid.columns]
                    df_to_insert = df_valid[cols_to_use]

                    df_to_insert.to_sql(table_name, conn, if_exists="append", index=False)
                    rows_loaded = len(df_to_insert)
                else:
                    rows_rejected = rows_read
                    rejection_reason = "MISSING_COMPANY_ID_COLUMN"
                    severity = "CRITICAL"

            conn.commit()

        except Exception as e:
            rows_loaded = 0
            rows_rejected = rows_read
            rejection_reason = f"LOAD_ERROR: {str(e)}"
            severity = "CRITICAL"
            source_filename = str(file_target)

        audit_logs.append(
            {
                "table": table_name,
                "source_file": source_filename,
                "rows_read": rows_read,
                "rows_loaded": rows_loaded,
                "rows_rejected": rows_rejected,
                "rejection_reason": rejection_reason,
                "severity": severity,
            }
        )

    conn.close()

    df_audit = pd.DataFrame(audit_logs)
    audit_csv_path = output_dir / "load_audit.csv"
    df_audit.to_csv(audit_csv_path, index=False)
    return df_audit


if __name__ == "__main__":
    load_data()
