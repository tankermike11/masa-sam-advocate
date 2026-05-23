"""
Tests for the escalation service and router endpoints.
Uses a temporary app.db via monkeypatch to avoid touching the real database.
"""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

import pytest

from backend.escalation.service import (
    CaseNotFoundError,
    evaluate_gate,
    request_escalation,
)
from backend.intake.schema import IntakeSubmission
from backend.triage.engine import triage

# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture()
def tmp_db(tmp_path, monkeypatch):
    """Redirect all app.db operations to a fresh temp database."""
    db_path = tmp_path / "test_app.db"
    monkeypatch.setenv("APP_DB_PATH", str(db_path))

    # Import after setting the env var so get_app_db_path() picks it up
    from backend.db.app_db import init_app_db
    init_app_db(db_path)
    return db_path


def _seed_case(
    intake_kwargs: dict,
    workflow_outputs: dict | None = None,
) -> str:
    """Insert a test case into app.db and return its case_id."""
    from backend.db.app_db import get_app_conn

    case_id = str(uuid4())
    intake = IntakeSubmission(**intake_kwargs)
    triage_result = triage(intake)
    created_at = datetime.now(timezone.utc).isoformat()

    with get_app_conn() as conn:
        conn.execute(
            "INSERT INTO cases "
            "(case_id, created_at, intake, triage_result, escalation_status, workflow_outputs) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (
                case_id,
                created_at,
                intake.model_dump_json(),
                triage_result.model_dump_json(),
                "none",
                json.dumps(workflow_outputs) if workflow_outputs else None,
            ),
        )
        conn.commit()
    return case_id


def _get_case_row(case_id: str) -> dict:
    from backend.db.app_db import get_app_conn
    with get_app_conn() as conn:
        row = conn.execute(
            "SELECT * FROM cases WHERE case_id = ?", (case_id,)
        ).fetchone()
    return dict(row) if row else {}


_BASE_INTAKE = {
    "insurance_situation": "commercial_employer",
    "state": "FL",
    "problem_type": "surprise_out_of_network",
}

# ── Gate tests (no DB needed) ─────────────────────────────────────────────────

def test_waived_tier_gate():
    gate = evaluate_gate(True, "Emergency Shield Plus")
    assert gate.fee_applies is False


def test_charged_tier_gate():
    gate = evaluate_gate(True, "Basic")
    assert gate.fee_applies is True


# ── request_escalation — member-initiated ─────────────────────────────────────

def test_member_initiated_sets_requested(tmp_db):
    intake = IntakeSubmission(**{**_BASE_INTAKE, "is_masa_member": True, "masa_plan_tier": "Basic"})
    case_id = _seed_case({**_BASE_INTAKE, "is_masa_member": True, "masa_plan_tier": "Basic"})

    result = request_escalation(case_id, "member_initiated", intake.model_dump_json())

    assert result.escalation_status == "requested"
    row = _get_case_row(case_id)
    assert row["escalation_status"] == "requested"


def test_engine_recommended_sets_recommended(tmp_db):
    case_id = _seed_case({**_BASE_INTAKE, "is_masa_member": False})
    intake = IntakeSubmission(**{**_BASE_INTAKE, "is_masa_member": False})

    result = request_escalation(case_id, "engine_recommended", intake.model_dump_json())

    assert result.escalation_status == "recommended"
    row = _get_case_row(case_id)
    assert row["escalation_status"] == "recommended"


def test_waived_tier_member_gate_decision_stored(tmp_db):
    intake_kwargs = {**_BASE_INTAKE, "is_masa_member": True, "masa_plan_tier": "Lifetime"}
    case_id = _seed_case(intake_kwargs)
    intake = IntakeSubmission(**intake_kwargs)

    result = request_escalation(case_id, "member_initiated", intake.model_dump_json())

    assert result.gate_decision.fee_applies is False
    assert result.gate_decision.tier_matched == "Lifetime"

    row = _get_case_row(case_id)
    stored_gate = json.loads(row["gate_decision"])
    assert stored_gate["fee_applies"] is False
    assert stored_gate["tier_matched"] == "Lifetime"


def test_non_waived_member_gate_decision_stored(tmp_db):
    intake_kwargs = {**_BASE_INTAKE, "is_masa_member": True, "masa_plan_tier": "Standard"}
    case_id = _seed_case(intake_kwargs)
    intake = IntakeSubmission(**intake_kwargs)

    result = request_escalation(case_id, "member_initiated", intake.model_dump_json())

    assert result.gate_decision.fee_applies is True
    row = _get_case_row(case_id)
    stored_gate = json.loads(row["gate_decision"])
    assert stored_gate["fee_applies"] is True


def test_unknown_case_id_raises_case_not_found(tmp_db):
    intake = IntakeSubmission(**_BASE_INTAKE)
    with pytest.raises(CaseNotFoundError):
        request_escalation("nonexistent-case-id", "member_initiated", intake.model_dump_json())


def test_unknown_trigger_raises_value_error(tmp_db):
    case_id = _seed_case(_BASE_INTAKE)
    intake = IntakeSubmission(**_BASE_INTAKE)
    with pytest.raises(ValueError, match="Unknown escalation trigger"):
        request_escalation(case_id, "invalid_trigger", intake.model_dump_json())


def test_full_case_object_complete_after_escalation(tmp_db):
    """Gate: escalation creates a complete case object (PRD §15 Phase 4 gate)."""
    intake_kwargs = {
        **_BASE_INTAKE,
        "is_masa_member": True,
        "masa_plan_tier": "Emergency Shield Plus",
        "amount_billed": 6000.0,
    }
    case_id = _seed_case(intake_kwargs)
    intake = IntakeSubmission(**intake_kwargs)

    request_escalation(case_id, "member_initiated", intake.model_dump_json())

    row = _get_case_row(case_id)
    assert row["case_id"] == case_id
    assert row["created_at"]
    assert row["intake"]         # JSON blob present
    assert row["triage_result"]  # JSON blob present
    assert row["escalation_status"] == "requested"
    assert row["gate_decision"]  # JSON blob present

    gate = json.loads(row["gate_decision"])
    assert "fee_applies" in gate
    assert "message" in gate


# ── Queue endpoint ─────────────────────────────────────────────────────────────

def test_queue_returns_escalated_cases_only(tmp_db):
    from backend.db.app_db import get_app_conn

    # Non-escalated case (should be excluded)
    _seed_case(_BASE_INTAKE)

    # Escalated case (should be included)
    escalated_id = _seed_case({**_BASE_INTAKE, "is_masa_member": True, "masa_plan_tier": "Basic"})
    intake = IntakeSubmission(**{**_BASE_INTAKE, "is_masa_member": True, "masa_plan_tier": "Basic"})
    request_escalation(escalated_id, "member_initiated", intake.model_dump_json())

    # Build queue the same way the router does
    with get_app_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM cases WHERE escalation_status IN ('recommended', 'requested', 'in_queue')"
        ).fetchall()

    assert len(rows) == 1
    assert dict(rows[0])["case_id"] == escalated_id


def test_queue_excludes_none_status(tmp_db):
    _seed_case(_BASE_INTAKE)  # escalation_status = "none"

    from backend.db.app_db import get_app_conn
    with get_app_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM cases WHERE escalation_status IN ('recommended', 'requested', 'in_queue')"
        ).fetchall()

    assert len(rows) == 0


def test_escalation_reasons_stored_in_triage_result(tmp_db):
    """Verify triage_result captures escalation_reasons for queue display."""
    intake_kwargs = {
        **_BASE_INTAKE,
        "amount_patient_responsibility": 30000.0,  # catastrophic → escalation_reasons includes high_dollar_exposure
    }
    case_id = _seed_case(intake_kwargs)
    row = _get_case_row(case_id)
    triage_data = json.loads(row["triage_result"])
    assert triage_data["escalation_recommendation"] == "suggested"
    assert "high_dollar_exposure" in triage_data["escalation_reasons"]
