"""Workflow 5 catch-all light route test fixtures."""

WORKFLOW5_FIXTURES: list[tuple[dict, dict]] = [
    # 1 — Medicaid: state routing
    (
        {
            "insurance_situation": "medicaid",
            "state": "FL",
            "problem_type": "billing_error",
        },
        {
            "medicaid_in_found": True,
            "state_in_next_step": True,
            "escalation": "suggested",
        },
    ),
    # 2 — Generic catch-all: non-Medicaid, non-deep-workflow case
    (
        {
            "insurance_situation": "commercial_employer",
            "state": "TX",
            "problem_type": "billing_error",
        },
        {
            "next_step_non_empty": True,
            "escalation": "suggested",
        },
    ),
    # 3 — Medicaid with codes: codes decoded + Medicaid routing
    (
        {
            "insurance_situation": "medicaid",
            "state": "CA",
            "problem_type": "billing_error",
            "codes_present": [{"code_type": "ICD10CM", "code": "A00"}],
        },
        {
            "medicaid_in_found": True,
            "code_in_found": "A00",
            "escalation": "suggested",
        },
    ),
]
