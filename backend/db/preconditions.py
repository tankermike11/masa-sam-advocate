"""
Precondition check for pilot.db.

Verifies that the three tables required by Phase 1+ are present and non-empty.
Raises PreconditionError with a message pointing to the Data Completion Addendum
if any check fails.

Used in:
  - backend/main.py lifespan event (blocks server startup on failure)
  - backend/routers/health.py (live re-check on every /health request)
  - backend/tests/test_preconditions.py (unit-tested with tmp_path fixtures)
"""

import sqlite3
from pathlib import Path

DATA_COMPLETION_ADDENDUM_REF = (
    "MASA Public Data Ingestion Layer — Data Completion Addendum v1.3 "
    "(repository: medical_billing_data)"
)

REQUIRED_TABLES = [
    {"name": "sources",                "min_rows": 1, "expected": 19},
    {"name": "nsa_rules",              "min_rows": 1, "expected": 59},
    {"name": "ambulance_fee_schedule", "min_rows": 1, "expected": 520},
]


class PreconditionError(RuntimeError):
    """Raised when pilot.db preconditions are not met."""
    pass


def check_preconditions(pilot_db_path: Path) -> dict:
    """
    Check all precondition tables in pilot.db.

    Returns {table_name: row_count} on success.
    Raises PreconditionError on any failure; every error message includes
    the DATA_COMPLETION_ADDENDUM_REF and a concrete remediation action.
    """
    if not pilot_db_path.exists():
        raise PreconditionError(
            f"pilot.db not found at {pilot_db_path}.\n"
            f"Copy the finished pilot.db snapshot to data/pilot.db before starting.\n"
            f"This file is built by: {DATA_COMPLETION_ADDENDUM_REF}"
        )

    try:
        conn = sqlite3.connect(f"file:{pilot_db_path}?mode=ro", uri=True)
    except sqlite3.OperationalError as e:
        raise PreconditionError(
            f"Cannot open pilot.db at {pilot_db_path} (read-only mode): {e}\n"
            f"Refer to: {DATA_COMPLETION_ADDENDUM_REF}"
        ) from e

    counts: dict[str, int] = {}
    failures: list[str] = []

    with conn:
        cur = conn.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
        existing_tables = {row[0] for row in cur.fetchall()}

        for spec in REQUIRED_TABLES:
            name = spec["name"]
            if name not in existing_tables:
                failures.append(f"  Table '{name}' is MISSING from pilot.db.")
                continue

            cur.execute(f"SELECT COUNT(*) FROM {name}")  # noqa: S608
            count = cur.fetchone()[0]
            counts[name] = count

            if count < spec["min_rows"]:
                failures.append(
                    f"  Table '{name}' is EMPTY (0 rows). Expected ~{spec['expected']} rows."
                )

    conn.close()

    if failures:
        lines = "\n".join(failures)
        raise PreconditionError(
            f"STARTUP BLOCKED — pilot.db preconditions not met:\n"
            f"{lines}\n\n"
            f"ACTION REQUIRED: Run the data-preparation tasks in:\n"
            f"  {DATA_COMPLETION_ADDENDUM_REF}\n"
            f"Then copy the resulting pilot.db snapshot to data/pilot.db and restart."
        )

    return counts
