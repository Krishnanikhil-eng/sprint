"""
Unit tests for ETL loader module (load_excel).
"""

from pathlib import Path
import pandas as pd
import pytest
from src.etl.loader import load_excel


def test_load_excel_missing_file():
    with pytest.raises(FileNotFoundError):
        load_excel("non_existent_file.xlsx")


def test_load_excel_valid_file(tmp_path):
    # Create temporary Excel file
    df_raw = pd.DataFrame({
        " Company ID ": [" reliance ", "tcs"],
        " YEAR ": ["Dec 2023", "Mar 2022"],
        " SALES ": [1000, 2000]
    })
    excel_path = tmp_path / "sample.xlsx"
    df_raw.to_excel(excel_path, index=False)

    df_loaded = load_excel(excel_path)

    # Check cleaned column names
    assert "company_id" in df_loaded.columns
    assert "year" in df_loaded.columns
    assert "sales" in df_loaded.columns

    # Check ticker normalization
    assert list(df_loaded["company_id"]) == ["RELIANCE", "TCS"]

    # Check year normalization
    assert list(df_loaded["year"]) == [2023, 2022]


def test_load_excel_column_name_cleaning(tmp_path):
    df_raw = pd.DataFrame({
        " Company ID ": ["ABB"],
        "YEAR-END": [2024],
        " Total Revenue ": [500]
    })
    excel_path = tmp_path / "columns_test.xlsx"
    df_raw.to_excel(excel_path, index=False)

    df_loaded = load_excel(excel_path)
    assert set(df_loaded.columns) == {"company_id", "year_end", "total_revenue"}


def test_load_excel_banner_header(tmp_path):
    # Simulate Excel file with top banner row
    banner = ["Bluestock Fintech - Nifty 100 | Balance Sheet | 2 records", "", ""]
    cols = ["id", "company_id", "year"]
    row1 = [1, "infy", "2023"]

    df_banner = pd.DataFrame([banner, cols, row1])
    excel_path = tmp_path / "banner_test.xlsx"
    df_banner.to_excel(excel_path, index=False, header=False)

    df_loaded = load_excel(excel_path)

    assert "company_id" in df_loaded.columns
    assert "year" in df_loaded.columns
    assert df_loaded.iloc[0]["company_id"] == "INFY"
    assert df_loaded.iloc[0]["year"] == 2023


def test_load_excel_real_data_file():
    real_file = Path("data/balancesheet.xlsx")
    if real_file.exists():
        df_loaded = load_excel(real_file)
        assert isinstance(df_loaded, pd.DataFrame)
        assert not df_loaded.empty
        assert "company_id" in df_loaded.columns
        assert "year" in df_loaded.columns
        # Check first company_id is uppercase
        first_company = df_loaded["company_id"].dropna().iloc[0]
        assert first_company == first_company.upper()
