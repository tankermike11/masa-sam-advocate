"""
GET /health — live precondition probe.

Re-runs check_preconditions() on every request so the endpoint reflects
the live state of pilot.db, not a startup snapshot.
"""

from fastapi import APIRouter
from pydantic import BaseModel

from backend.db.preconditions import check_preconditions
from backend.db.pilot import get_pilot_db_path
from backend.db.app_db import get_app_db_path

router = APIRouter()


class PreconditionCounts(BaseModel):
    sources: int
    nsa_rules: int
    ambulance_fee_schedule: int


class HealthResponse(BaseModel):
    status: str
    version: str
    pilot_db_path: str
    app_db_path: str
    precondition_tables: PreconditionCounts


@router.get("/health", response_model=HealthResponse)
def health_check():
    counts = check_preconditions(get_pilot_db_path())
    return HealthResponse(
        status="ok",
        version="0.1.0",
        pilot_db_path=str(get_pilot_db_path()),
        app_db_path=str(get_app_db_path()),
        precondition_tables=PreconditionCounts(
            sources=counts["sources"],
            nsa_rules=counts["nsa_rules"],
            ambulance_fee_schedule=counts["ambulance_fee_schedule"],
        ),
    )
