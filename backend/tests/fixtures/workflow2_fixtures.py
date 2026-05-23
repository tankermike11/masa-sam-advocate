"""Workflow 2 test fixtures."""

_BASE = {
    "insurance_situation": "commercial_employer",
    "state": "FL",
    "problem_type": "surprise_out_of_network",
}

WORKFLOW2_FIXTURES: list[tuple[dict, dict]] = [
    # 1 — Ground ambulance: federal gap explanation
    (
        {**_BASE, "ambulance_involved": True, "ambulance_type": "ground"},
        {"federal_gap_in_found": True, "escalation": "suggested"},
    ),
    # 2 — Air ambulance: NSA engine path (not ground node)
    (
        {**_BASE, "ambulance_involved": True, "ambulance_type": "air"},
        {"escalation": "suggested", "no_federal_gap_in_found": True},
    ),
    # 3 — Ground + reference rate (FL state, A0425 HCPCS from codes_present)
    (
        {
            **_BASE,
            "ambulance_involved": True,
            "ambulance_type": "ground",
            "codes_present": [{"code_type": "HCPCS", "code": "A0425"}],
            "amount_billed": 1800.0,
        },
        {"reference_rate_in_found": True, "escalation": "suggested"},
    ),
    # 4 — Ground + invalid state: no crash, noted in what_needs_verification
    (
        {
            **_BASE,
            "state": "XX",
            "ambulance_involved": True,
            "ambulance_type": "ground",
        },
        {"rate_missing_in_verification": True, "no_crash": True},
    ),
    # 5 — Ground + MASA member: MASA routing in recommended_next_step
    (
        {
            **_BASE,
            "ambulance_involved": True,
            "ambulance_type": "ground",
            "is_masa_member": True,
        },
        {"masa_in_next_step": True},
    ),
    # 6 — Ground + catastrophic severity: hardship options in interpretation
    (
        {
            **_BASE,
            "ambulance_involved": True,
            "ambulance_type": "ground",
            "amount_patient_responsibility": 30000.0,
        },
        {"hardship_in_interpretation": True},
    ),
    # 7 — Ground + self-pay + GFE received: PPDR mention
    (
        {
            **_BASE,
            "insurance_situation": "uninsured_self_pay",
            "ambulance_involved": True,
            "ambulance_type": "ground",
            "gfe_received": True,
        },
        {"ppdr_in_found": True},
    ),
    # 8 — Non-ambulance surprise bill: NSA engine path
    (
        {**_BASE},
        {"escalation": "suggested"},
    ),
]
