"""
Escalation endpoints (PRD §8, §9).

POST /cases/{case_id}/escalate  — trigger escalation (member or engine)
GET  /cases/queue               — read-only advocate queue (escalated cases only)
GET  /cases/{case_id}           — full case detail for advocate view

IMPORTANT: /cases/queue must be declared before /cases/{case_id} so FastAPI
matches the literal path before the parameterised one.
"""

from __future__ import annotations

import json
import logging

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.db.app_db import get_app_conn
from backend.escalation.service import (
    CaseNotFoundError,
    EscalationResult,
    GateDecision,
    request_escalation,
)
from backend.intake.schema import IntakeSubmission
from backend.triage.engine import TriageResult

logger = logging.getLogger(__name__)
router = APIRouter()


# ── Request / response models ─────────────────────────────────────────────────

class EscalationRequest(BaseModel):
    trigger: str = "member_initiated"  # "member_initiated" | "engine_recommended"


class EscalationResponse(BaseModel):
    case_id: str
    escalation_status: str
    gate_decision: GateDecision
    message: str


class CaseSummary(BaseModel):
    case_id: str
    created_at: str
    escalation_status: str
    severity: str
    problem_type: str
    insurance_situation: str
    advocacy_capacity: str
    dollar_at_stake: float | None
    escalation_reasons: list[str]
    gate_decision: dict | None
    workflow_outputs_present: list[str]


class QueueResponse(BaseModel):
    cases: list[CaseSummary]
    total: int


class CaseDetail(BaseModel):
    case_id: str
    created_at: str
    escalation_status: str
    gate_decision: dict | None
    intake: dict
    triage_result: dict
    workflow_outputs: dict
    generated_documents: dict


# ── Helpers ───────────────────────────────────────────────────────────────────

def _fetch_case(case_id: str) -> dict:
    with get_app_conn() as conn:
        row = conn.execute(
            "SELECT case_id, created_at, intake, triage_result, "
            "workflow_outputs, generated_documents, escalation_status, gate_decision "
            "FROM cases WHERE case_id = ?",
            (case_id,),
        ).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail=f"Case {case_id!r} not found.")
    return dict(row)


def _safe_json(value: str | None) -> dict:
    if not value:
        return {}
    try:
        return json.loads(value)
    except (json.JSONDecodeError, TypeError):
        return {}


def _extract_dollar_at_stake(workflow_outputs_json: str | None) -> float | None:
    outputs = _safe_json(workflow_outputs_json)
    for wf_data in outputs.values():
        if isinstance(wf_data, dict) and wf_data.get("dollar_at_stake") is not None:
            try:
                return float(wf_data["dollar_at_stake"])
            except (TypeError, ValueError):
                pass
    return None


def _build_summary(row: dict) -> CaseSummary:
    triage = _safe_json(row.get("triage_result"))
    gate = _safe_json(row.get("gate_decision")) or None
    outputs = _safe_json(row.get("workflow_outputs"))

    return CaseSummary(
        case_id=row["case_id"],
        created_at=row["created_at"],
        escalation_status=row["escalation_status"],
        severity=triage.get("severity", "unknown"),
        problem_type=triage.get("problem_type", "unknown"),
        insurance_situation=triage.get("insurance_situation", "unknown"),
        advocacy_capacity=triage.get("advocacy_capacity", "unknown"),
        dollar_at_stake=_extract_dollar_at_stake(row.get("workflow_outputs")),
        escalation_reasons=triage.get("escalation_reasons", []),
        gate_decision=gate,
        workflow_outputs_present=list(outputs.keys()),
    )


# ── Endpoints — queue MUST come before {case_id} ─────────────────────────────

@router.get("/cases/queue", response_model=QueueResponse)
def get_queue() -> QueueResponse:
    """
    Advocate queue — read-only list of escalated cases (§8.3).
    Returns cases where escalation_status in ('recommended', 'requested', 'in_queue').
    """
    with get_app_conn() as conn:
        rows = conn.execute(
            "SELECT case_id, created_at, intake, triage_result, "
            "workflow_outputs, generated_documents, escalation_status, gate_decision "
            "FROM cases "
            "WHERE escalation_status IN ('recommended', 'requested', 'in_queue') "
            "ORDER BY created_at DESC",
        ).fetchall()

    summaries = [_build_summary(dict(r)) for r in rows]
    return QueueResponse(cases=summaries, total=len(summaries))


@router.post("/cases/{case_id}/escalate", response_model=EscalationResponse)
def escalate_case(case_id: str, body: EscalationRequest) -> EscalationResponse:
    """
    Trigger escalation for a case (PRD §8.1).

    Member-initiated (trigger="member_initiated") → status becomes "requested".
    Engine-recommended (trigger="engine_recommended") → status becomes "recommended".
    The engine recommends; it never forces. The member always decides.
    """
    case = _fetch_case(case_id)   # raises 404 if not found

    try:
        result: EscalationResult = request_escalation(
            case_id=case_id,
            trigger=body.trigger,
            intake_json=case["intake"],
        )
    except CaseNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    return EscalationResponse(
        case_id=result.case_id,
        escalation_status=result.escalation_status,
        gate_decision=result.gate_decision,
        message=result.gate_decision.message,
    )


@router.get("/cases/{case_id}", response_model=CaseDetail)
def get_case(case_id: str) -> CaseDetail:
    """Full case detail for the advocate view (§8.3)."""
    row = _fetch_case(case_id)
    return CaseDetail(
        case_id=row["case_id"],
        created_at=row["created_at"],
        escalation_status=row["escalation_status"],
        gate_decision=_safe_json(row.get("gate_decision")) or None,
        intake=_safe_json(row.get("intake")),
        triage_result=_safe_json(row.get("triage_result")),
        workflow_outputs=_safe_json(row.get("workflow_outputs")),
        generated_documents=_safe_json(row.get("generated_documents")),
    )
