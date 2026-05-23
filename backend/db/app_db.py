"""
app.db — the app-owned case store.

This is the ONLY database the application writes to.
pilot.db is never touched by any code in this module.
"""

import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path

_DEFAULT_PATH = Path("data/app.db")

_CREATE_CASES = """
CREATE TABLE IF NOT EXISTS cases (
    case_id             TEXT PRIMARY KEY,
    created_at          TEXT NOT NULL,
    intake              TEXT,
    triage_result       TEXT,
    workflow_outputs    TEXT,
    generated_documents TEXT,
    escalation_status   TEXT NOT NULL DEFAULT 'none'
                        CHECK(escalation_status IN
                              ('none','recommended','requested','in_queue')),
    gate_decision       TEXT
)
"""


def get_app_db_path() -> Path:
    env = os.environ.get("APP_DB_PATH")
    return Path(env) if env else _DEFAULT_PATH


def init_app_db(app_db_path: Path | None = None) -> None:
    """Create app.db and apply schema. Safe to call repeatedly (IF NOT EXISTS)."""
    path = app_db_path or get_app_db_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    with conn:
        conn.execute(_CREATE_CASES)
    conn.close()


@contextmanager
def get_app_conn():
    """Yields a writable sqlite3.Connection to app.db."""
    path = get_app_db_path()
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()
