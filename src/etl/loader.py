"""
ETL Loader Module
Handles loading Excel files, cleaning column names, and applying normalization.
"""

import os
from pathlib import Path
from typing import Union
import pandas as pd

from src.etl.normaliser import normalize_ticker, normalize_year


def load_excel(file_path: Union[str, Path]) -> pd.DataFrame:
    """
    Loads an Excel file, cleans column names, and applies normalization rules.

    Args:
        file_path: Path to the .xlsx file to be loaded.

    Returns:
        pd.DataFrame: Loaded and normalized DataFrame.

    Raises:
        FileNotFoundError: If the specified Excel file does not exist.
        ValueError: If file is invalid or cannot be read.
    """
    path_obj = Path(file_path)
    if not path_obj.exists():
        raise FileNotFoundError(f"Excel file not found: {file_path}")

    # Inspect first row to detect if row 0 is a title/banner line
    try:
        raw_df = pd.read_excel(path_obj, nrows=1, header=None)
    except Exception as e:
        raise ValueError(f"Failed to read Excel file '{file_path}': {e}") from e

    header_row = 0
    if not raw_df.empty:
        first_val = str(raw_df.iloc[0, 0])
        if "Fintech" in first_val or "records" in first_val or "Nifty 100" in first_val:
            header_row = 1

    df = pd.read_excel(path_obj, header=header_row)

    # Basic column-name cleaning
    df.columns = [
        str(col).strip().lower().replace(" ", "_").replace("-", "_")
        for col in df.columns
    ]

    # Apply year normalization if 'year' column exists
    if "year" in df.columns:
        df["year"] = df["year"].apply(normalize_year)

    # Apply ticker normalization if 'company_id' or 'ticker' column exists
    for col in ["company_id", "ticker"]:
        if col in df.columns:
            df[col] = df[col].apply(normalize_ticker)

    return df


def load_data():
    """Placeholder function for pipeline loading execution."""
    pass
