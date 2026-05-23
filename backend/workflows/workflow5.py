"""
Workflow 5 — Light "explain & route" catch-all (PRD §6.6).

Ensures no case dead-ends. Handles:
  - Medicaid (Axis-2 override routed here regardless of problem_type, PRD §4.2)
  - Any unrecognized problem_type not matched by Workflows 1–4
  - Any case that falls through to the catch-all

Per PRD §6.6: "Catch-all so no case dead-ends."
Every case receives an explanation + a concrete recommended_next_step.
"""

from __future__ import annotations

import logging

from backend.data_access.interface import lookup_code
from backend.intake.schema import InsuranceSituation, IntakeSubmission
from backend.triage.engine import TriageResult
from backend.workflows.answer_card import AnswerCard, build_citations

logger = logging.getLogger(__name__)

_SOURCE_MAP = {
    "ICD10CM": "a01_icd10cm", "ICD10PCS": "a02_icd10pcs",
    "HCPCS":   "a03_hcpcs",   "CARC":     "a05_carc",
    "RARC":    "a06_rarc",    "REVENUECODE": "a07_revenue",
}


def run_workflow5(intake: IntakeSubmission, triage_result: TriageResult) -> AnswerCard:
    """
    Light explanation and routing. Every case that reaches here gets a concrete next step.
    Graceful degradation on code lookups (same pattern as Workflow 1).
    """
    found: list[str] = []
    interpretation: list[str] = []
    needs_verification: list[str] = []
    source_ids: list[str] = []

    # ── Decode any codes present ──────────────────────────────────────────────
    for entry in intake.codes_present:
        try:
            result = lookup_code(entry.code_type, entry.code)
        except Exception as exc:
            logger.error("lookup_code failed in workflow5 for %r/%r: %s",
                         entry.code_type, entry.code, exc)
            needs_verification.append(
                f"Code {entry.code_type}/{entry.code}: lookup failed — verify manually."
            )
            continue

        if result is None:
            needs_verification.append(
                f"Code {entry.code_type}/{entry.code}: not found in database."
            )
        elif "fallback" in result:
            needs_verification.append(
                f"CPT code {entry.code}: {result['fallback']}"
            )
        else:
            desc = result.get("description") or result.get("short_description", "(no description)")
            found.append(f"{entry.code_type} {entry.code}: {desc}")
            sid = result.get("source_id") or _SOURCE_MAP.get(entry.code_type.upper())
            if sid:
                source_ids.append(sid)

    # ── Route by insurance situation and problem type ─────────────────────────
    if intake.insurance_situation == InsuranceSituation.medicaid:
        found.append(
            f"Coverage type: Medicaid ({intake.state})."
        )
        interpretation.append(
            "Medicaid adjudication rules vary significantly by state. "
            "Deep Medicaid adjudication — including benefit determinations, prior-auth rules, "
            "and appeal procedures — is outside the scope of this system's automated workflows."
        )
        needs_verification.append(
            f"State-specific Medicaid eligibility and appeal procedures for {intake.state} "
            "require direct review with your state Medicaid agency."
        )
        next_step = (
            f"Contact your {intake.state} state Medicaid office for case-specific guidance. "
            "Find your state's Medicaid agency at medicaid.gov/state-overviews. "
            "A human advocate with state Medicaid expertise can provide additional support."
        )

    else:
        if not found:
            found.append(
                f"Case received: {intake.problem_type} / "
                f"{intake.insurance_situation.value.replace('_', ' ')}."
            )
        interpretation.append(
            "This case type was not matched to a specialized automated workflow. "
            "Limited analysis is available from the structured intake data provided."
        )
        interpretation.append(
            "A human advocate can review the full context and provide appropriate, "
            "case-specific next steps."
        )
        needs_verification.append(
            "Provide complete intake details to a human advocate for a thorough assessment."
        )
        next_step = (
            "Request escalation to a human advocate for personalized guidance on this case. "
            "Describe the issue and any relevant dates, amounts, and communications received."
        )

    # ── Dollar context ────────────────────────────────────────────────────────
    if intake.amount_patient_responsibility:
        found.append(
            f"Patient responsibility on file: ${intake.amount_patient_responsibility:,.2f}."
        )

    # ── Ensure what_we_found is never empty ───────────────────────────────────
    if not found:
        found.append("Case received for light explanation and routing.")

    return AnswerCard(
        workflow="workflow_5",
        what_we_found=found,
        what_it_likely_means=interpretation or [
            "Insufficient information for automated analysis. Human review recommended."
        ],
        citations=build_citations(list(dict.fromkeys(source_ids))),
        confidence={},
        what_needs_verification=needs_verification,
        recommended_next_step=next_step,
        dollar_at_stake=intake.amount_patient_responsibility,
        escalation_recommendation="suggested",
    )
