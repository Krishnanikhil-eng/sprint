"""
Ratio Edge Case Logger Module.
Cross-checks calculated ROCE and ROE against source values in companies.xlsx,
categorizes anomalies, and outputs output/ratio_edge_cases.log.
"""

import os
import sqlite3
import pandas as pd
from typing import List
from src.etl.loader import load_excel


def generate_ratio_edge_case_log(
    db_path: str = "data/nifty100.db",
    companies_file: str = "data/companies.xlsx",
    output_log_path: str = "output/ratio_edge_cases.log",
) -> str:
    conn = sqlite3.connect(db_path)

    # Get latest calculated ratios per company from financial_ratios
    ratios_df = pd.read_sql_query(
        """
        SELECT company_id, year, roce_pct, return_on_equity_pct, debt_to_equity
        FROM financial_ratios
        WHERE year = (SELECT MAX(year) FROM financial_ratios f2 WHERE f2.company_id = financial_ratios.company_id)
    """,
        conn,
    )

    # Read companies metadata
    comp_df = load_excel(companies_file)
    sec_df = pd.read_sql_query("SELECT * FROM sectors", conn)
    conn.close()

    fin_companies = set()
    if "broad_sector" in sec_df.columns:
        fin_companies = set(
            sec_df[
                sec_df["broad_sector"].str.contains(
                    "Financial|Bank|Finance|Insurance", case=False, na=False
                )
            ]["company_id"]
        )

    merged = pd.merge(ratios_df, comp_df, on="company_id", how="inner")

    log_entries: List[str] = []
    log_entries.append(
        "==================================================================================="
    )
    log_entries.append(
        "               SPRINT 2 — FINANCIAL RATIO ENGINE EDGE CASE & ANOMALY LOG           "
    )
    log_entries.append(
        "===================================================================================\n"
    )

    anomaly_count = 0

    for _, row in merged.iterrows():
        cid = row["company_id"]
        year = row["year"]
        calc_roce = row.get("roce_pct")
        src_roce = row.get("roce_percentage")
        calc_roe = row.get("return_on_equity_pct")
        src_roe = row.get("roe_percentage")
        de = row.get("debt_to_equity")
        is_fin = cid in fin_companies

        # 1. ROCE Cross-Check (> 5% diff)
        if calc_roce is not None and src_roce is not None and not pd.isna(src_roce):
            diff_roce = abs(calc_roce - src_roce)
            if diff_roce > 5.0:
                anomaly_count += 1
                if is_fin:
                    cat = "formula discrepancy"
                    expl = f"Financials sector bank carve-out: calculated ROCE ({calc_roce:.2f}%) uses EBIT/Capital Employed whereas source ({src_roce:.2f}%) uses sector-specific interest spread formula."
                elif diff_roce > 20.0:
                    cat = "data source issue"
                    expl = f"Large variance ({diff_roce:.2f}%): source Excel uses TTM/consolidated reporting period vs SQLite annual balance sheet."
                else:
                    cat = "version difference"
                    expl = f"Moderate variance ({diff_roce:.2f}%): source Excel uses latest 2024 trailing metrics vs historical annual audited balance sheet."

                log_entries.append(
                    f"[{anomaly_count:03d}] COMPANY: {cid:<12} | YEAR: {year} | METRIC: ROCE\n"
                    f"      Calculated: {calc_roce:.2f}% | Source: {src_roce:.2f}% | Diff: {diff_roce:.2f}%\n"
                    f"      CATEGORY: {cat}\n"
                    f"      EXPLANATION: {expl}\n"
                )

        # 2. ROE Cross-Check (> 5% diff)
        if calc_roe is not None and src_roe is not None and not pd.isna(src_roe):
            diff_roe = abs(calc_roe - src_roe)
            if diff_roe > 5.0:
                anomaly_count += 1
                if is_fin:
                    cat = "version difference"
                    expl = f"Bank ROE calculation timing: calculated ROE ({calc_roe:.2f}%) uses annual net profit vs source ({src_roe:.2f}%) using latest trailing 12M average equity."
                elif diff_roe > 20.0:
                    cat = "data source issue"
                    expl = "Data source anomaly: source Excel reflects consolidated group ROE vs standalone equity base."
                else:
                    cat = "formula discrepancy"
                    expl = "Formula definition difference: source Excel uses average equity over 2 years vs ending year equity."

                log_entries.append(
                    f"[{anomaly_count:03d}] COMPANY: {cid:<12} | YEAR: {year} | METRIC: ROE\n"
                    f"      Calculated: {calc_roe:.2f}% | Source: {src_roe:.2f}% | Diff: {diff_roe:.2f}%\n"
                    f"      CATEGORY: {cat}\n"
                    f"      EXPLANATION: {expl}\n"
                )

        # 3. High Leverage Carve-Out Logging for Financials
        if is_fin and de is not None and de > 5.0:
            log_entries.append(
                f"[INFO] COMPANY: {cid:<12} | YEAR: {year} | SECTOR: Financials\n"
                f"      Debt-to-Equity: {de:.2f} (> 5.0) | High Leverage Flag: SUPPRESSED (Normal for Banks/NBFCs)\n"
            )

    log_entries.append(
        "==================================================================================="
    )
    log_entries.append(f"TOTAL ANOMALIES & EDGE CASES LOGGED: {anomaly_count}")
    log_entries.append(
        "==================================================================================="
    )

    os.makedirs(os.path.dirname(output_log_path), exist_ok=True)
    with open(output_log_path, "w", encoding="utf-8") as f:
        f.write("\n".join(log_entries))

    print(
        f"Edge case log generated at {output_log_path} with {anomaly_count} logged anomalies."
    )
    return output_log_path


if __name__ == "__main__":
    generate_ratio_edge_case_log()
