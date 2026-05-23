"""Workflow 1 test fixtures."""

_BASE = {
    "insurance_situation": "commercial_employer",
    "state": "FL",
    "problem_type": "billing_error",
}

WORKFLOW1_FIXTURES: list[tuple[dict, dict]] = [
    # 1 — ICD10CM code decodes correctly
    (
        {**_BASE, "codes_present": [{"code_type": "ICD10CM", "code": "A00"}]},
        {"code_in_found": "A00", "source_cited": True},
    ),
    # 2 — CPT code returns fallback (no crash, noted in what_needs_verification)
    (
        {**_BASE, "codes_present": [{"code_type": "CPT", "code": "99213"}]},
        {"cpt_in_needs_verification": True, "no_crash": True},
    ),
    # 3 — Unknown code noted in what_needs_verification, workflow completes
    (
        {**_BASE, "codes_present": [{"code_type": "ICD10CM", "code": "ZZZZZZZ"}]},
        {"unknown_in_needs_verification": True, "no_crash": True},
    ),
    # 4 — No codes: workflow still returns valid AnswerCard
    (
        {**_BASE},
        {"answer_card_valid": True},
    ),
    # 5 — Complete dollar amounts appear in what_we_found
    (
        {
            **_BASE,
            "amount_billed": 1500.0,
            "amount_allowed": 1200.0,
            "amount_plan_paid": 960.0,
            "amount_patient_responsibility": 240.0,
        },
        {"dollar_reconciliation_in_found": True, "dollar_at_stake": 240.0},
    ),
    # 6 — All dollar amounts None: noted in what_needs_verification
    (
        {**_BASE},
        {"amounts_none_handled": True},
    ),
]
