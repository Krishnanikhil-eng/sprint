"""
API Database Module (Day 38).
Provides SQLite connection helpers reusing the canonical nifty100.db database.
"""

import sqlite3
from typing import Generator

DB_PATH_DEFAULT = "nifty100.db"


def get_db_connection(db_path: str = DB_PATH_DEFAULT) -> sqlite3.Connection:
    """Returns a new SQLite connection with row factory configured."""
    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def get_db() -> Generator[sqlite3.Connection, None, None]:
    """FastAPI Dependency for database connection."""
    conn = get_db_connection()
    try:
        yield conn
    finally:
        conn.close()
