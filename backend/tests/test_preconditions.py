"""
Tests for backend/db/preconditions.py.

Happy-path tests against the real pilot.db skip if data/pilot.db is absent.
Failure-mode tests use pytest tmp_path fixtures and always run.
"""

import sqlite3
from pathlib import Path

import pytest

from backend.db.preconditions import (
    check_preconditions,
    PreconditionError,
    DATA_COMPLETION_ADDENDUM_REF,
)

PILOT_DB_PATH = Path("data/pilot.db")


# ── Happy path (real pilot.db) ───────────────────────────────────────────────

def test_preconditions_pass_with_real_pilot_db():
    if not PILOT_DB_PATH.exists():
        pytest.skip("pilot.db not present — copy snapshot to data/pilot.db first")
    counts = check_preconditions(PILOT_DB_PATH)
    assert counts["sources"] >= 1
    assert counts["nsa_rules"] >= 1
    assert counts["ambulance_fee_schedule"] >= 1


def test_preconditions_return_expected_counts():
    if not PILOT_DB_PATH.exists():
        pytest.skip("pilot.db not present")
    counts = check_preconditions(PILOT_DB_PATH)
    assert counts["sources"] == 19
    assert counts["nsa_rules"] == 59
    assert counts["ambulance_fee_schedule"] == 520


# ── Failure: missing file ────────────────────────────────────────────────────

def test_missing_file_raises_precondition_error(tmp_path):
    with pytest.raises(PreconditionError) as exc:
        check_preconditions(tmp_path / "nonexistent.db")
    assert "not found" in str(exc.value).lower()
    assert DATA_COMPLETION_ADDENDUM_REF in str(exc.value)


# ── Failure: missing table ───────────────────────────────────────────────────

def test_missing_table_raises_error_with_table_name(tmp_path):
    db_path = tmp_path / "partial.db"
    conn = sqlite3.connect(db_path)
    conn.execute("CREATE TABLE sources (source_id TEXT)")
    conn.execute("INSERT INTO sources VALUES ('x')")
    conn.commit()
    conn.close()

    with pytest.raises(PreconditionError) as exc:
        check_preconditions(db_path)
    msg = str(exc.value)
    assert "nsa_rules" in msg
    assert "MISSING" in msg
    assert DATA_COMPLETION_ADDENDUM_REF in msg


# ── Failure: empty table ─────────────────────────────────────────────────────

def test_empty_table_raises_error(tmp_path):
    db_path = tmp_path / "empty_tables.db"
    conn = sqlite3.connect(db_path)
    for tbl in ("sources", "nsa_rules", "ambulance_fee_schedule"):
        conn.execute(f"CREATE TABLE {tbl} (id TEXT)")
    conn.commit()
    conn.close()

    with pytest.raises(PreconditionError) as exc:
        check_preconditions(db_path)
    msg = str(exc.value)
    assert "EMPTY" in msg
    assert DATA_COMPLETION_ADDENDUM_REF in msg


# ── Addendum ref present in all failure paths ────────────────────────────────

def test_error_message_always_has_addendum_ref(tmp_path):
    with pytest.raises(PreconditionError) as exc:
        check_preconditions(tmp_path / "no.db")
    assert DATA_COMPLETION_ADDENDUM_REF in str(exc.value)

    db_path = tmp_path / "bare.db"
    conn = sqlite3.connect(db_path)
    conn.execute("CREATE TABLE sources (id TEXT)")
    conn.commit()
    conn.close()
    with pytest.raises(PreconditionError) as exc:
        check_preconditions(db_path)
    assert DATA_COMPLETION_ADDENDUM_REF in str(exc.value)
