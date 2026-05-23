"""
Read-only connection factory for pilot.db.

Always opens with SQLite URI mode=ro. The application NEVER writes to this database.
Only the data_access module calls get_pilot_conn(); nothing else touches SQL directly.
"""

import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path

_DEFAULT_PATH = Path("data/pilot.db")


def get_pilot_db_path() -> Path:
    env = os.environ.get("PILOT_DB_PATH")
    return Path(env) if env else _DEFAULT_PATH


@contextmanager
def get_pilot_conn():
    """Yields a read-only sqlite3.Connection to pilot.db."""
    path = get_pilot_db_path()
    conn = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()
