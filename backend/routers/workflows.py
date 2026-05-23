"""
Workflow endpoints — POST /cases/{case_id}/workflow1 and /workflow2.

Each endpoint:
  1. Fetches the existing case from app.db (404 if not found)
  2. Deserializes the stored intake and triage_result
  3. Runs the appropriate workflow
  4. Updates the case's workflow_outputs in app.db
  5. Returns the AnswerCard
"""

from __future__ import annotations

import json
import logging

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.db.app_db import get_app_conn
from backend.intake.schema import IntakeSubmission
from backend.triage.engine import TriageResult
from backend.workflows.answer_card import AnswerCard
from backend.workflows.workflow1 import run_workflow1
from backend.workflows.workflow2 import run_workflow2

logger = logging.getLogger(__name__)
router = APIRouter()


class WorkflowResponse(BaseModel):
    case_id: str
    workflow: str
    answer_card: AnswerCard


def _fetch_case(case_id: str) -> dict:
    """Return the case row dict, or raise 404."""
    with get_app_conn() as conn:
        row = conn.execute(
            "SELECT case_id, intake, triage_result, workflow_outputs "
            "FROM cases WHERE case_id = ?",
            (case_id,),
        ).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail=f"Case {case_id!r} not found.")
    return dict(row)


def _update_workflow_outputs(case_id: str, workflow_name: str, card: AnswerCard) -> None:
    """Append / overwrite the workflow entry in cases.workflow_outputs."""
    with get_app_conn() as conn:
        row = conn.execute(
            "SELECT workflow_outputs FROM cases WHERE case_id = ?", (case_id,)
        ).fetchone()
        existing: dict = {}
        if row and row["workflow_outputs"]:
            try:
                existing = json.loads(row["workflow_outputs"])
            except (json.JSONDecodeError, TypeError):
                existing = {}
        existing[workflow_name] = json.loads(card.model_dump_json())
        conn.execute(
            "UPDATE cases SET workflow_outputs = ? WHERE case_id = ?",
            (json.dumps(existing), case_id),
        )
        conn.commit()


@router.post("/cases/{case_id}/workflow1", response_model=WorkflowResponse)
def run_workflow_1(case_id: str) -> WorkflowResponse:
    case = _fetch_case(case_id)
    try:
        intake = IntakeSubmission.model_validate_json(case["intake"])
    except Exception as exc:
        logger.error("Failed to parse intake for case %r: %s", case_id, exc)
        raise HTTPException(status_code=422, detail="Stored intake is invalid.") from exc

    card = run_workflow1(intake)
    _update_workflow_outputs(case_id, "workflow_1", card)
    return WorkflowResponse(case_id=case_id, workflow="workflow_1", answer_card=card)


@router.post("/cases/{case_id}/workflow2", response_model=WorkflowResponse)
def run_workflow_2(case_id: str) -> WorkflowResponse:
    case = _fetch_case(case_id)
    try:
        intake = IntakeSubmission.model_validate_json(case["intake"])
        triage_result = TriageResult.model_validate_json(case["triage_result"])
    except Exception as exc:
        logger.error("Failed to parse case data for %r: %s", case_id, exc)
        raise HTTPException(status_code=422, detail="Stored case data is invalid.") from exc

    card = run_workflow2(intake, triage_result)
    _update_workflow_outputs(case_id, "workflow_2", card)
    return WorkflowResponse(case_id=case_id, workflow="workflow_2", answer_card=card)
