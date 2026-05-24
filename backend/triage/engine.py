"""
Triage engine — Billing Advocacy Axes Framework (PRD §4).

Axis 2 (insurance_situation) is evaluated FIRST and may override Axis 1.
Currently only medicaid is an explicit Axis 2 short-circuit; all others
proceed through the Axis 1 routing table.

Severity bands and escalation complexity flags are read from
config/escalation_rules.yaml (cached per process).
"""

from functools import lru_cache
from pathlib import Path

import yaml
from pydantic import BaseModel

from backend.intake.schema import (
    AmbulanceType,
    InsuranceSituation,
    IntakeSubmission,
    NetworkStatus,
    PlanFundingType,
    ProblemType,
)


class TriageResult(BaseModel):
    problem_type: str
    insurance_situation: str
    severity: str                  # minor | moderate | high | catastrophic | unknown
    advocacy_capacity: str
    primary_workflow: str          # workflow_1 through workflow_5
    rule_modules: list[str]        # nsa_rules category letters, e.g. ["A","B","K"]
    escalation_recommendation: str  # "none" | "suggested"
    escalation_reasons: list[str]


# Axis 1 routing: problem_type → (primary_workflow, base_rule_modules)
_ROUTING: dict[str, tuple[str, list[str]]] = {
    ProblemType.surprise_out_of_network:      ("workflow_2", ["A", "B", "C", "D", "E", "J"]),
    ProblemType.clean_denial:                 ("workflow_1", []),
    ProblemType.partial_payment_underpayment: ("workflow_1", []),
    ProblemType.balance_bill:                 ("workflow_2", ["A", "B", "C", "D", "E", "J"]),
    ProblemType.billing_error:                ("workflow_1", []),
    ProblemType.billing_explanation:          ("workflow_1", []),
    ProblemType.catastrophic_exposure:        ("workflow_1", []),
    ProblemType.collections_credit_impact:    ("workflow_4", []),
}

# Problem types that involve a potential state-law question (ERISA + state-law tension)
_STATE_LAW_PROBLEM_TYPES = frozenset({
    ProblemType.surprise_out_of_network,
    ProblemType.balance_bill,
})


@lru_cache(maxsize=1)
def _escalation_config() -> dict:
    path = Path("config/escalation_rules.yaml")
    with open(path) as f:
        return yaml.safe_load(f)


def _severity(intake: IntakeSubmission) -> str:
    cfg = _escalation_config()
    bands = cfg.get("severity_bands", {})

    amount = intake.amount_patient_responsibility
    if amount is None:
        amount = intake.amount_billed
    if amount is None:
        return "unknown"

    catastrophic_min = bands.get("catastrophic", {}).get("min_dollars", 25000)
    high_min = bands.get("high", {}).get("min_dollars", 5000)
    moderate_min = bands.get("moderate", {}).get("min_dollars", 500)

    if amount >= catastrophic_min:
        return "catastrophic"
    if amount >= high_min:
        return "high"
    if amount >= moderate_min:
        return "moderate"
    return "minor"


def triage(intake: IntakeSubmission) -> TriageResult:
    """
    Run the two-axis triage engine and return a routing decision.

    Axis 2 (insurance_situation) is evaluated first; medicaid short-circuits
    to workflow_5 regardless of problem_type (PRD §4.2).
    All other insurance situations proceed through the Axis 1 routing table.
    """
    # ── Axis 2 override ───────────────────────────────────────────────────────
    if intake.insurance_situation == InsuranceSituation.medicaid:
        return TriageResult(
            problem_type=intake.problem_type,
            insurance_situation=intake.insurance_situation,
            severity=_severity(intake),
            advocacy_capacity=intake.advocacy_capacity,
            primary_workflow="workflow_5",
            rule_modules=[],
            escalation_recommendation="none",
            escalation_reasons=[],
        )

    # ── Axis 1 routing ────────────────────────────────────────────────────────
    workflow, base_modules = _ROUTING.get(
        intake.problem_type, ("workflow_5", [])
    )
    rule_modules: list[str] = list(base_modules)

    # Ambulance type modifies rule_modules (PRD §6.3)
    if intake.ambulance_involved:
        if intake.ambulance_type == AmbulanceType.air:
            if "G" not in rule_modules:
                rule_modules.append("G")
        elif intake.ambulance_type == AmbulanceType.ground:
            if "K" not in rule_modules:
                rule_modules.append("K")

    # Self-pay triggers GFE (H) and PPDR (I) rule categories
    if intake.insurance_situation == InsuranceSituation.uninsured_self_pay:
        for cat in ("H", "I"):
            if cat not in rule_modules:
                rule_modules.append(cat)

    # ── Severity ──────────────────────────────────────────────────────────────
    severity = _severity(intake)

    # ── Escalation recommendation (Phase 1: intake-field triggers only) ───────
    # Rule-engine triggers (human_review actions) are added in Phase 2.
    reasons: list[str] = []

    if severity in ("high", "catastrophic"):
        reasons.append("high_dollar_exposure")

    if intake.notice_consent_claimed:
        reasons.append("notice_and_consent_dispute")

    if (
        intake.plan_funding_type == PlanFundingType.self_funded_erisa
        and intake.problem_type in _STATE_LAW_PROBLEM_TYPES
    ):
        reasons.append("self_funded_erisa_state_law_conflict")

    if (
        intake.facility_network_status == NetworkStatus.unknown
        and intake.problem_type in _STATE_LAW_PROBLEM_TYPES
    ):
        reasons.append("unknown_inputs_on_load_bearing_fields")

    return TriageResult(
        problem_type=intake.problem_type,
        insurance_situation=intake.insurance_situation,
        severity=severity,
        advocacy_capacity=intake.advocacy_capacity,
        primary_workflow=workflow,
        rule_modules=rule_modules,
        escalation_recommendation="suggested" if reasons else "none",
        escalation_reasons=reasons,
    )
