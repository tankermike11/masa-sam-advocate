"""
Curated triage routing fixtures for the Phase 1 gate.

Each entry: (intake_kwargs, expected) where expected may contain:
  primary_workflow          — exact match required
  rule_modules_include      — each category must appear in result.rule_modules
  rule_modules_exclude      — each category must NOT appear in result.rule_modules
  severity                  — exact match if present
  escalation_recommendation — exact match if present
  escalation_reasons_include — each reason flag must appear in result.escalation_reasons
"""

_BASE = {
    "insurance_situation": "commercial_employer",
    "state": "FL",
    "problem_type": "clean_denial",
}

FIXTURES: list[tuple[dict, dict]] = [
    # 1 — Axis 2 override: medicaid always routes to workflow_5 regardless of problem_type
    (
        {**_BASE, "insurance_situation": "medicaid", "problem_type": "surprise_out_of_network"},
        {"primary_workflow": "workflow_5"},
    ),
    # 2 — Axis 1: commercial + surprise_out_of_network → workflow_2 with NSA categories
    (
        {**_BASE, "problem_type": "surprise_out_of_network"},
        {"primary_workflow": "workflow_2", "rule_modules_include": ["A", "B", "D", "E"]},
    ),
    # 3 — Axis 1: commercial + balance_bill → workflow_2
    (
        {**_BASE, "problem_type": "balance_bill"},
        {"primary_workflow": "workflow_2", "rule_modules_include": ["A", "B"]},
    ),
    # 4 — Axis 1: clean_denial → workflow_1
    (
        {**_BASE, "problem_type": "clean_denial"},
        {"primary_workflow": "workflow_1"},
    ),
    # 5 — Axis 1: billing_error → workflow_1
    (
        {**_BASE, "problem_type": "billing_error"},
        {"primary_workflow": "workflow_1"},
    ),
    # 6 — Axis 1: partial_payment_underpayment → workflow_1
    (
        {**_BASE, "problem_type": "partial_payment_underpayment"},
        {"primary_workflow": "workflow_1"},
    ),
    # 7 — Axis 1: collections_credit_impact → workflow_4
    (
        {**_BASE, "problem_type": "collections_credit_impact"},
        {"primary_workflow": "workflow_4"},
    ),
    # 8 — medicare_only proceeds through Axis 1 (NOT an Axis 2 override)
    (
        {**_BASE, "insurance_situation": "medicare_only", "problem_type": "clean_denial"},
        {"primary_workflow": "workflow_1"},
    ),
    # 9 — Ground ambulance adds category K; G must NOT appear
    (
        {
            **_BASE,
            "problem_type": "surprise_out_of_network",
            "ambulance_involved": True,
            "ambulance_type": "ground",
        },
        {
            "primary_workflow": "workflow_2",
            "rule_modules_include": ["K"],
            "rule_modules_exclude": ["G"],
        },
    ),
    # 10 — Air ambulance adds category G; K must NOT appear
    (
        {
            **_BASE,
            "problem_type": "surprise_out_of_network",
            "ambulance_involved": True,
            "ambulance_type": "air",
        },
        {
            "primary_workflow": "workflow_2",
            "rule_modules_include": ["G"],
            "rule_modules_exclude": ["K"],
        },
    ),
    # 11 — Uninsured self-pay adds H (GFE) and I (PPDR)
    (
        {
            **_BASE,
            "insurance_situation": "uninsured_self_pay",
            "problem_type": "surprise_out_of_network",
        },
        {"primary_workflow": "workflow_2", "rule_modules_include": ["H", "I"]},
    ),
    # 12 — Catastrophic dollar amount → severity=catastrophic, escalation=suggested
    (
        {
            **_BASE,
            "problem_type": "surprise_out_of_network",
            "amount_patient_responsibility": 30000.0,
        },
        {
            "primary_workflow": "workflow_2",
            "severity": "catastrophic",
            "escalation_recommendation": "suggested",
            "escalation_reasons_include": ["high_dollar_exposure"],
        },
    ),
    # 13 — Minor dollar amount → severity=minor, no escalation on severity alone
    (
        {**_BASE, "problem_type": "clean_denial", "amount_patient_responsibility": 200.0},
        {
            "primary_workflow": "workflow_1",
            "severity": "minor",
            "escalation_recommendation": "none",
        },
    ),
    # 14 — notice_consent_claimed triggers escalation reason
    (
        {**_BASE, "problem_type": "surprise_out_of_network", "notice_consent_claimed": True},
        {
            "primary_workflow": "workflow_2",
            "escalation_recommendation": "suggested",
            "escalation_reasons_include": ["notice_and_consent_dispute"],
        },
    ),
    # 15 — Self-funded ERISA + state-law problem type triggers escalation
    (
        {
            **_BASE,
            "problem_type": "surprise_out_of_network",
            "plan_funding_type": "self_funded_erisa",
        },
        {
            "primary_workflow": "workflow_2",
            "escalation_recommendation": "suggested",
            "escalation_reasons_include": ["self_funded_erisa_state_law_conflict"],
        },
    ),
]
