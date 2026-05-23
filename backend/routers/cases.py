"""
POST /cases — validate intake, run triage, persist case to app.db.
"""

from datetime import datetime, timezone
from uuid import uuid4

from fastapi import APIRouter
from pydantic import BaseModel

from backend.db.app_db import get_app_conn
from backend.intake.schema import IntakeSubmission
from backend.triage.engine import TriageResult, triage

router = APIRouter()


class CaseResponse(BaseModel):
    case_id: str
    created_at: str
    triage_result: TriageResult


@router.post("/cases", response_model=CaseResponse, status_code=201)
def create_case(intake: IntakeSubmission) -> CaseResponse:
    case_id = str(uuid4())
    created_at = datetime.now(timezone.utc).isoformat()
    result = triage(intake)

    with get_app_conn() as conn:
        conn.execute(
            "INSERT INTO cases "
            "(case_id, created_at, intake, triage_result, escalation_status) "
            "VALUES (?, ?, ?, ?, ?)",
            (
                case_id,
                created_at,
                intake.model_dump_json(),
                result.model_dump_json(),
                "none",
            ),
        )
        conn.commit()

    return CaseResponse(case_id=case_id, created_at=created_at, triage_result=result)
