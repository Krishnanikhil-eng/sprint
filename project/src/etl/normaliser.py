"""
ETL Normaliser Module
Handles data cleaning, transformation, and normalization for the Nifty 100 ETL pipeline.
"""

import math
import re
from typing import Optional, Union, Any
import pandas as pd


def normalize_year(value: Any) -> Optional[int]:
    """
    Normalizes a year input into a consistent 4-digit integer year (1900 - 2100).

    Handles integer, float, numeric string, and date-like string inputs (e.g. 2023, 2023.0,
    "2023", " 2023 ", "Dec 2012", "Mar-13", "FY 2023").

    Invalid or missing values (None, NaN, empty strings, invalid text, negative numbers,
    unrealistic years outside 1900-2100) return None.

    Args:
        value: Input value representing a year.

    Returns:
        Optional[int]: Normalized 4-digit year as int, or None if invalid.
    """
    if value is None:
        return None

    if isinstance(value, bool):
        return None

    if isinstance(value, float):
        if math.isnan(value) or math.isinf(value):
            return None
        if value.is_integer():
            year_int = int(value)
            return year_int if 1900 <= year_int <= 2100 else None
        return None

    if isinstance(value, int):
        return value if 1900 <= value <= 2100 else None

    if isinstance(value, str):
        cleaned = value.strip()
        if not cleaned:
            return None

        # Check if it's a numeric string like "2023" or "2023.0"
        try:
            val_float = float(cleaned)
            if val_float.is_integer():
                year_int = int(val_float)
                if 1900 <= year_int <= 2100:
                    return year_int
        except ValueError:
            pass

        # Check for 4-digit year pattern (e.g. "Dec 2012", "FY 2023", "2023-24")
        four_digit_match = re.search(r'\b(19\d\d|20\d\d)\b', cleaned)
        if four_digit_match:
            year_int = int(four_digit_match.group(1))
            if 1900 <= year_int <= 2100:
                return year_int

        # Check for Month-YY pattern (e.g. "Mar-13", "Dec-12")
        two_digit_match = re.search(r'^[A-Za-z]{3}[-\s](\d{2})$', cleaned)
        if two_digit_match:
            yy = int(two_digit_match.group(1))
            full_year = 2000 + yy if yy < 50 else 1900 + yy
            if 1900 <= full_year <= 2100:
                return full_year

        return None

    return None


def normalize_ticker(value: Any) -> Optional[str]:
    """
    Normalizes stock ticker strings into uppercase trimmed format.

    Handles leading/trailing whitespace, mixed case, and preserves existing exchange
    suffixes such as '.NS' or '.BO'.

    Invalid or missing values (None, NaN, empty strings, whitespace-only, non-string types)
    return None.

    Args:
        value: Input value representing a ticker symbol.

    Returns:
        Optional[str]: Uppercase trimmed ticker string, or None if invalid.
    """
    if value is None:
        return None

    if isinstance(value, float):
        if math.isnan(value) or math.isinf(value):
            return None

    if not isinstance(value, str):
        return None

    cleaned = value.strip()
    if not cleaned:
        return None

    return cleaned.upper()
