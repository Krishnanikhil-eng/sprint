"""
Batch Tearsheets & Sector Reports Generator (Day 34).
Runs full batch generation for 92 company tearsheets and 11 sector PDFs, logging skipped companies.
"""

import os
import re
import sqlite3
import pandas as pd
from typing import List, Dict, Any, Tuple

from src.reports.tearsheet import TearsheetGenerator
from src.reports.sector_report import run_sector_reports


def count_pdf_pages(filepath: str) -> int:
    """Helper to count pages in raw PDF using regex."""
    with open(filepath, 'rb') as f:
        content = f.read()
    pages = re.findall(rb'/Type\s*/Page\b', content)
    return len(pages)


def run_batch_tearsheet_generation(
    db_path: str = "nifty100.db",
    output_dir: str = "reports/tearsheets",
    skipped_csv: str = "output/skipped_tearsheets.csv"
) -> Tuple[List[str], List[Dict[str, Any]]]:
    """
    Generates tearsheets for all eligible companies in nifty100.db.
    Skips companies with <3 usable years and logs reasons.
    """
    os.makedirs(output_dir, exist_ok=True)
    os.makedirs(os.path.dirname(skipped_csv), exist_ok=True)

    conn = sqlite3.connect(db_path)
    df_comp = pd.read_sql_query("SELECT company_id, company_name FROM companies ORDER BY company_id", conn)
    df_pnl = pd.read_sql_query("SELECT company_id, year FROM profitandloss", conn)
    conn.close()

    pnl_year_counts = df_pnl.groupby('company_id')['year'].nunique().to_dict()

    generator = TearsheetGenerator(db_path=db_path, output_dir=output_dir)

    generated_files = []
    skipped_records = []

    for _, row in df_comp.iterrows():
        cid = str(row['company_id']).strip()
        c_name = str(row['company_name']).split('\n')[0].strip()
        avail_years = pnl_year_counts.get(cid, 0)

        # Skip companies with <3 usable financial years
        if avail_years < 3:
            skipped_records.append({
                "company_id": cid,
                "ticker": cid,
                "reason": "Insufficient historical data (< 3 usable years)",
                "available_year_count": avail_years
            })
            print(f"Skipping {cid}: insufficient data ({avail_years} years)")
            continue

        out_pdf = os.path.join(output_dir, f"{cid}_tearsheet.pdf")
        try:
            generator.build_pdf(cid, output_path=out_pdf)
            # Verify generated PDF
            if os.path.exists(out_pdf):
                size = os.path.getsize(out_pdf)
                pages = count_pdf_pages(out_pdf)
                if size < 30 * 1024 or pages != 2:
                    skipped_records.append({
                        "company_id": cid,
                        "ticker": cid,
                        "reason": f"PDF validation failure (size: {size} bytes, pages: {pages})",
                        "available_year_count": avail_years
                    })
                else:
                    generated_files.append(out_pdf)
        except Exception as e:
            skipped_records.append({
                "company_id": cid,
                "ticker": cid,
                "reason": f"Generation exception: {str(e)}",
                "available_year_count": avail_years
            })
            print(f"ERROR generating tearsheet for {cid}: {e}")

    generator.close()

    df_skipped = pd.DataFrame(skipped_records, columns=["company_id", "ticker", "reason", "available_year_count"])
    df_skipped.to_csv(skipped_csv, index=False)

    print(f"=== Batch Tearsheet Summary ===")
    print(f"Total Companies Processed: {len(df_comp)}")
    print(f"Successfully Generated Tearsheets: {len(generated_files)}")
    print(f"Skipped / Failed Tearsheets: {len(df_skipped)}")
    print(f"Skipped log saved to -> {skipped_csv}")

    return generated_files, skipped_records


def run_full_day34_batch():
    """Runs batch tearsheets and 11 sector PDF reports."""
    print("--- Starting Batch Company Tearsheet Generation ---")
    tearsheet_files, skipped = run_batch_tearsheet_generation()

    print("\n--- Starting Sector Report Generation ---")
    sector_files = run_sector_reports()

    print(f"\nDay 34 Complete! Generated {len(tearsheet_files)} company tearsheets and {len(sector_files)} sector PDFs.")


if __name__ == "__main__":
    run_full_day34_batch()
