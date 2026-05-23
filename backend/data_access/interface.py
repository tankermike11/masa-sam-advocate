"""
Data-access module — the ONLY SQL layer.

Workflows and the rule engine never run SQL directly; they call these functions.
All reads go through get_pilot_conn() (read-only). No SQL outside this file.

CPT data limitation (PRD §10): CPT codes are AMA-licensed and not in pilot.db.
lookup_code() detects CPT code_type and returns a category-level fallback dict.
"""

from backend.db.pilot import get_pilot_conn


def lookup_code(code_type: str, code: str) -> dict | None:
    """
    Look up a medical code in Family A (codes table).

    Returns dict with {code, code_type, description, short_description, source_id},
    or None if not found.
    CPT codes return a fallback dict with a "fallback" key (AMA license boundary).
    """
    if code_type.upper() == "CPT":
        return {
            "code": code,
            "code_type": "CPT",
            "description": None,
            "short_description": None,
            "fallback": (
                "CPT codes are AMA-licensed and not available in this system. "
                "Category-level information only."
            ),
            "source_id": "a04_cpt_handling",
        }

    with get_pilot_conn() as conn:
        row = conn.execute(
            "SELECT code_type, code, description, short_description, source_id "
            "FROM codes WHERE code_type = ? AND code = ? LIMIT 1",
            (code_type, code),
        ).fetchone()

    return dict(row) if row else None


def search_plan(query: str, state: str | None = None) -> list[dict]:
    """
    Search for a health plan by name, issuer, or HIOS ID (Family B).

    Returns up to 20 matching plan dicts ordered by plan_year DESC.
    """
    like_q = f"%{query}%"
    with get_pilot_conn() as conn:
        rows = conn.execute(
            "SELECT plan_id, plan_name, issuer_id, issuer_name, state, "
            "       metal_level, plan_year, plan_type "
            "FROM plans "
            "WHERE (plan_id LIKE ? OR plan_name LIKE ? OR issuer_name LIKE ?) "
            "  AND (? IS NULL OR state = ?) "
            "ORDER BY plan_year DESC "
            "LIMIT 20",
            (like_q, like_q, like_q, state, state),
        ).fetchall()
    return [dict(r) for r in rows]


def get_sbc_fields(plan_id: str) -> dict | None:
    """
    Retrieve benefit fields for a plan.

    Tries SBC (Family F) first; falls back to plan_attributes (Family B).
    Returns a dict keyed by field name. The "_source" key indicates which
    table was used ("sbc" or "plan_attributes"). Returns None if no data found.
    """
    with get_pilot_conn() as conn:
        # Try SBC first (~2,326 of 5,290 plans have SBC data)
        sbc_rows = conn.execute(
            "SELECT sf.field_name, sf.field_value, sf.confidence "
            "FROM sbc_documents sd "
            "JOIN sbc_fields sf ON sf.sbc_document_id = sd.id "
            "WHERE sd.plan_id = ? "
            "ORDER BY sf.field_name",
            (plan_id,),
        ).fetchall()

        if sbc_rows:
            return {
                "_source": "sbc",
                **{
                    r["field_name"]: {
                        "value": r["field_value"],
                        "confidence": r["confidence"],
                    }
                    for r in sbc_rows
                },
            }

        # Fallback: plan_attributes (more complete for deductible/OOP)
        attr_rows = conn.execute(
            "SELECT attribute_name, attribute_value "
            "FROM plan_attributes WHERE plan_id = ?",
            (plan_id,),
        ).fetchall()

        if attr_rows:
            return {
                "_source": "plan_attributes",
                **{r["attribute_name"]: r["attribute_value"] for r in attr_rows},
            }

    return None


def get_ambulance_reference_rate(
    hcpcs: str,
    state: str,
    geo_level: str = "state",
) -> dict | None:
    """
    Get the Medicare reference rate for a ground ambulance HCPCS code.

    reference_rate is stored as integer cents; this function adds
    reference_rate_dollars = reference_rate / 100 to the returned dict.
    Returns None if no matching rate found.
    """
    with get_pilot_conn() as conn:
        row = conn.execute(
            "SELECT hcpcs, geo_level, geo_key, reference_rate, effective_year, source_id "
            "FROM ambulance_fee_schedule "
            "WHERE hcpcs = ? AND geo_level = ? AND geo_key = ? "
            "ORDER BY effective_year DESC LIMIT 1",
            (hcpcs, geo_level, state.upper()),
        ).fetchone()

    if row is None:
        return None

    result = dict(row)
    result["reference_rate_dollars"] = result["reference_rate"] / 100
    return result


def get_nsa_rules(categories: list[str]) -> list[dict]:
    """
    Retrieve NSA rules for the given category list (e.g. ["A", "B", "K"]).

    Returns all matching rows ordered by category ASC, rule_id ASC.
    Callers must check status == "counsel_approved" before surfacing
    definitive UI determinations (PRD §6.7). All 59 rules are currently
    status="draft" (awaiting counsel review).
    """
    if not categories:
        return []

    placeholders = ",".join("?" * len(categories))
    with get_pilot_conn() as conn:
        rows = conn.execute(
            f"SELECT * FROM nsa_rules "  # noqa: S608
            f"WHERE category IN ({placeholders}) "
            f"ORDER BY category ASC, rule_id ASC",
            categories,
        ).fetchall()

    return [dict(r) for r in rows]


def search_codes(query: str, code_type: str | None = None, limit: int = 10) -> list[dict]:
    """
    Search codes by code string or description fragment.

    Used by the frontend code-search widget (PRD §5.2). Covers all 11 code types.
    CPT code_type returns the fallback sentinel immediately without a DB query.
    """
    if code_type and code_type.upper() == "CPT":
        return [{
            "code": query,
            "code_type": "CPT",
            "description": None,
            "short_description": None,
            "fallback": "CPT codes are AMA-licensed and not available in this system.",
            "source_id": "a04_cpt_handling",
        }]

    like_q = f"%{query}%"
    with get_pilot_conn() as conn:
        if code_type:
            rows = conn.execute(
                "SELECT code_type, code, description, short_description, source_id "
                "FROM codes "
                "WHERE code_type = ? AND (code LIKE ? OR description LIKE ?) "
                "AND is_header = 0 "
                "LIMIT ?",
                (code_type, like_q, like_q, limit),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT code_type, code, description, short_description, source_id "
                "FROM codes "
                "WHERE (code LIKE ? OR description LIKE ?) "
                "AND is_header = 0 AND code_type != 'CPT_SENTINEL' "
                "LIMIT ?",
                (like_q, like_q, limit),
            ).fetchall()

    return [dict(r) for r in rows]


def resolve_source(source_id: str) -> dict | None:
    """
    Resolve a source_id to its full citation record.

    Returns {source_id, publisher, canonical_url, license, refresh_cadence, notes}
    or None if source_id not found.
    """
    with get_pilot_conn() as conn:
        row = conn.execute(
            "SELECT source_id, publisher, canonical_url, license, refresh_cadence, notes "
            "FROM sources WHERE source_id = ?",
            (source_id,),
        ).fetchone()

    return dict(row) if row else None
