"""
Unit tests for database schema and ETL loader pipeline (load_data).
"""

import sqlite3
from pathlib import Path
import pandas as pd
import pytest
from src.etl.loader import load_data


def test_db_schema_initialization(tmp_path):
    db_file = tmp_path / "test_nifty.db"
    df_audit = load_data(db_path=db_file, output_dir=tmp_path)

    assert db_file.exists()
    conn = sqlite3.connect(db_file)
    conn.execute("PRAGMA foreign_keys = ON;")
    cur = conn.cursor()

    # Check 12 tables created
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name != 'sqlite_sequence';")
    tables = [r[0] for r in cur.fetchall()]
    assert len(tables) == 12

    # Check foreign key pragma enabled
    cur.execute("PRAGMA foreign_keys;")
    assert cur.fetchone()[0] == 1

    # Check PRAGMA foreign_key_check is 0
    fk_violations = cur.execute("PRAGMA foreign_key_check;").fetchall()
    assert len(fk_violations) == 0

    # Check companies table count
    cur.execute("SELECT count(*) FROM companies;")
    assert cur.fetchone()[0] == 92

    conn.close()


def test_load_audit_csv_generation(tmp_path):
    db_file = tmp_path / "test_nifty_audit.db"
    df_audit = load_data(db_path=db_file, output_dir=tmp_path)

    audit_csv = tmp_path / "load_audit.csv"
    assert audit_csv.exists()
    df_read = pd.read_csv(audit_csv)
    assert len(df_read) == 12
    assert "table" in df_read.columns
    assert "rows_loaded" in df_read.columns
    assert "rows_rejected" in df_read.columns
