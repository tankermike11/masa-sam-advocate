"""
NSA rule engine test fixtures.

Each entry: (intake_kwargs, rule_modules, expected) where expected may contain:
  rule_ids_include   — each rule_id must appear in matched_rules
  escalation_recommendation — exact match
  has_counsel_approved_rules — exact match
  protection_determination — exact match
"""

_BASE = {
    "insurance_situation": "commercial_employer",
    "state": "FL",
    "problem_type": "surprise_out_of_network",
}

NSA_FIXTURES: list[tuple[dict, list[str], dict]] = [
    # 1 — Ground ambulance: GROUND-001/003/009 fire for category K
    (
        {**_BASE, "ambulance_involved": True, "ambulance_type": "ground"},
        ["K"],
        {
            "rule_ids_include": ["GROUND-001", "GROUND-003", "GROUND-009"],
            "escalation_recommendation": "suggested",
            "has_counsel_approved_rules": False,
            "protection_determination": "human_review_required",
        },
    ),
    # 2 — Air ambulance: NSA-AIR-001/004 fire for category G
    (
        {**_BASE, "ambulance_involved": True, "ambulance_type": "air"},
        ["G"],
        {
            "rule_ids_include": ["NSA-AIR-001", "NSA-AIR-004"],
            "escalation_recommendation": "suggested",
            "has_counsel_approved_rules": False,
        },
    ),
    # 3 — Emergency + OON: B rules fire
    (
        {
            **_BASE,
            "service_type": "emergency",
            "provider_network_status": "out_of_network",
            "denial_present": True,
        },
        ["A", "B"],
        {
            "rule_ids_include": ["NSA-EMERG-001", "NSA-EMERG-002"],
            "escalation_recommendation": "suggested",
        },
    ),
    # 4 — Notice consent claimed: D rules fire
    (
        {**_BASE, "notice_consent_claimed": True},
        ["D"],
        {
            "rule_ids_include": ["NSA-CONSENT-001"],
            "escalation_recommendation": "suggested",
        },
    ),
    # 5 — Self-pay: GFE-001 fires for category H
    (
        {**_BASE, "insurance_situation": "uninsured_self_pay"},
        ["H"],
        {
            "rule_ids_include": ["GFE-001"],
            "escalation_recommendation": "suggested",
        },
    ),
    # 6 — Self-funded ERISA: STATE-ROUTE-002 fires
    (
        {**_BASE, "plan_funding_type": "self_funded_erisa"},
        ["J"],
        {
            "rule_ids_include": ["STATE-ROUTE-002"],
            "escalation_recommendation": "suggested",
        },
    ),
    # 7 — Empty rule_modules: no matches, no escalation from rules
    (
        _BASE,
        [],
        {
            "escalation_recommendation": "none",
            "has_counsel_approved_rules": False,
        },
    ),
    # 8 — Non-emergency OON at in-network facility: NONEMERG-001 fires
    (
        {
            **_BASE,
            "facility_network_status": "in_network",
            "provider_network_status": "out_of_network",
            "service_type": "non_emergency",
        },
        ["C"],
        {
            "rule_ids_include": ["NSA-NONEMERG-001"],
            "escalation_recommendation": "suggested",
        },
    ),
]
