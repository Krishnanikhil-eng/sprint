"""
Valuation Engine
Computes FCF yield, sector benchmarks, and valuation flags for Nifty 100 companies
"""

import sqlite3
import pandas as pd
from pathlib import Path
from typing import Optional, Dict, Any

DB_PATH = "nifty100.db"


def get_connection() -> sqlite3.Connection:
    """Get SQLite database connection."""
    db_path = Path(DB_PATH)
    if not db_path.exists():
        db_path = Path(f"../{DB_PATH}")
    return sqlite3.connect(str(db_path))


def load_market_cap_data() -> pd.DataFrame:
    """Load market cap data from Excel file."""
    try:
        market_cap_path = Path("data/market_cap.xlsx")
        if not market_cap_path.exists():
            market_cap_path = Path(f"../data/market_cap.xlsx")
        
        if market_cap_path.exists():
            return pd.read_excel(market_cap_path)
        else:
            print("Warning: market_cap.xlsx not found")
            return pd.DataFrame()
    except Exception as e:
        print(f"Error loading market cap data: {e}")
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


def load_company_sectors() -> pd.DataFrame:
    """Load company sector information."""
    conn = get_connection()
    try:
        query = """
        SELECT c.company_id, s.broad_sector
        FROM companies c
        LEFT JOIN sectors s ON c.company_id = s.company_id;
        """
        df = pd.read_sql_query(query, conn)
        return df
    finally:
        conn.close()


def compute_fcf_yield(market_cap_df: pd.DataFrame, ratios_df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute FCF yield for all companies.
    FCF_yield_pct = FCF / market_cap_crore * 100
    """
    if market_cap_df.empty or ratios_df.empty:
        return pd.DataFrame()
    
    # Validate inputs
    missing_market_cap = market_cap_df['market_cap_crore'].isna().sum()
    zero_market_cap = (market_cap_df['market_cap_crore'] == 0).sum()
    missing_fcf = ratios_df['free_cash_flow_cr'].isna().sum()
    
    if missing_market_cap > 0:
        print(f"Warning: {missing_market_cap} companies missing market cap")
    if zero_market_cap > 0:
        print(f"Warning: {zero_market_cap} companies with zero market cap")
    if missing_fcf > 0:
        print(f"Warning: {missing_fcf} companies missing FCF")
    
    # Merge market cap with ratios
    merged = pd.merge(
        market_cap_df,
        ratios_df,
        on='company_id',
        how='inner'
    )
    
    # Check for duplicates
    duplicates = merged['company_id'].duplicated().sum()
    if duplicates > 0:
        print(f"Warning: {duplicates} duplicate company IDs found")
        merged = merged.drop_duplicates(subset=['company_id'])
    
    # Compute FCF yield
    merged['FCF_yield_pct'] = None
    
    for idx, row in merged.iterrows():
        fcf = row.get('free_cash_flow_cr')
        market_cap = row.get('market_cap_crore')
        
        if pd.notna(fcf) and pd.notna(market_cap) and market_cap != 0:
            merged.at[idx, 'FCF_yield_pct'] = (fcf / market_cap) * 100
    
    return merged


def calculate_sector_median_pe(valuation_df: pd.DataFrame) -> Dict[str, float]:
    """Calculate median P/E for each broad sector using latest available year."""
    sector_medians = {}
    
    if 'pe_ratio' not in valuation_df.columns or 'broad_sector' not in valuation_df.columns:
        print("Warning: Required columns (pe_ratio, broad_sector) not found")
        return sector_medians
    
    missing_pe = valuation_df['pe_ratio'].isna().sum()
    if missing_pe > 0:
        print(f"Warning: {missing_pe} companies missing P/E values")
    
    for sector in valuation_df['broad_sector'].dropna().unique():
        sector_data = valuation_df[valuation_df['broad_sector'] == sector]
        pe_values = sector_data['pe_ratio'].dropna()
        
        if not pe_values.empty:
            sector_medians[sector] = pe_values.median()
            print(f"Sector {sector}: Median P/E = {sector_medians[sector]:.2f}")
        else:
            print(f"Warning: No valid P/E values for sector {sector}")
    
    return sector_medians


def compute_valuation_flags(valuation_df: pd.DataFrame, sector_medians: Dict[str, float]) -> pd.DataFrame:
    """
    Apply valuation flags based on P/E vs sector median:
    - P/E > sector_median * 1.5 => Caution
    - P/E < sector_median * 0.7 => Discount
    - otherwise => Fair
    """
    if valuation_df.empty:
        return valuation_df
    
    valuation_df['flag'] = 'Fair'
    valuation_df['PE_vs_sector_median_pct'] = None
    
    missing_benchmark_count = 0
    
    for idx, row in valuation_df.iterrows():
        pe = row.get('pe_ratio')
        sector = row.get('broad_sector')
        
        if pd.notna(pe) and sector in sector_medians:
            sector_median = sector_medians[sector]
            if pd.notna(sector_median) and sector_median != 0:
                pe_vs_median = (pe / sector_median) * 100
                valuation_df.at[idx, 'PE_vs_sector_median_pct'] = pe_vs_median
                
                if pe > sector_median * 1.5:
                    valuation_df.at[idx, 'flag'] = 'Caution'
                elif pe < sector_median * 0.7:
                    valuation_df.at[idx, 'flag'] = 'Discount'
            else:
                missing_benchmark_count += 1
        else:
            if pd.notna(pe):
                missing_benchmark_count += 1
    
    if missing_benchmark_count > 0:
        print(f"Warning: {missing_benchmark_count} companies could not be flagged due to missing sector benchmark or P/E")
    
    return valuation_df


def run_valuation_engine() -> pd.DataFrame:
    """Main function to run valuation engine."""
    print("Running Valuation Engine...")
    
    # Load data
    market_cap_df = load_market_cap_data()
    ratios_df = load_financial_ratios()
    sectors_df = load_company_sectors()
    
    if market_cap_df.empty:
        print("Warning: No market cap data available")
        return pd.DataFrame()
    
    if ratios_df.empty:
        print("Warning: No financial ratios available")
        return pd.DataFrame()
    
    # Compute FCF yield
    valuation_df = compute_fcf_yield(market_cap_df, ratios_df)
    
    if valuation_df.empty:
        print("Warning: No companies matched between market cap and ratios")
        return pd.DataFrame()
    
    # Merge with sector info
    valuation_df = pd.merge(valuation_df, sectors_df, on='company_id', how='left')
    
    # Calculate sector median P/E
    sector_medians = calculate_sector_median_pe(valuation_df)
    
    # Compute valuation flags
    valuation_df = compute_valuation_flags(valuation_df, sector_medians)
    
    print(f"Valuation engine completed. Processed {len(valuation_df)} companies.")
    return valuation_df


def export_valuation_summary(valuation_df: pd.DataFrame, output_path: str = "output/valuation_summary.xlsx") -> None:
    """Export valuation summary to Excel file."""
    if valuation_df.empty:
        print("Warning: No data to export")
        return
    
    # Create output directory if it doesn't exist
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Select required columns
    required_cols = [
        'company_id',
        'company_name',
        'broad_sector',
        'pe_ratio',
        'pb_ratio',
        'ev_ebitda',
        'FCF_yield_pct',
        'PE_vs_sector_median_pct',
        'flag'
    ]
    
    # Add 5yr_median_PE placeholder (using current PE as proxy)
    if 'pe_ratio' in valuation_df.columns:
        valuation_df['5yr_median_PE'] = valuation_df['pe_ratio']
        required_cols.insert(7, '5yr_median_PE')
    
    # Filter available columns
    export_cols = [col for col in required_cols if col in valuation_df.columns]
    export_df = valuation_df[export_cols].copy()
    
    # Rename columns for output
    col_rename = {
        'company_id': 'company_id',
        'company_name': 'company_name',
        'broad_sector': 'sector',
        'pe_ratio': 'P/E',
        'pb_ratio': 'P/B',
        'ev_ebitda': 'EV/EBITDA',
        'FCF_yield_pct': 'FCF_yield_pct',
        '5yr_median_PE': '5yr_median_PE',
        'PE_vs_sector_median_pct': 'PE_vs_sector_median_pct',
        'flag': 'flag'
    }
    export_df = export_df.rename(columns=col_rename)
    
    # Export to Excel
    try:
        export_df.to_excel(output_path, index=False)
        print(f"Exported valuation summary to {output_path} with {len(export_df)} rows")
    except Exception as e:
        print(f"Error exporting valuation summary: {e}")


def export_valuation_flags(valuation_df: pd.DataFrame, output_path: str = "output/valuation_flags.csv") -> None:
    """Export only Caution and Discount flags to CSV."""
    if valuation_df.empty:
        print("Warning: No data to export")
        return
    
    # Filter for Caution and Discount flags
    flags_df = valuation_df[valuation_df['flag'].isin(['Caution', 'Discount'])].copy()
    
    if flags_df.empty:
        print("Warning: No Caution or Discount flags found")
        return
    
    # Select relevant columns
    export_cols = ['company_id', 'company_name', 'broad_sector', 'pe_ratio', 'FCF_yield_pct', 'flag']
    available_cols = [col for col in export_cols if col in flags_df.columns]
    export_df = flags_df[available_cols].copy()
    
    # Create output directory if it doesn't exist
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Export to CSV
    try:
        export_df.to_csv(output_path, index=False)
        print(f"Exported valuation flags to {output_path} with {len(export_df)} rows")
    except Exception as e:
        print(f"Error exporting valuation flags: {e}")


if __name__ == '__main__':
    result = run_valuation_engine()
    if not result.empty:
        print("\nValuation Summary:")
        print(result[['company_id', 'FCF_yield_pct', 'pe_ratio', 'flag']].head(10))
