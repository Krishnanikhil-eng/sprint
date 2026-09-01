"""
End-to-End Ratio Engine Pipeline Orchestrator.
Runs the complete Sprint 2 Financial Ratio Engine workflow:
1. Executes ratio engine computation and updates nifty100.db
2. Exports output/capital_allocation.csv
3. Generates output/ratio_edge_cases.log
4. Runs manual spot checks and screener validation
"""

import sys
from typing import Dict, Any

from src.analytics.ratio_engine import run_ratio_engine
from src.analytics.capital_allocation_exporter import export_capital_allocation
from src.analytics.ratio_edge_case_logger import generate_ratio_edge_case_log
from src.analytics.manual_spot_check import run_manual_spot_checks
from src.analytics.screener_preview import run_screener_preview

def run_sprint2_pipeline(db_path: str = 'nifty100.db') -> Dict[str, Any]:
    print("===================================================================================")
    print("           EXECUTING SPRINT 2 — FINANCIAL RATIO ENGINE FULL PIPELINE               ")
    print("===================================================================================")
    
    # 1. Ratio Engine Run
    df_ratios = run_ratio_engine(db_path)
    
    # 2. Capital Allocation Export
    csv_path = export_capital_allocation(db_path)
    
    # 3. Ratio Edge Case Logging
    log_path = generate_ratio_edge_case_log(db_path)
    
    # 4. Manual Spot Checks
    spot_pass = run_manual_spot_checks(db_path)
    
    # 5. Screener Preview
    df_screener = run_screener_preview(db_path)
    
    pipeline_summary = {
        'total_ratio_rows': len(df_ratios),
        'capital_allocation_csv': csv_path,
        'edge_case_log': log_path,
        'spot_check_passed': spot_pass,
        'screener_matching_companies': len(df_screener)
    }
    
    print("\n===================================================================================")
    print("                    SPRINT 2 PIPELINE EXECUTION SUMMARY                            ")
    print("===================================================================================")
    print(f"1. financial_ratios rows populated : {pipeline_summary['total_ratio_rows']}")
    print(f"2. Capital allocation CSV generated  : {pipeline_summary['capital_allocation_csv']}")
    print(f"3. Edge case log generated          : {pipeline_summary['edge_case_log']}")
    print(f"4. 3-Company spot checks result     : {'PASS' if spot_pass else 'FAIL'}")
    print(f"5. Equity screener matching count   : {pipeline_summary['screener_matching_companies']} companies")
    print("===================================================================================")
    return pipeline_summary

if __name__ == '__main__':
    run_sprint2_pipeline()
