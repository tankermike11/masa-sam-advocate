"""GET /codes/search — code autocomplete for the frontend intake widget (PRD §5.2)."""

from fastapi import APIRouter, Query
from backend.data_access.interface import search_codes

router = APIRouter()


@router.get("/codes/search")
def search_codes_endpoint(
    q: str = Query(..., min_length=1, description="Code string or description fragment"),
    code_type: str | None = Query(None, description="Filter by code type (e.g. ICD10CM, HCPCS)"),
    limit: int = Query(10, ge=1, le=50),
) -> list[dict]:
    return search_codes(query=q, code_type=code_type, limit=limit)
