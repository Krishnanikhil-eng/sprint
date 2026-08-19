"""
Unit tests for ETL normaliser module (normalize_year and normalize_ticker).
"""

import math
import numpy as np
import pytest
from src.etl.normaliser import normalize_ticker, normalize_year


# ==============================================================================
# Tests for normalize_year() [22 Tests]
# ==============================================================================

def test_year_integer():
    assert normalize_year(2023) == 2023


def test_year_string():
    assert normalize_year("2023") == 2023


def test_year_whitespace():
    assert normalize_year(" 2023 ") == 2023


def test_year_float():
    assert normalize_year(2023.0) == 2023


def test_year_numeric_string_decimal():
    assert normalize_year("2023.0") == 2023


def test_year_month_four_digit():
    assert normalize_year("Dec 2012") == 2012


def test_year_month_two_digit():
    assert normalize_year("Mar-13") == 2013


def test_year_fy_prefix():
    assert normalize_year("FY 2023") == 2023


def test_year_none():
    assert normalize_year(None) is None


def test_year_nan_float():
    assert normalize_year(float("nan")) is None


def test_year_numpy_nan():
    assert normalize_year(np.nan) is None


def test_year_empty_string():
    assert normalize_year("") is None


def test_year_whitespace_only():
    assert normalize_year("   ") is None


def test_year_invalid_text():
    assert normalize_year("abc") is None


def test_year_negative_value():
    assert normalize_year(-2023) is None


def test_year_zero():
    assert normalize_year(0) is None


def test_year_unrealistic_past():
    assert normalize_year(1700) is None


def test_year_unrealistic_future():
    assert normalize_year(9999) is None


def test_year_consistency_repeated():
    val1 = normalize_year("2023")
    val2 = normalize_year(2023.0)
    assert val1 == val2 == 2023


def test_year_boundary_min():
    assert normalize_year(1900) == 1900


def test_year_boundary_max():
    assert normalize_year(2100) == 2100


def test_year_non_integer_float():
    assert normalize_year(2023.5) is None


def test_year_boolean():
    assert normalize_year(True) is None


def test_year_complex_type():
    assert normalize_year([2023]) is None


# ==============================================================================
# Tests for normalize_ticker() [19 Tests]
# ==============================================================================

def test_ticker_uppercase():
    assert normalize_ticker("RELIANCE") == "RELIANCE"


def test_ticker_lowercase():
    assert normalize_ticker("reliance") == "RELIANCE"


def test_ticker_mixed_case():
    assert normalize_ticker("Reliance") == "RELIANCE"


def test_ticker_leading_whitespace():
    assert normalize_ticker(" RELIANCE") == "RELIANCE"


def test_ticker_trailing_whitespace():
    assert normalize_ticker("RELIANCE ") == "RELIANCE"


def test_ticker_both_whitespace():
    assert normalize_ticker(" RELIANCE ") == "RELIANCE"


def test_ticker_empty_string():
    assert normalize_ticker("") is None


def test_ticker_whitespace_only():
    assert normalize_ticker("   ") is None


def test_ticker_none():
    assert normalize_ticker(None) is None


def test_ticker_nan():
    assert normalize_ticker(np.nan) is None


def test_ticker_ns_suffix():
    assert normalize_ticker("RELIANCE.NS") == "RELIANCE.NS"


def test_ticker_lowercase_ns_suffix():
    assert normalize_ticker("tcs.ns") == "TCS.NS"


def test_ticker_bo_suffix():
    assert normalize_ticker("500325.BO") == "500325.BO"


def test_ticker_unexpected_int_type():
    assert normalize_ticker(12345) is None


def test_ticker_unexpected_list_type():
    assert normalize_ticker(["RELIANCE"]) is None


def test_ticker_with_hyphen():
    assert normalize_ticker("BAJAJ-AUTO") == "BAJAJ-AUTO"


def test_ticker_with_ampersand():
    assert normalize_ticker("m&m") == "M&M"


def test_ticker_already_normalized():
    assert normalize_ticker("INFY") == "INFY"


def test_ticker_boolean():
    assert normalize_ticker(True) is None
