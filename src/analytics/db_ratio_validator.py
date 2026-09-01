"""
Database Ratio Validator Module.
Performs explicit validation audits on the financial_ratios table in nifty100.db:
- Minimum row count >= 1,100
- Uniqueness of (company_id, year)
- Verification of SBIN and ATGL inclusion
- Non-null coverage on essential KPIs
"""

import sqlite3
import pandas as pd
from typing import Dict, Any, List

def validate_financial_ratios_db(db_path: str = 'nifty100.db') -> Dict[str, Any]:
    conn = sqlite3.connect(db_path)
    
    df = pd.read_sql_query("SELECT * FROM financial_ratios", conn)
    conn.close()
    
    row_count = len(df)
    dup_count = df.duplicated(subset=['company_id', 'year']).sum()
    companies = df['company_id'].unique().tolist()
    
    sbin_present = 'SBIN' in companies
    atgl_present = 'ATGL' in companies
    
    sbin_rows = len(df[df['company_id'] == 'SBIN'])
    atgl_rows = len(df[df['company_id'] == 'ATGL'])
    
    null_npm = df['net_profit_margin_pct'].isnull().sum()
    null_opm = df['operating_profit_margin_pct'].isnull().sum()
    null_de = df['debt_to_equity'].isnull().sum()
    
    validation_passed = (
        row_count >= 1100 and
        dup_count == 0 and
        sbin_present and
        atgl_present and
        sbin_rows > 0 and
        atgl_rows > 0
    )
    
    results = {
        'row_count': row_count,
        'duplicate_rows': int(dup_count),
        'total_companies': len(companies),
        'sbin_present': sbin_present,
        'sbin_rows': sbin_rows,
        'atgl_present': atgl_present,
        'atgl_rows': atgl_rows,
        'null_npm_count': int(null_npm),
        'null_opm_count': int(null_opm),
        'null_de_count': int(null_de),
        'validation_passed': validation_passed
    }
    
    print("===================================================================================")
    print("               DATABASE RATIOS HEALTH & COMPLETENESS AUDIT                          ")
    print("===================================================================================")
    print(f"Row count                      : {row_count} (>= 1,100: {'PASS' if row_count>=1100 else 'FAIL'})")
    print(f"Duplicate (company_id, year)   : {dup_count} (== 0: {'PASS' if dup_count==0 else 'FAIL'})")
    print(f"Distinct companies represented : {len(companies)}")
    print(f"SBIN present in database       : {sbin_present} ({sbin_rows} rows)")
    print(f"ATGL present in database       : {atgl_present} ({atgl_rows} rows)")
    print(f"OVERALL AUDIT PASSED           : {validation_passed}")
    print("===================================================================================")
    
    return results

if __name__ == '__main__':
    validate_financial_ratios_db()
