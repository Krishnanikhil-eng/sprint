"""
ETL Validator Module
Handles schema and data validation prior to transformation, loading, and audit execution.
Implements DQ-01 through DQ-16 with severity classification and failure logging.
"""

from pathlib import Path
from typing import Dict, List, Optional, Union, Any
import pandas as pd
import sqlite3


class DataQualityFailure:
    def __init__(
        self,
        rule_id: str,
        severity: str,
        table: str,
        company_id: Optional[str] = None,
        year: Optional[Union[int, str]] = None,
        field: Optional[str] = None,
        actual_value: Optional[Any] = None,
        message: str = "",
    ):
        self.rule_id = rule_id
        self.severity = severity  # 'CRITICAL' or 'WARNING'
        self.table = table
        self.company_id = company_id
        self.year = year
        self.field = field
        self.actual_value = actual_value
        self.message = message

    def to_dict(self) -> Dict[str, Any]:
        return {
            "rule_id": self.rule_id,
            "severity": self.severity,
            "table": self.table,
            "company_id": self.company_id or "",
            "year": self.year if self.year is not None else "",
            "field": self.field or "",
            "actual_value": (
                str(self.actual_value) if self.actual_value is not None else ""
            ),
            "message": self.message,
        }


class DataQualityValidator:
    """Validator class implementing DQ-01 through DQ-16 data quality rules."""

    def __init__(self, output_dir: Union[str, Path] = "output"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.failures: List[DataQualityFailure] = []
        self.rule_statuses: Dict[str, Dict[str, Any]] = {}

    def log_failure(
        self,
        rule_id: str,
        severity: str,
        table: str,
        company_id: Optional[str] = None,
        year: Optional[Union[int, str]] = None,
        field: Optional[str] = None,
        actual_value: Optional[Any] = None,
        message: str = "",
    ):
        failure = DataQualityFailure(
            rule_id=rule_id,
            severity=severity,
            table=table,
            company_id=company_id,
            year=year,
            field=field,
            actual_value=actual_value,
            message=message,
        )
        self.failures.append(failure)

    def export_failures(self, filename: str = "validation_failures.csv") -> Path:
        output_path = self.output_dir / filename
        df_failures = pd.DataFrame([f.to_dict() for f in self.failures])
        if df_failures.empty:
            df_failures = pd.DataFrame(
                columns=[
                    "rule_id",
                    "severity",
                    "table",
                    "company_id",
                    "year",
                    "field",
                    "actual_value",
                    "message",
                ]
            )
        df_failures.to_csv(output_path, index=False)
        return output_path

    # =========================================================================
    # Individual DQ Rule Implementations (DQ-01 to DQ-16)
    # =========================================================================

    def check_dq01_ticker_format(self, df: pd.DataFrame, table_name: str) -> int:
        """DQ-01: Ticker Format & Validation (CRITICAL). Upper, alphanumeric with optional .NS/.BO/-/_."""
        rule_id = "DQ-01"
        fail_count = 0
        col = (
            "company_id"
            if "company_id" in df.columns
            else ("id" if "id" in df.columns and table_name == "companies" else None)
        )
        if not col:
            return 0

        for idx, row in df.iterrows():
            val = row[col]
            if pd.notna(val):
                s_val = str(val).strip()
                if (
                    not s_val.isupper()
                    or not s_val.replace(".", "")
                    .replace("-", "")
                    .replace("&", "")
                    .isalnum()
                ):
                    fail_count += 1
                    self.log_failure(
                        rule_id,
                        "CRITICAL",
                        table_name,
                        company_id=s_val,
                        field=col,
                        actual_value=val,
                        message="Ticker format is not uppercase or contains invalid characters",
                    )
        return fail_count

    def check_dq02_missing_ticker(self, df: pd.DataFrame, table_name: str) -> int:
        """DQ-02: Missing / Null Ticker Check (CRITICAL)."""
        rule_id = "DQ-02"
        fail_count = 0
        col = (
            "company_id"
            if "company_id" in df.columns
            else ("id" if "id" in df.columns and table_name == "companies" else None)
        )
        if not col:
            return 0

        for idx, row in df.iterrows():
            val = row[col]
            if pd.isna(val) or str(val).strip() == "":
                fail_count += 1
                yr = row.get("year", None) if "year" in df.columns else None
                self.log_failure(
                    rule_id,
                    "CRITICAL",
                    table_name,
                    year=yr,
                    field=col,
                    actual_value=val,
                    message="Company ID/Ticker is null or blank",
                )
        return fail_count

    def check_dq03_duplicate_company(self, df: pd.DataFrame, table_name: str) -> int:
        """DQ-03: Duplicate Company ID Check (CRITICAL). Applies to companies primary entity table."""
        rule_id = "DQ-03"
        if table_name != "companies":
            return 0
        col = "company_id" if "company_id" in df.columns else "id"
        if col not in df.columns:
            return 0

        dups = df[df.duplicated(subset=[col], keep=False)]
        fail_count = len(dups)
        for idx, row in dups.iterrows():
            self.log_failure(
                rule_id,
                "CRITICAL",
                table_name,
                company_id=str(row[col]),
                field=col,
                actual_value=row[col],
                message="Duplicate company_id primary key found in companies table",
            )
        return fail_count

    def check_dq04_year_range(self, df: pd.DataFrame, table_name: str) -> int:
        """DQ-04: Year Range & Format (1900-2100) (WARNING)."""
        rule_id = "DQ-04"
        if "year" not in df.columns:
            return 0

        fail_count = 0
        comp_col = "company_id" if "company_id" in df.columns else "id"
        for idx, row in df.iterrows():
            yr = row["year"]
            if pd.notna(yr):
                try:
                    yr_int = int(float(yr))
                    if yr_int < 1900 or yr_int > 2100:
                        fail_count += 1
                        self.log_failure(
                            rule_id,
                            "WARNING",
                            table_name,
                            company_id=str(row.get(comp_col, "")),
                            year=yr,
                            field="year",
                            actual_value=yr,
                            message=f"Year {yr} is outside expected range 1900-2100",
                        )
                except (ValueError, TypeError):
                    fail_count += 1
                    self.log_failure(
                        rule_id,
                        "WARNING",
                        table_name,
                        company_id=str(row.get(comp_col, "")),
                        year=yr,
                        field="year",
                        actual_value=yr,
                        message=f"Year value '{yr}' cannot be converted to integer",
                    )
        return fail_count

    def check_dq05_missing_year(self, df: pd.DataFrame, table_name: str) -> int:
        """DQ-05: Missing / Null Year Check (CRITICAL). For annual time-series tables."""
        rule_id = "DQ-05"
        time_series_tables = [
            "profitandloss",
            "balancesheet",
            "cashflow",
            "financial_ratios",
            "market_cap",
        ]
        if table_name not in time_series_tables or "year" not in df.columns:
            return 0

        comp_col = "company_id" if "company_id" in df.columns else "id"
        null_yrs = df[df["year"].isna()]
        fail_count = len(null_yrs)
        for idx, row in null_yrs.iterrows():
            self.log_failure(
                rule_id,
                "CRITICAL",
                table_name,
                company_id=str(row.get(comp_col, "")),
                field="year",
                actual_value=None,
                message=f"Missing year in annual financial table {table_name}",
            )
        return fail_count

    def check_dq06_duplicate_year_per_company(
        self, df: pd.DataFrame, table_name: str
    ) -> int:
        """DQ-06: Duplicate Year per Company Check (CRITICAL)."""
        rule_id = "DQ-06"
        time_series_tables = [
            "profitandloss",
            "balancesheet",
            "cashflow",
            "financial_ratios",
            "market_cap",
        ]
        if (
            table_name not in time_series_tables
            or "year" not in df.columns
            or "company_id" not in df.columns
        ):
            return 0

        dups = df[df.duplicated(subset=["company_id", "year"], keep=False)]
        fail_count = len(dups)
        for idx, row in dups.iterrows():
            self.log_failure(
                rule_id,
                "CRITICAL",
                table_name,
                company_id=str(row["company_id"]),
                year=row["year"],
                field="company_id, year",
                actual_value=f"{row['company_id']}-{row['year']}",
                message=f"Duplicate (company_id, year) composite key in {table_name}",
            )
        return fail_count

    def check_dq07_financial_numeric(self, df: pd.DataFrame, table_name: str) -> int:
        """DQ-07: Financial Value Numeric Check (WARNING)."""
        rule_id = "DQ-07"
        numeric_cols = df.select_dtypes(include=["number"]).columns
        fail_count = 0
        comp_col = "company_id" if "company_id" in df.columns else "id"

        for col in numeric_cols:
            if col in ["id", "year"]:
                continue
            invalid = df[df[col].isna() & df[col].notnull()]  # NaN or non-numeric
            # Check for Inf
            inf_rows = df[df[col].isin([float("inf"), float("-inf")])]
            for idx, row in inf_rows.iterrows():
                fail_count += 1
                self.log_failure(
                    rule_id,
                    "WARNING",
                    table_name,
                    company_id=str(row.get(comp_col, "")),
                    year=row.get("year", None),
                    field=col,
                    actual_value=row[col],
                    message=f"Infinite numeric value found in column {col}",
                )
        return fail_count

    def check_dq08_financial_sanity_range(
        self, df: pd.DataFrame, table_name: str
    ) -> int:
        """DQ-08: Financial Value Range / Sanity Check (WARNING)."""
        rule_id = "DQ-08"
        fail_count = 0
        comp_col = "company_id" if "company_id" in df.columns else "id"

        if table_name == "balancesheet" and "total_assets" in df.columns:
            neg_assets = df[df["total_assets"] < 0]
            for idx, row in neg_assets.iterrows():
                fail_count += 1
                self.log_failure(
                    rule_id,
                    "WARNING",
                    table_name,
                    company_id=str(row.get(comp_col, "")),
                    year=row.get("year", None),
                    field="total_assets",
                    actual_value=row["total_assets"],
                    message="Total Assets is negative",
                )
        return fail_count

    def check_dq09_balance_sheet_equation(
        self, df: pd.DataFrame, table_name: str
    ) -> int:
        """DQ-09: Balance Sheet Equation (Assets = Liabilities + Equity) (CRITICAL)."""
        rule_id = "DQ-09"
        if (
            table_name != "balancesheet"
            or "total_assets" not in df.columns
            or "total_liabilities" not in df.columns
        ):
            return 0

        fail_count = 0
        comp_col = "company_id" if "company_id" in df.columns else "id"
        for idx, row in df.iterrows():
            ta = row["total_assets"]
            tl = row["total_liabilities"]
            if pd.notna(ta) and pd.notna(tl):
                diff = abs(float(ta) - float(tl))
                if diff > 1.0:  # Tolerance threshold
                    fail_count += 1
                    self.log_failure(
                        rule_id,
                        "CRITICAL",
                        table_name,
                        company_id=str(row.get(comp_col, "")),
                        year=row.get("year", None),
                        field="total_assets vs total_liabilities",
                        actual_value=f"Assets={ta}, Liab={tl}, Diff={diff}",
                        message=f"Balance sheet accounting discrepancy: Assets ({ta}) != Liabilities ({tl})",
                    )
        return fail_count

    def check_dq10_sales_non_negative(self, df: pd.DataFrame, table_name: str) -> int:
        """DQ-10: Revenue / Sales Non-Negativity Check (CRITICAL)."""
        rule_id = "DQ-10"
        if table_name != "profitandloss" or "sales" not in df.columns:
            return 0

        neg_sales = df[df["sales"] < 0]
        fail_count = len(neg_sales)
        comp_col = "company_id" if "company_id" in df.columns else "id"
        for idx, row in neg_sales.iterrows():
            self.log_failure(
                rule_id,
                "CRITICAL",
                table_name,
                company_id=str(row.get(comp_col, "")),
                year=row.get("year", None),
                field="sales",
                actual_value=row["sales"],
                message="Sales/Revenue value is negative",
            )
        return fail_count

    def check_dq11_cashflow_consistency(self, df: pd.DataFrame, table_name: str) -> int:
        """DQ-11: Cash Flow Net Change Consistency Check (WARNING)."""
        rule_id = "DQ-11"
        if table_name != "cashflow":
            return 0
        cols = [
            "operating_activity",
            "investing_activity",
            "financing_activity",
            "net_cash_flow",
        ]
        if not all(c in df.columns for c in cols):
            return 0

        fail_count = 0
        comp_col = "company_id" if "company_id" in df.columns else "id"
        for idx, row in df.iterrows():
            op = (
                float(row["operating_activity"])
                if pd.notna(row["operating_activity"])
                else 0.0
            )
            inv = (
                float(row["investing_activity"])
                if pd.notna(row["investing_activity"])
                else 0.0
            )
            fin = (
                float(row["financing_activity"])
                if pd.notna(row["financing_activity"])
                else 0.0
            )
            net = float(row["net_cash_flow"]) if pd.notna(row["net_cash_flow"]) else 0.0

            calc_net = op + inv + fin
            diff = abs(calc_net - net)
            if diff > 2.0:  # Tolerance threshold
                fail_count += 1
                self.log_failure(
                    rule_id,
                    "WARNING",
                    table_name,
                    company_id=str(row.get(comp_col, "")),
                    year=row.get("year", None),
                    field="net_cash_flow",
                    actual_value=f"Actual={net}, Calculated={calc_net}, Diff={diff:.2f}",
                    message="Net cash flow does not match sum of operating, investing, and financing activities",
                )
        return fail_count

    def check_dq12_required_fields(self, df: pd.DataFrame, table_name: str) -> int:
        """DQ-12: Required Fields / Columns Presence Check (CRITICAL)."""
        rule_id = "DQ-12"
        required_schema = {
            "companies": ["company_id"],
            "profitandloss": ["company_id", "year", "sales", "net_profit"],
            "balancesheet": ["company_id", "year", "total_assets"],
            "cashflow": ["company_id", "year", "net_cash_flow"],
            "stock_prices": ["company_id", "date", "close_price"],
        }
        if table_name not in required_schema:
            return 0

        fail_count = 0
        missing_cols = [c for c in required_schema[table_name] if c not in df.columns]
        for col in missing_cols:
            fail_count += 1
            self.log_failure(
                rule_id,
                "CRITICAL",
                table_name,
                field=col,
                actual_value=None,
                message=f"Mandatory column '{col}' is missing from table {table_name}",
            )
        return fail_count

    def check_dq13_foreign_key_integrity(
        self, df: pd.DataFrame, table_name: str, valid_companies: set
    ) -> int:
        """DQ-13: Foreign Key / Parent Company Integrity Check (CRITICAL)."""
        rule_id = "DQ-13"
        if table_name == "companies" or "company_id" not in df.columns:
            return 0

        fail_count = 0
        for idx, row in df.iterrows():
            cid = row["company_id"]
            if pd.notna(cid) and str(cid).strip() not in valid_companies:
                fail_count += 1
                self.log_failure(
                    rule_id,
                    "CRITICAL",
                    table_name,
                    company_id=str(cid),
                    year=row.get("year", None),
                    field="company_id",
                    actual_value=cid,
                    message=f"Foreign key violation: company_id '{cid}' not found in companies table",
                )
        return fail_count

    def check_dq14_duplicate_records(self, df: pd.DataFrame, table_name: str) -> int:
        """DQ-14: Duplicate Financial Records Check (WARNING)."""
        rule_id = "DQ-14"
        subset_cols = [c for c in df.columns if c != "id"]
        if not subset_cols:
            return 0

        dups = df[df.duplicated(subset=subset_cols, keep=False)]
        fail_count = len(dups)
        comp_col = "company_id" if "company_id" in df.columns else "id"
        for idx, row in dups.iterrows():
            self.log_failure(
                rule_id,
                "WARNING",
                table_name,
                company_id=str(row.get(comp_col, "")),
                year=row.get("year", None),
                field="entire_row",
                actual_value="Duplicate row",
                message=f"Identical duplicate row detected in table {table_name}",
            )
        return fail_count

    def check_dq15_outlier_detection(self, df: pd.DataFrame, table_name: str) -> int:
        """DQ-15: Outlier / Extreme Value Detection (WARNING)."""
        rule_id = "DQ-15"
        if (
            table_name not in ["profitandloss", "financial_ratios"]
            or "sales" not in df.columns
        ):
            return 0

        fail_count = 0
        comp_col = "company_id" if "company_id" in df.columns else "id"
        sales = df["sales"].dropna()
        if len(sales) > 10:
            mean = sales.mean()
            std = sales.std()
            if std > 0:
                outliers = df[abs(df["sales"] - mean) > 5 * std]
                fail_count = len(outliers)
                for idx, row in outliers.iterrows():
                    self.log_failure(
                        rule_id,
                        "WARNING",
                        table_name,
                        company_id=str(row.get(comp_col, "")),
                        year=row.get("year", None),
                        field="sales",
                        actual_value=row["sales"],
                        message="Extreme outlier sales value (>5 std dev from mean)",
                    )
        return fail_count

    def check_dq16_stock_price_sanity(self, df: pd.DataFrame, table_name: str) -> int:
        """DQ-16: Stock Price Date / Price Sanity Check (CRITICAL)."""
        rule_id = "DQ-16"
        if table_name != "stock_prices":
            return 0

        fail_count = 0
        comp_col = "company_id" if "company_id" in df.columns else "id"
        for idx, row in df.iterrows():
            cid = str(row.get(comp_col, ""))
            dt = row.get("date", None)
            open_p = row.get("open_price", 0)
            high_p = row.get("high_price", 0)
            low_p = row.get("low_price", 0)
            close_p = row.get("close_price", 0)
            vol = row.get("volume", 0)

            # Check low <= high
            if pd.notna(low_p) and pd.notna(high_p) and float(low_p) > float(high_p):
                fail_count += 1
                self.log_failure(
                    rule_id,
                    "CRITICAL",
                    table_name,
                    company_id=cid,
                    field="low_price, high_price",
                    actual_value=f"Low={low_p}, High={high_p}",
                    message="Stock price low_price > high_price sanity failure",
                )

            # Check positive prices
            if pd.notna(close_p) and float(close_p) <= 0:
                fail_count += 1
                self.log_failure(
                    rule_id,
                    "CRITICAL",
                    table_name,
                    company_id=cid,
                    field="close_price",
                    actual_value=close_p,
                    message="Stock close_price is non-positive",
                )
        return fail_count

    # =========================================================================
    # Execution Runner Across All Tables
    # =========================================================================

    def validate_tables(
        self, data_dict: Dict[str, pd.DataFrame]
    ) -> Dict[str, Dict[str, Any]]:
        """
        Runs all DQ-01 through DQ-16 rules against a dictionary of loaded tables {table_name: df}.
        """
        self.failures.clear()
        self.rule_statuses.clear()

        # Build valid company set for FK check (DQ-13)
        valid_companies = set()
        if "companies" in data_dict:
            comp_df = data_dict["companies"]
            col = "company_id" if "company_id" in comp_df.columns else "id"
            if col in comp_df.columns:
                valid_companies = set(comp_df[col].dropna().astype(str).str.strip())

        # Initialize summary metrics for 16 rules
        rule_descriptions = {
            "DQ-01": "Ticker Format & Validation",
            "DQ-02": "Missing / Null Ticker Check",
            "DQ-03": "Duplicate Company ID Check",
            "DQ-04": "Year Range Check (1900-2100)",
            "DQ-05": "Missing / Null Year Check",
            "DQ-06": "Duplicate Year per Company Check",
            "DQ-07": "Financial Value Numeric Check",
            "DQ-08": "Financial Value Range / Sanity Check",
            "DQ-09": "Balance Sheet Accounting Equation Check",
            "DQ-10": "Revenue / Sales Non-Negativity Check",
            "DQ-11": "Cash Flow Net Change Consistency Check",
            "DQ-12": "Required Fields / Columns Presence Check",
            "DQ-13": "Foreign Key / Parent Company Integrity Check",
            "DQ-14": "Duplicate Financial Records Check",
            "DQ-15": "Outlier / Extreme Value Detection",
            "DQ-16": "Stock Price Date / Price Sanity Check",
        }

        rule_counts = {r_id: 0 for r_id in rule_descriptions.keys()}

        for table_name, df in data_dict.items():
            rule_counts["DQ-01"] += self.check_dq01_ticker_format(df, table_name)
            rule_counts["DQ-02"] += self.check_dq02_missing_ticker(df, table_name)
            rule_counts["DQ-03"] += self.check_dq03_duplicate_company(df, table_name)
            rule_counts["DQ-04"] += self.check_dq04_year_range(df, table_name)
            rule_counts["DQ-05"] += self.check_dq05_missing_year(df, table_name)
            rule_counts["DQ-06"] += self.check_dq06_duplicate_year_per_company(
                df, table_name
            )
            rule_counts["DQ-07"] += self.check_dq07_financial_numeric(df, table_name)
            rule_counts["DQ-08"] += self.check_dq08_financial_sanity_range(
                df, table_name
            )
            rule_counts["DQ-09"] += self.check_dq09_balance_sheet_equation(
                df, table_name
            )
            rule_counts["DQ-10"] += self.check_dq10_sales_non_negative(df, table_name)
            rule_counts["DQ-11"] += self.check_dq11_cashflow_consistency(df, table_name)
            rule_counts["DQ-12"] += self.check_dq12_required_fields(df, table_name)
            rule_counts["DQ-13"] += self.check_dq13_foreign_key_integrity(
                df, table_name, valid_companies
            )
            rule_counts["DQ-14"] += self.check_dq14_duplicate_records(df, table_name)
            rule_counts["DQ-15"] += self.check_dq15_outlier_detection(df, table_name)
            rule_counts["DQ-16"] += self.check_dq16_stock_price_sanity(df, table_name)

        # Build summary output dictionary
        rule_severities = {
            "DQ-01": "CRITICAL",
            "DQ-02": "CRITICAL",
            "DQ-03": "CRITICAL",
            "DQ-04": "WARNING",
            "DQ-05": "CRITICAL",
            "DQ-06": "CRITICAL",
            "DQ-07": "WARNING",
            "DQ-08": "WARNING",
            "DQ-09": "CRITICAL",
            "DQ-10": "CRITICAL",
            "DQ-11": "WARNING",
            "DQ-12": "CRITICAL",
            "DQ-13": "CRITICAL",
            "DQ-14": "WARNING",
            "DQ-15": "WARNING",
            "DQ-16": "CRITICAL",
        }

        for r_id, desc in rule_descriptions.items():
            fail_cnt = rule_counts[r_id]
            sev = rule_severities[r_id]
            status = (
                "PASS"
                if fail_cnt == 0
                else ("FAIL (CRITICAL)" if sev == "CRITICAL" else "WARNING")
            )
            self.rule_statuses[r_id] = {
                "rule_id": r_id,
                "description": desc,
                "status": status,
                "severity": sev,
                "failures": fail_cnt,
            }

        self.export_failures()
        return self.rule_statuses

    def validate_database(
        self, db_path: Union[str, Path] = "nifty100.db"
    ) -> Dict[str, Dict[str, Any]]:
        """Runs validation directly on SQLite database tables."""
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        cur.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name != 'sqlite_sequence';"
        )
        tables = [r[0] for r in cur.fetchall()]

        data_dict = {}
        for t in tables:
            data_dict[t] = pd.read_sql_query(f'SELECT * FROM "{t}"', conn)
        conn.close()

        return self.validate_tables(data_dict)


def validate_data(
    data_source: Optional[Union[Dict[str, pd.DataFrame], str, Path]] = "nifty100.db"
):
    """
    Main entry point function for data validation.
    Accepts either a dict of dataframes or path to SQLite database.
    """
    validator = DataQualityValidator()
    if isinstance(data_source, dict):
        return validator.validate_tables(data_source)
    else:
        db_p = Path(data_source) if data_source else Path("nifty100.db")
        if db_p.exists() and db_p.stat().st_size > 0:
            return validator.validate_database(db_p)
        else:
            return validator.rule_statuses
