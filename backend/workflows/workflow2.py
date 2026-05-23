"""
Workflow 2 — Ambulance / surprise-bill triage (PRD §6.3).

Routes by ambulance type:
  - Ground ambulance → _handle_ground_ambulance() (Table K; NOT NSA-protected)
  - Air ambulance    → NSA rule engine (Table G)
  - Non-ambulance    → NSA rule engine (Tables A–E, J, as selected by triage)

Ground-ambulance node (PRD §6.3, Table K):
  Explains federal gap, surfaces Medicare reference rate as negotiation anchor,
  checks state-law routing, MASA gap-coverage, and hardship options.
  Framing is ALWAYS "negotiation context, not legal entitlement" (§13).
"""

from __future__ import annotations

import logging

from backend.data_access.interface import get_ambulance_reference_rate
from backend.intake.schema import (
    AmbulanceType,
    InsuranceSituation,
    IntakeSubmission,
    PlanFundingType,
)
from backend.nsa.engine import NSADetermination, nsa_rule_engine
from backend.triage.engine import TriageResult
from backend.workflows.answer_card import AnswerCard, build_citations

logger = logging.getLogger(__name__)

# Ambulance HCPCS codes present in ambulance_fee_schedule
_AMBULANCE_HCPCS = frozenset({"A0425", "A0426", "A0427", "A0428", "A0429",
                                "A0430", "A0431", "A0432", "A0433", "A0434"})
_DEFAULT_GROUND_HCPCS = "A0425"  # mileage per loaded mile — most common ground code


def run_workflow2(intake: IntakeSubmission, triage_result: TriageResult) -> AnswerCard:
    """Route ambulance vs. non-ambulance and return the appropriate AnswerCard."""
    if intake.ambulance_involved and intake.ambulance_type == AmbulanceType.ground:
        return _handle_ground_ambulance(intake, triage_result)

    # Air ambulance or non-ambulance surprise/balance-bill: run NSA engine
    determination = nsa_rule_engine(intake, triage_result.rule_modules)
    return _build_nsa_answer_card(intake, determination)


# ── NSA answer card (air ambulance + non-ambulance surprise/balance) ──────────

def _build_nsa_answer_card(
    intake: IntakeSubmission,
    det: NSADetermination,
) -> AnswerCard:
    found: list[str] = []
    interpretation: list[str] = []
    needs_verification: list[str] = []
    confidence: dict[str, str] = {}

    if det.matched_rules:
        found.append(
            f"{len(det.matched_rules)} applicable rule(s) evaluated across "
            f"categor{'y' if len(det.rule_modules) == 1 else 'ies'} "
            f"{', '.join(det.rule_modules)}."
        )
        for rule in det.matched_rules[:5]:  # surface first 5 to keep card readable
            found.append(f"[{rule.rule_id}] {rule.system_action}")
        if len(det.matched_rules) > 5:
            found.append(f"…and {len(det.matched_rules) - 5} additional rule(s).")
    else:
        found.append("No applicable rules matched for the provided intake data.")

    if not det.has_counsel_approved_rules:
        found.append(
            "Note: All applicable rules are currently pending counsel review. "
            "A definitive determination is not available at this time."
        )
        confidence["rule_determination"] = "low"
    else:
        confidence["rule_determination"] = "high"

    if det.protection_determination == "likely_protected":
        interpretation.append(
            "Based on the rules evaluated, this case appears to involve federal "
            "balance-billing protections under the No Surprises Act. "
            "This is a preliminary assessment — not a definitive legal conclusion."
        )
    elif det.protection_determination == "not_protected":
        interpretation.append(
            "Based on the rules evaluated, this service does not appear to be "
            "covered by federal No Surprises Act balance-billing protections."
        )
    else:
        interpretation.append(
            "The rules evaluated indicate this case requires human review for "
            "a definitive assessment."
        )

    if intake.ambulance_involved and intake.ambulance_type == AmbulanceType.air:
        interpretation.append(
            "Air ambulance services are generally covered by federal NSA protections "
            "when the plan covers emergency air transport."
        )

    needs_verification.append(
        "All NSA rule determinations are pending counsel review. "
        "Treat this output as preliminary — consult a human advocate before acting."
    )

    # Build recommended next step from collected actions
    actions_lower = [a.lower() for a in det.actions]
    if any("appeal" in a for a in actions_lower):
        next_step = "File an internal appeal citing the applicable NSA protections identified above."
    elif any("human review" in a for a in actions_lower):
        next_step = "This case requires human advocate review for a definitive assessment."
    else:
        next_step = (
            "Review the matched rules above. "
            "Contact your plan to discuss the identified protections."
        )

    if det.escalation_recommendation == "suggested":
        next_step += " Escalation to a human advocate is strongly recommended."

    return AnswerCard(
        workflow="workflow_2",
        what_we_found=found,
        what_it_likely_means=interpretation,
        citations=build_citations(det.cited_sources),
        confidence=confidence,
        what_needs_verification=needs_verification,
        recommended_next_step=next_step,
        dollar_at_stake=intake.amount_patient_responsibility,
        escalation_recommendation=det.escalation_recommendation,
    )


# ── Ground-ambulance handling node ────────────────────────────────────────────

def _handle_ground_ambulance(
    intake: IntakeSubmission,
    triage_result: TriageResult,
) -> AnswerCard:
    """
    Ground ambulance handling node — Table K (PRD §6.3).

    Ground ambulance is NOT protected by the federal No Surprises Act.
    This node explains that gap, surfaces the Medicare reference rate as a
    negotiation anchor (NOT a legal cap), and routes appropriately.
    """
    found: list[str] = []
    interpretation: list[str] = []
    needs_verification: list[str] = []
    confidence: dict[str, str] = {}
    source_ids: list[str] = ["e01_nsa_rules"]
    next_step_parts: list[str] = []

    # Run K-category rules through the engine for structured action collection
    determination = nsa_rule_engine(intake, ["K"])

    # ── GROUND-003: Federal gap explanation (mandatory) ───────────────────────
    found.append(
        "As of 2026, ground ambulance services are NOT protected by the federal "
        "No Surprises Act. The Advisory Committee on Ground Ambulance and Patient "
        "Billing issued recommendations in March 2024, but no binding federal "
        "protection has been enacted."
    )
    confidence["federal_protection"] = "high"

    # ── GROUND-009: Medicare reference rate ───────────────────────────────────
    ambulance_hcpcs = _get_ambulance_hcpcs(intake)
    rate_result = None
    try:
        rate_result = get_ambulance_reference_rate(ambulance_hcpcs, intake.state)
    except Exception as exc:
        logger.error("get_ambulance_reference_rate(%r, %r) failed: %s",
                     ambulance_hcpcs, intake.state, exc)

    if rate_result:
        rate_dollars = rate_result["reference_rate_dollars"]
        found.append(
            f"Medicare reference rate for {ambulance_hcpcs} in {intake.state}: "
            f"${rate_dollars:,.2f} (effective {rate_result.get('effective_year', 'N/A')})."
        )
        confidence["reference_rate"] = "high"
        source_ids.append(rate_result.get("source_id", "c01_ambulance_fee_schedule"))

        if intake.amount_billed is not None:
            gap = intake.amount_billed - rate_dollars
            found.append(
                f"Billed amount: ${intake.amount_billed:,.2f}. "
                f"Gap above Medicare reference rate: ${gap:,.2f}."
            )
            interpretation.append(
                f"The Medicare reference rate (${rate_dollars:,.2f}) provides a negotiation "
                f"anchor for the provider conversation. This is not a legal cap or entitlement — "
                f"it is a benchmark to use when negotiating a reduced balance."
            )
            next_step_parts.append(
                f"Contact the ambulance provider and request a reduction to or near the "
                f"Medicare reference rate of ${rate_dollars:,.2f} for {ambulance_hcpcs} in {intake.state}."
            )
        else:
            next_step_parts.append(
                f"Use the Medicare reference rate (${rate_dollars:,.2f}) as a negotiation anchor "
                f"when contacting the ambulance provider."
            )
    else:
        needs_verification.append(
            f"Medicare reference rate not found for {ambulance_hcpcs} in {intake.state}. "
            f"Human review recommended for negotiation strategy."
        )
        confidence["reference_rate"] = "unknown"
        next_step_parts.append(
            "Contact a human advocate for negotiation strategy — reference rate unavailable."
        )

    # ── GROUND-004/005: State-law routing ─────────────────────────────────────
    needs_verification.append(
        f"State-specific ground ambulance balance-billing laws for {intake.state} have not "
        f"been evaluated. Your state may have protections — human review recommended."
    )
    if intake.plan_funding_type == PlanFundingType.self_funded_erisa:
        needs_verification.append(
            "Self-funded ERISA plans are typically not subject to state insurance laws. "
            "Federal preemption likely applies — human review recommended."
        )
    elif intake.plan_funding_type == PlanFundingType.unknown:
        needs_verification.append(
            "Plan funding type is unknown. If the plan is self-funded ERISA, "
            "state ground ambulance laws may not apply."
        )

    # ── GROUND-006: Medicare/MA/Medicaid routing ──────────────────────────────
    if intake.insurance_situation in (
        InsuranceSituation.medicare_only,
        InsuranceSituation.medicare_advantage,
        InsuranceSituation.medicaid,
    ):
        interpretation.append(
            f"Your coverage ({intake.insurance_situation.value.replace('_', ' ')}) has its own "
            f"rules for ground ambulance. Medicare assignment and limiting-charge rules constrain "
            f"provider billing differently than commercial surprise-billing protections."
        )
        next_step_parts.append(
            "Consult a human advocate or your program's member services for program-specific guidance."
        )

    # ── GROUND-007: Claim adjudication verification ───────────────────────────
    if intake.denial_present or intake.amount_plan_paid is None:
        needs_verification.append(
            "Verify the claim was properly submitted and adjudicated by your plan. "
            "The balance may reflect a denial, processing error, or unsubmitted claim "
            "rather than a true balance bill."
        )

    # ── GROUND-008: Self-pay GFE/PPDR cross-reference ────────────────────────
    if intake.insurance_situation == InsuranceSituation.uninsured_self_pay:
        if intake.gfe_received:
            found.append(
                "You received a Good Faith Estimate (GFE). "
                "If the final charges exceed the GFE amount by $400 or more for any single provider, "
                "you may be eligible for the Patient-Provider Dispute Resolution (PPDR) process."
            )
            next_step_parts.append(
                "Compare the bill to the GFE you received. "
                "If the difference is ≥$400 per provider, consider initiating PPDR."
            )
        else:
            needs_verification.append(
                "As an uninsured/self-pay patient, you were entitled to a Good Faith Estimate. "
                "If none was provided for a scheduled service, this may be a disclosure issue."
            )

    # ── GROUND-010: MASA gap-coverage routing ─────────────────────────────────
    if intake.is_masa_member:
        interpretation.append(
            "As a MASA member, you may be eligible for gap-coverage benefits that apply "
            "to the residual balance after advocacy efforts are exhausted."
        )
        next_step_parts.append(
            "Review your MASA plan documents for gap-coverage eligibility on ground ambulance balances."
        )

    # ── GROUND-011: Hardship options for high/catastrophic severity ───────────
    if triage_result.severity in ("high", "catastrophic"):
        interpretation.append(
            "Ground ambulance providers — including municipal, fire-district, hospital-based, "
            "and private services — frequently offer financial hardship discounts and "
            "interest-free payment plans for large balances."
        )
        next_step_parts.append(
            "Ask the provider about financial hardship discount programs and payment plans."
        )

    # ── Escalation ────────────────────────────────────────────────────────────
    escalation = determination.escalation_recommendation  # always "suggested" (all rules draft)

    # ── Final recommended next step ───────────────────────────────────────────
    if not next_step_parts:
        next_step_parts.append(
            "Contact the ambulance provider to discuss the balance and explore resolution options."
        )
    next_step_parts.append(
        "Request escalation to a human advocate for state-law guidance and negotiation support."
    )
    recommended = " ".join(next_step_parts)

    dollar_at_stake = intake.amount_patient_responsibility or intake.amount_billed

    return AnswerCard(
        workflow="workflow_2",
        what_we_found=found,
        what_it_likely_means=interpretation,
        citations=build_citations(list(dict.fromkeys(source_ids))),
        confidence=confidence,
        what_needs_verification=needs_verification,
        recommended_next_step=recommended,
        dollar_at_stake=dollar_at_stake,
        escalation_recommendation=escalation,
    )


def _get_ambulance_hcpcs(intake: IntakeSubmission) -> str:
    """Return the first ambulance HCPCS from codes_present, or default to A0425."""
    for entry in intake.codes_present:
        if entry.code_type.upper() == "HCPCS" and entry.code in _AMBULANCE_HCPCS:
            return entry.code
    return _DEFAULT_GROUND_HCPCS
