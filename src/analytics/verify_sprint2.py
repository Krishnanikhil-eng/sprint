"""
Full Sprint 2 Financial Ratio Engine Verification & Audit Script.
Executes end-to-end pipeline, runs database health audits, bank carve-out audits,
manual spot checks, equity screener, and reports final exit status.
"""

import sys
from src.analytics.pipeline import run_sprint2_pipeline
from src.analytics.db_ratio_validator import validate_financial_ratios_db
from src.analytics.bank_benchmark_validator import validate_bank_carveout_rules

def verify_all_sprint2() -> bool:
    print("===================================================================================")
    print("      FINAL SPRINT 2 FINANCIAL RATIO ENGINE VERIFICATION & EXIT AUDIT              ")
    print("===================================================================================")
    
    # 1. Pipeline Execution
    pipeline_res = run_sprint2_pipeline()
    
    # 2. Database Health & Completeness Audit
    db_res = validate_financial_ratios_db()
    
    # 3. Bank Sector Carve-Out Audit
    bank_res = validate_bank_carveout_rules()
    
    final_success = (
        pipeline_res['total_ratio_rows'] >= 1100 and
        pipeline_res['spot_check_passed'] and
        15 <= pipeline_res['screener_matching_companies'] <= 50 and
        db_res['validation_passed'] and
        bank_res['passed']
    )
    
    print("\n===================================================================================")
    print(f"FINAL SPRINT 2 EXIT VERIFICATION RESULT: {'SUCCESS (100% Exit Criteria Met)' if final_success else 'FAILURE'}")
    print("===================================================================================")
    
    return final_success

if __name__ == '__main__':
    verify_all_sprint2()
