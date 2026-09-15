"""
Package Final Deliverables Script (Day 44/45).
Archives all key project deliverables into output/final_deliverables/.
"""

import os
import shutil

DELIVERABLES_DIR = os.path.join("output", "final_deliverables")


def package_deliverables():
    os.makedirs(DELIVERABLES_DIR, exist_ok=True)

    files_to_copy = [
        ("nifty100.db", "nifty100.db"),
        ("docs/openapi.json", "openapi.json"),
        ("docs/postman_collection.json", "postman_collection.json"),
        ("docs/analyst_guide.pdf", "analyst_guide.pdf"),
        ("docs/acceptance_checklist.pdf", "acceptance_checklist.pdf"),
        ("output/sprint6_final_validation_report.txt", "sprint6_final_validation_report.txt"),
        ("output/cluster_labels.csv", "cluster_labels.csv"),
        ("output/outlier_report.csv", "outlier_report.csv"),
        ("output/portfolio_stats.csv", "portfolio_stats.csv"),
        ("output/perf_notes.md", "perf_notes.md"),
        ("reports/pytest_report.html", "pytest_report.html"),
        ("reports/elbow_plot.png", "elbow_plot.png"),
        ("reports/correlation_heatmap.png", "correlation_heatmap.png")
    ]

    print("Archiving final deliverables...")
    copied_count = 0
    for src, dst_name in files_to_copy:
        if os.path.exists(src):
            dst = os.path.join(DELIVERABLES_DIR, dst_name)
            shutil.copy2(src, dst)
            copied_count += 1
            print(f"  Copied {src} -> {dst}")
        else:
            print(f"  Warning: {src} not found")

    print(f"Successfully archived {copied_count} files into {DELIVERABLES_DIR}")


if __name__ == "__main__":
    package_deliverables()
