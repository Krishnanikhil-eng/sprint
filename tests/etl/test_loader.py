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


def test_load_excel_duplicate_columns(tmp_path):
    df_raw = pd.DataFrame([[ "tcs", 2023, 100, 200 ]], columns=["Company ID", "Year", "Sales", "Sales"])
    excel_path = tmp_path / "dup_cols.xlsx"
    df_raw.to_excel(excel_path, index=False)
    df_loaded = load_excel(excel_path)
    assert len(df_loaded.columns) >= 3


def test_load_excel_empty_rows(tmp_path):
    df_raw = pd.DataFrame([
        ["tcs", 2023, 100],
        [None, None, None],
        ["infy", 2024, 200]
    ], columns=["Company ID", "Year", "Sales"])
    excel_path = tmp_path / "empty_rows.xlsx"
    df_raw.to_excel(excel_path, index=False)
    df_loaded = load_excel(excel_path)
    assert len(df_loaded) >= 2


def test_load_excel_column_normalization_case(tmp_path):
    df_raw = pd.DataFrame([["wipro", 2023]], columns=["Company ID", "Year"])
    excel_path = tmp_path / "sheet_test.xlsx"
    df_raw.to_excel(excel_path, index=False)
    df_loaded = load_excel(excel_path)
    assert df_loaded.iloc[0]["company_id"] == "WIPRO"


def test_load_excel_data_types_integrity(tmp_path):
    df_raw = pd.DataFrame([["HDFCBANK", "FY 2023", "1234.56"]], columns=["Company ID", "Year", "Net Profit"])
    excel_path = tmp_path / "types_test.xlsx"
    df_raw.to_excel(excel_path, index=False)
    df_loaded = load_excel(excel_path)
    assert df_loaded.iloc[0]["company_id"] == "HDFCBANK"
    assert df_loaded.iloc[0]["year"] == 2023


def test_load_excel_invalid_extension(tmp_path):
    bad_path = tmp_path / "test.txt"
    bad_path.write_text("not an excel file")
    with pytest.raises(Exception):
        load_excel(bad_path)

