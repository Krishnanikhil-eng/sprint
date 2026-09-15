"""
NLP Analysis Text Parser Module (Day 29)
Parses text fields from analysis.xlsx into structured CAGR/metric data with CAGR cross-validation.
"""

import os
import re
import sqlite3
import pandas as pd
from typing import Tuple, Optional, Dict, Any

from src.analytics.cagr import calculate_series_cagr

# Primary Regex Pattern: (\d+)\s*Years?\s*:?\s*([-\d.]+)%
PARSE_REGEX = re.compile(r"(\d+)\s*Years?\s*:?\s*([-\d.]+)%", re.IGNORECASE)

TARGET_FIELDS = [
    "compounded_sales_growth",
    "compounded_profit_growth",
    "stock_price_cagr",
    "roe",
]


def parse_metric_text(
    text_val: Any,
) -> Tuple[Optional[int], Optional[float], Optional[str]]:
    """
    Parses string input into (period_years, value_pct, failure_reason).
    Returns (None, None, failure_reason) if parsing fails.
    """
    if pd.isna(text_val) or text_val is None:
        return None, None, "Empty or NaN value"

    val_str = str(text_val).strip()
    if not val_str:
        return None, None, "Empty string"

    match = PARSE_REGEX.search(val_str)
    if not match:
        return None, None, f"Regex match failed for pattern '{val_str}'"

    try:
        period_years = int(match.group(1))
        value_pct = float(match.group(2))
        return period_years, value_pct, None
    except (ValueError, TypeError) as e:
        return None, None, f"Conversion error: {str(e)}"


def validate_cagr_against_db(
    company_id: str,
    metric_type: str,
    period_years: int,
    parsed_value: float,
    conn: sqlite3.Connection,
) -> Dict[str, Any]:
    """
    Cross-validates parsed CAGR value against Ratio Engine CAGR / DB values.
    Returns validation info dict.
    """
    computed_value = None

    if metric_type == "compounded_sales_growth":
        df_pnl = pd.read_sql_query(
            "SELECT year, sales FROM profitandloss WHERE company_id = ? AND sales IS NOT NULL ORDER BY year",
            conn,
            params=(company_id,),
        )
        if not df_pnl.empty and len(df_pnl) >= 2:
            time_series = dict(
                zip(df_pnl["year"].astype(int), df_pnl["sales"].astype(float))
            )
            end_year = max(time_series.keys())
            computed_value, _ = calculate_series_cagr(
                time_series, end_year, period_years
            )

    elif metric_type == "compounded_profit_growth":
        df_pnl = pd.read_sql_query(
            "SELECT year, net_profit FROM profitandloss WHERE company_id = ? AND net_profit IS NOT NULL ORDER BY year",
            conn,
            params=(company_id,),
        )
        if not df_pnl.empty and len(df_pnl) >= 2:
            time_series = dict(
                zip(df_pnl["year"].astype(int), df_pnl["net_profit"].astype(float))
            )
            end_year = max(time_series.keys())
            computed_value, _ = calculate_series_cagr(
                time_series, end_year, period_years
            )

    elif metric_type == "roe":
        df_roe = pd.read_sql_query(
            "SELECT return_on_equity_pct FROM financial_ratios WHERE company_id = ? ORDER BY year DESC LIMIT 1",
            conn,
            params=(company_id,),
        )
        if not df_roe.empty and df_roe["return_on_equity_pct"].iloc[0] is not None:
            computed_value = float(df_roe["return_on_equity_pct"].iloc[0])

    elif metric_type == "stock_price_cagr":
        df_prices = pd.read_sql_query(
            "SELECT date, close_price FROM stock_prices WHERE company_id = ? ORDER BY date",
            conn,
            params=(company_id,),
        )
        if not df_prices.empty and len(df_prices) >= 2:
            df_prices["year"] = pd.to_datetime(df_prices["date"]).dt.year
            yearly = df_prices.groupby("year")["close_price"].last().to_dict()
            if yearly:
                end_yr = max(yearly.keys())
                computed_value, _ = calculate_series_cagr(yearly, end_yr, period_years)

    divergence_pct = None
    review_flag = "UNKNOWN"

    if computed_value is not None:
        computed_value = round(computed_value, 2)
        divergence_pct = round(abs(parsed_value - computed_value), 2)
        if divergence_pct > 5.0:
            review_flag = "DIVERGENCE_HIGH"
        else:
            review_flag = "VALIDATED"
    else:
        review_flag = "NO_COMPUTED_DATA"

    return {
        "company_id": company_id,
        "metric_type": metric_type,
        "period_years": period_years,
        "parsed_value": parsed_value,
        "computed_value": computed_value,
        "divergence_pct": divergence_pct,
        "review_flag": review_flag,
    }


def process_analysis_file(
    excel_path: str = "data/analysis.xlsx",
    db_path: str = "nifty100.db",
    output_dir: str = "output",
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Reads data/analysis.xlsx, parses text columns, logs failures, cross-validates CAGRs,
    and writes outputs.
    """
    os.makedirs(output_dir, exist_ok=True)

    # Header row is index 1 in analysis.xlsx
    df = pd.read_excel(excel_path, header=1)

    parsed_records = []
    failure_records = []
    validation_records = []

    conn = sqlite3.connect(db_path) if os.path.exists(db_path) else None

    for _, row in df.iterrows():
        company_id = str(row.get("company_id", "")).strip()
        if not company_id or pd.isna(row.get("company_id")):
            continue

        for metric in TARGET_FIELDS:
            if metric not in df.columns:
                continue

            raw_val = row.get(metric)
            period_years, value_pct, failure_reason = parse_metric_text(raw_val)

            if failure_reason is not None:
                failure_records.append(
                    {
                        "company_id": company_id,
                        "metric_type": metric,
                        "original_value": "" if pd.isna(raw_val) else str(raw_val),
                        "failure_reason": failure_reason,
                    }
                )
            else:
                parsed_records.append(
                    {
                        "company_id": company_id,
                        "metric_type": metric,
                        "period_years": period_years,
                        "value_pct": value_pct,
                    }
                )

                if conn:
                    val_res = validate_cagr_against_db(
                        company_id=company_id,
                        metric_type=metric,
                        period_years=period_years,
                        parsed_value=value_pct,
                        conn=conn,
                    )
                    validation_records.append(val_res)

    if conn:
        conn.close()

    df_parsed = pd.DataFrame(
        parsed_records,
        columns=["company_id", "metric_type", "period_years", "value_pct"],
    )
    df_failures = pd.DataFrame(
        failure_records,
        columns=["company_id", "metric_type", "original_value", "failure_reason"],
    )
    df_validation = pd.DataFrame(
        validation_records,
        columns=[
            "company_id",
            "metric_type",
            "period_years",
            "parsed_value",
            "computed_value",
            "divergence_pct",
            "review_flag",
        ],
    )

    parsed_csv = os.path.join(output_dir, "analysis_parsed.csv")
    failures_csv = os.path.join(output_dir, "parse_failures.csv")
    validation_csv = os.path.join(output_dir, "cagr_validation.csv")

    df_parsed.to_csv(parsed_csv, index=False)
    df_failures.to_csv(failures_csv, index=False)
    df_validation.to_csv(validation_csv, index=False)

    print(f"Parsed {len(df_parsed)} records -> {parsed_csv}")
    print(f"Logged {len(df_failures)} failures -> {failures_csv}")
    print(f"Validated {len(df_validation)} CAGR records -> {validation_csv}")

    return df_parsed, df_failures, df_validation


if __name__ == "__main__":
    process_analysis_file()
