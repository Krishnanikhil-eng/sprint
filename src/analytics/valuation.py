"""
Valuation Engine
Computes FCF yield, sector benchmarks, 5yr median PE, and valuation flags for Nifty 100 companies
"""

import sqlite3
import pandas as pd
from pathlib import Path
from typing import Dict

DB_PATH = "nifty100.db"


def get_connection() -> sqlite3.Connection:
    """Get SQLite database connection."""
    db_path = Path(DB_PATH)
    if not db_path.exists():
        db_path = Path(f"../{DB_PATH}")
    return sqlite3.connect(str(db_path))


def load_market_cap_data() -> pd.DataFrame:
    """Load market cap data from database or Excel file."""
    try:
        conn = get_connection()
        try:
            df = pd.read_sql_query("SELECT * FROM market_cap", conn)
            if not df.empty:
                return df
        finally:
            conn.close()
    except Exception as e:
        print(f"Error loading market cap from DB: {e}")

    try:
        market_cap_path = Path("data/market_cap.xlsx")
        if not market_cap_path.exists():
            market_cap_path = Path("../data/market_cap.xlsx")

        if market_cap_path.exists():
            return pd.read_excel(market_cap_path)
    except Exception as e:
        print(f"Error loading market cap data from Excel: {e}")

    print("Warning: market_cap data not found")
    return pd.DataFrame()


def load_financial_ratios() -> pd.DataFrame:
    """Load latest financial ratios from database."""
    conn = get_connection()
    try:
        query = """
        WITH LatestRatios AS (
            SELECT f.*,
                   ROW_NUMBER() OVER (PARTITION BY f.company_id ORDER BY f.year DESC) as rn
            FROM financial_ratios f
        )
        SELECT lr.*
        FROM LatestRatios lr
        WHERE lr.rn = 1;
        """
        df = pd.read_sql_query(query, conn)
        return df
    finally:
        conn.close()


def load_companies_info() -> pd.DataFrame:
    """Load company names and sector information for all 92 companies."""
    conn = get_connection()
    try:
        query = """
        SELECT c.company_id, c.company_name, s.broad_sector
        FROM companies c
        LEFT JOIN sectors s ON c.company_id = s.company_id;
        """
        df = pd.read_sql_query(query, conn)
        return df
    finally:
        conn.close()


def compute_5yr_median_pe(market_cap_df: pd.DataFrame) -> pd.Series:
    """Compute 5-year (or available historical years) median P/E for each company."""
    if market_cap_df.empty or "pe_ratio" not in market_cap_df.columns:
        return pd.Series(dtype=float)

    pe_clean = market_cap_df.dropna(subset=["pe_ratio"])
    pe_clean = pe_clean[pe_clean["pe_ratio"] > 0]
    return pe_clean.groupby("company_id")["pe_ratio"].median()


def compute_fcf_yield(
    market_cap_latest: pd.DataFrame, ratios_df: pd.DataFrame
) -> pd.DataFrame:
    """
    Compute FCF yield for all companies.
    FCF_yield_pct = FCF / market_cap_crore * 100
    """
    if market_cap_latest.empty or ratios_df.empty:
        return pd.DataFrame()

    merged = pd.merge(
        market_cap_latest,
        ratios_df[["company_id", "free_cash_flow_cr"]],
        on="company_id",
        how="left",
    )

    merged["FCF_yield_pct"] = None

    for idx, row in merged.iterrows():
        fcf = row.get("free_cash_flow_cr")
        market_cap = row.get("market_cap_crore")

        if pd.notna(fcf) and pd.notna(market_cap) and market_cap > 0:
            merged.at[idx, "FCF_yield_pct"] = (fcf / market_cap) * 100

    return merged


def calculate_sector_median_pe(valuation_df: pd.DataFrame) -> Dict[str, float]:
    """Calculate median P/E for each broad sector using latest available year."""
    sector_medians = {}

    if (
        "pe_ratio" not in valuation_df.columns
        or "broad_sector" not in valuation_df.columns
    ):
        print("Warning: Required columns (pe_ratio, broad_sector) not found")
        return sector_medians

    for sector in valuation_df["broad_sector"].dropna().unique():
        sector_data = valuation_df[valuation_df["broad_sector"] == sector]
        pe_values = sector_data["pe_ratio"].dropna()
        pe_values = pe_values[pe_values > 0]

        if not pe_values.empty:
            sector_medians[sector] = float(pe_values.median())
            print(f"Sector {sector}: Median P/E = {sector_medians[sector]:.2f}")
        else:
            print(f"Warning: No valid positive P/E values for sector {sector}")

    return sector_medians


def compute_valuation_flags(
    valuation_df: pd.DataFrame, sector_medians: Dict[str, float]
) -> pd.DataFrame:
    """
    Apply valuation flags based on P/E vs sector median:
    - P/E > sector_median * 1.5 => Caution
    - P/E < sector_median * 0.7 => Discount
    - otherwise => Fair
    """
    if valuation_df.empty:
        return valuation_df

    valuation_df["flag"] = "Fair"
    valuation_df["PE_vs_sector_median_pct"] = None

    for idx, row in valuation_df.iterrows():
        pe = row.get("pe_ratio")
        sector = row.get("broad_sector")

        if pd.notna(pe) and sector in sector_medians:
            sector_median = sector_medians[sector]
            if pd.notna(sector_median) and sector_median > 0:
                pe_vs_median = (pe / sector_median) * 100
                valuation_df.at[idx, "PE_vs_sector_median_pct"] = pe_vs_median

                if pe > sector_median * 1.5:
                    valuation_df.at[idx, "flag"] = "Caution"
                elif pe < sector_median * 0.7:
                    valuation_df.at[idx, "flag"] = "Discount"
                else:
                    valuation_df.at[idx, "flag"] = "Fair"

    return valuation_df


def run_valuation_engine() -> pd.DataFrame:
    """Main function to run valuation engine for all 92 companies."""
    print("Running Valuation Engine...")

    # 1. Load companies info (92 rows)
    companies_df = load_companies_info()
    if companies_df.empty:
        print("Error: No company data available")
        return pd.DataFrame()

    # 2. Load market cap data & ratios
    market_cap_df = load_market_cap_data()
    ratios_df = load_financial_ratios()

    # 3. Compute 5-year median PE per company across historical years
    median_pe_5yr_series = compute_5yr_median_pe(market_cap_df)

    # 4. Filter market cap data to latest year per company
    if not market_cap_df.empty and "year" in market_cap_df.columns:
        latest_mc_idx = market_cap_df.groupby("company_id")["year"].idxmax()
        market_cap_latest = market_cap_df.loc[latest_mc_idx].copy()
    else:
        market_cap_latest = market_cap_df.copy()

    # 5. Merge all 92 companies with latest market cap data
    valuation_df = pd.merge(
        companies_df, market_cap_latest, on="company_id", how="left"
    )

    # 6. Compute FCF yield
    if not ratios_df.empty:
        valuation_df = compute_fcf_yield(valuation_df, ratios_df)
    else:
        valuation_df["FCF_yield_pct"] = None

    # 7. Add 5yr_median_PE column
    valuation_df["5yr_median_PE"] = valuation_df["company_id"].map(median_pe_5yr_series)

    # 8. Calculate sector median P/E and valuation flags
    sector_medians = calculate_sector_median_pe(valuation_df)
    valuation_df = compute_valuation_flags(valuation_df, sector_medians)

    # 9. Automatically export summary Excel and flags CSV
    export_valuation_summary(valuation_df)
    export_valuation_flags(valuation_df)

    print(f"Valuation engine completed. Processed {len(valuation_df)} companies.")
    return valuation_df


def export_valuation_summary(
    valuation_df: pd.DataFrame, output_path: str = "output/valuation_summary.xlsx"
) -> None:
    """Export valuation summary to Excel file with exact required columns."""
    if valuation_df.empty:
        print("Warning: No data to export")
        return

    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)

    col_mapping = {
        "company_id": "company_id",
        "company_name": "company_name",
        "broad_sector": "sector",
        "pe_ratio": "P/E",
        "pb_ratio": "P/B",
        "ev_ebitda": "EV/EBITDA",
        "FCF_yield_pct": "FCF_yield_pct",
        "5yr_median_PE": "5yr_median_PE",
        "PE_vs_sector_median_pct": "PE_vs_sector_median_pct",
        "flag": "flag",
    }

    export_df = valuation_df.copy()

    # Ensure all required columns exist
    for src_col in col_mapping.keys():
        if src_col not in export_df.columns:
            export_df[src_col] = None

    export_df = export_df[list(col_mapping.keys())].rename(columns=col_mapping)

    try:
        export_df.to_excel(output_path, index=False)
        print(f"Exported valuation summary to {output_path} with {len(export_df)} rows")
    except Exception as e:
        print(f"Error exporting valuation summary: {e}")


def export_valuation_flags(
    valuation_df: pd.DataFrame, output_path: str = "output/valuation_flags.csv"
) -> None:
    """Export only Caution and Discount flags to CSV."""
    if valuation_df.empty:
        print("Warning: No data to export")
        return

    flags_df = valuation_df[valuation_df["flag"].isin(["Caution", "Discount"])].copy()

    if flags_df.empty:
        print("Warning: No Caution or Discount flags found")
        return

    col_mapping = {
        "company_id": "company_id",
        "company_name": "company_name",
        "broad_sector": "sector",
        "pe_ratio": "P/E",
        "FCF_yield_pct": "FCF_yield_pct",
        "5yr_median_PE": "5yr_median_PE",
        "PE_vs_sector_median_pct": "PE_vs_sector_median_pct",
        "flag": "flag",
    }

    for src_col in col_mapping.keys():
        if src_col not in flags_df.columns:
            flags_df[src_col] = None

    export_df = flags_df[list(col_mapping.keys())].rename(columns=col_mapping)

    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)

    try:
        export_df.to_csv(output_path, index=False)
        print(f"Exported valuation flags to {output_path} with {len(export_df)} rows")
    except Exception as e:
        print(f"Error exporting valuation flags: {e}")


if __name__ == "__main__":
    result = run_valuation_engine()
    if not result.empty:
        print("\nValuation Summary:")
        print(result[["company_id", "FCF_yield_pct", "pe_ratio", "flag"]].head(10))
