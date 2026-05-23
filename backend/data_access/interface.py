"""
Data-access module — Phase 0 stubs.

This is the ONLY SQL layer. Workflows and the rule engine never run SQL directly;
they call these functions. Phase 0 stubs raise NotImplementedError.
Phase 1 replaces each stub with a real SQLite implementation against pilot.db.

Function signatures are the authoritative interface contract for Phase 1.
"""


def lookup_code(code_type: str, code: str) -> dict | None:
    """
    Look up a medical code in Family A (codes table).

    Args:
        code_type: e.g. "ICD10CM", "HCPCS", "revenue", "CARC", "RARC"
        code:      the code string as read from the bill/EOB

    Returns:
        dict with at minimum {code, code_type, description, source_id}, or None if not found.
        CPT codes return a category-level fallback only (PRD §10 — AMA license boundary).
    """
    raise NotImplementedError("lookup_code — implement in Phase 1")


def search_plan(query: str, state: str | None = None) -> list[dict]:
    """
    Search for a health plan by name, issuer, or HIOS ID (Family B).

    Args:
        query: free-text or ID fragment
        state: optional two-letter state code to narrow results

    Returns:
        List of matching plan dicts (may be empty).
    """
    raise NotImplementedError("search_plan — implement in Phase 1")


def get_sbc_fields(plan_id: str) -> dict | None:
    """
    Retrieve Summary of Benefits and Coverage fields for a plan (Family F).

    Returns:
        dict of SBC field values, or None if not found.
        Falls back to plan_attributes (Family B) when SBC fields are absent (~2,326 of ~5,290 plans have SBC data).
    """
    raise NotImplementedError("get_sbc_fields — implement in Phase 1")


def get_ambulance_reference_rate(
    hcpcs: str,
    state: str,
    geo_level: str = "state",
) -> dict | None:
    """
    Get the Medicare reference rate for a ground ambulance HCPCS code.

    reference_rate is stored as integer cents in ambulance_fee_schedule.
    Returns {hcpcs, geo_level, geo_key, reference_rate_cents, reference_rate_dollars,
             effective_year, source_id}, or None if no matching rate found.
    """
    raise NotImplementedError("get_ambulance_reference_rate — implement in Phase 1")


def get_nsa_rules(categories: list[str]) -> list[dict]:
    """
    Retrieve NSA rules for the given category list (e.g. ["A", "B", "K"]).

    Returns rows from nsa_rules ordered by category then rule_id.
    Only returns rows regardless of status; callers must respect the
    counsel_approved gate before surfacing definitive UI determinations (PRD §6.7).
    """
    raise NotImplementedError("get_nsa_rules — implement in Phase 1")


def resolve_source(source_id: str) -> dict | None:
    """
    Resolve a source_id to its full citation record from the sources table.

    Returns {source_id, publisher, canonical_url, license, refresh_cadence, notes},
    or None if source_id not found.
    """
    raise NotImplementedError("resolve_source — implement in Phase 1")
