"""Quick database audit script."""
import sqlite3
import os

db_path = "nifty100.db"
if not os.path.exists(db_path):
    print(f"{db_path} does NOT exist")
    exit(1)

conn = sqlite3.connect(db_path)
cur = conn.cursor()

# Tables
cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [t[0] for t in cur.fetchall()]
print("Tables:", tables)

# Companies count
cur.execute("SELECT COUNT(*) FROM companies")
print("Companies:", cur.fetchone()[0])

# Financial ratios
if "financial_ratios" in tables:
    cur.execute("SELECT COUNT(*) FROM financial_ratios")
    print("Financial ratios rows:", cur.fetchone()[0])
    cur.execute("SELECT COUNT(DISTINCT company_id) FROM financial_ratios")
    print("Financial ratios unique companies:", cur.fetchone()[0])
    
    # Check FK violations
    cur.execute("""
        SELECT DISTINCT fr.company_id 
        FROM financial_ratios fr 
        WHERE fr.company_id NOT IN (SELECT company_id FROM companies)
    """)
    orphans = [r[0] for r in cur.fetchall()]
    print(f"FK violations (orphan company_ids in financial_ratios): {len(orphans)}")
    if orphans:
        print("  Orphan IDs:", orphans[:20])

# Sectors
if "sectors" in tables:
    cur.execute("SELECT DISTINCT broad_sector FROM sectors")
    sectors = [r[0] for r in cur.fetchall()]
    print(f"Sectors ({len(sectors)}):", sectors)

# Row counts for all tables
for t in tables:
    cur.execute(f"SELECT COUNT(*) FROM [{t}]")
    print(f"  {t}: {cur.fetchone()[0]} rows")

conn.close()

# Check for data/nifty100.db
print(f"\ndata/nifty100.db exists: {os.path.exists('data/nifty100.db')}")

# Check for config/screener_config.yaml
print(f"config/screener_config.yaml exists: {os.path.exists('config/screener_config.yaml')}")

# Check for reports/radar_charts/
radar_dir = "reports/radar_charts"
if os.path.exists(radar_dir):
    charts = [f for f in os.listdir(radar_dir) if f.endswith('.png')]
    print(f"Radar charts: {len(charts)}")
else:
    print("reports/radar_charts/ does NOT exist")

# Check output files
for f in ["output/screener_output.xlsx", "output/screener_results.xlsx", 
           "output/peer_comparison.xlsx", "output/peer_comparison_report.xlsx"]:
    print(f"{f} exists: {os.path.exists(f)}")
