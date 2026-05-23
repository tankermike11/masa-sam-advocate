"""Workflow 4 collections microflow test fixtures."""

WORKFLOW4_FIXTURES: list[tuple[dict, dict]] = [
    # 1 — In collections: full output
    (
        {
            "insurance_situation": "commercial_employer",
            "state": "FL",
            "problem_type": "collections_credit_impact",
            "in_collections": True,
            "amount_patient_responsibility": 1200.0,
        },
        {
            "fdcpa_in_found": True,
            "cfpb_in_found": True,
            "debt_letter_in_found": True,
            "escalation": "suggested",
        },
    ),
    # 2 — Not in collections: still returns FDCPA guidance, no crash
    (
        {
            "insurance_situation": "commercial_employer",
            "state": "TX",
            "problem_type": "collections_credit_impact",
        },
        {
            "fdcpa_in_found": True,
            "escalation": "suggested",
        },
    ),
    # 3 — Reported to credit: credit bureau note added
    (
        {
            "insurance_situation": "commercial_employer",
            "state": "CA",
            "problem_type": "collections_credit_impact",
            "reported_to_credit": True,
        },
        {
            "credit_mention_in_found": True,
            "escalation": "suggested",
        },
    ),
]
