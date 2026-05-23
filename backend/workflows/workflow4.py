"""
Workflow 4 — Collections microflow (PRD §6.5).

A deliberate, self-contained endpoint for collections / credit harassment.
Does NOT resolve the collection — equips and routes.

No DB dependency. Three outputs:
  1. FDCPA-rights explainer
  2. Debt-validation letter template
  3. CFPB / state AG complaint routing

Structured so the deep collections-defense product can replace it later
without rework (PRD §6.5).
"""

from __future__ import annotations

from datetime import date

from backend.intake.schema import IntakeSubmission
from backend.workflows.answer_card import AnswerCard, STANDARD_DISCLAIMER


def run_workflow4(intake: IntakeSubmission) -> AnswerCard:
    """
    Collections microflow — no rule engine, no pilot.db lookups.
    Returns AnswerCard with FDCPA rights, debt-validation letter, and routing.
    """
    found: list[str] = []
    interpretation: list[str] = []
    needs_verification: list[str] = []

    # ── FDCPA rights explainer ────────────────────────────────────────────────
    found.append(
        "Under the Fair Debt Collection Practices Act (FDCPA, 15 U.S.C. §§ 1692–1692p), "
        "third-party debt collectors must: "
        "(1) provide written notice of the debt within 5 days of first contact; "
        "(2) stop collection activity if you dispute the debt in writing within 30 days "
        "of first contact; "
        "(3) validate the debt upon written request before continuing collection."
    )

    if intake.reported_to_credit:
        found.append(
            "A medical debt reported to credit bureaus while disputed may violate FDCPA §807 "
            "(false or misleading representations). You may have the right to dispute the "
            "credit report entry with each bureau (Equifax, Experian, TransUnion)."
        )

    if intake.debt_validated:
        found.append("Debt has been validated per your intake information.")
    else:
        found.append(
            "The debt has not been validated (per your intake). You have the right to "
            "request written validation under FDCPA §809 within 30 days of first written "
            "contact from the collector."
        )

    # ── Debt-validation letter ────────────────────────────────────────────────
    letter = (
        f"[DATE: {date.today().isoformat()}]\n\n"
        "[YOUR NAME]\n"
        "[YOUR ADDRESS]\n"
        "[CITY, STATE, ZIP]\n\n"
        "To: [COLLECTION AGENCY NAME AND ADDRESS — from your collection notice]\n"
        "Re: Account Number [ACCOUNT NUMBER — from your collection notice]\n\n"
        "I am writing pursuant to 15 U.S.C. § 1692g (FDCPA Section 809) to formally "
        "dispute and request validation of the above-referenced debt.\n\n"
        "Please provide:\n"
        "  1. The name and address of the original creditor\n"
        "  2. The original account number and the date the account was opened\n"
        "  3. Verification that the amount claimed is accurate and complete\n"
        f"  4. Documentation that this agency is licensed to collect debts in {intake.state}\n"
        "  5. A copy of any agreement or signed document creating this alleged obligation\n\n"
        "Until this debt is fully validated, you are required to cease all collection "
        "activity, including any credit reporting.\n\n"
        "[YOUR SIGNATURE — sign before sending]\n"
        "[YOUR PRINTED NAME]\n\n"
        "Send via CERTIFIED MAIL, RETURN RECEIPT REQUESTED. Keep a copy for your records.\n\n"
        f"IMPORTANT: Complete all [BRACKETED] fields before sending.\n"
        f"{STANDARD_DISCLAIMER}"
    )
    found.append(
        "Debt validation letter prepared — complete [BRACKETED] fields before sending:\n\n"
        + letter
    )

    # ── CFPB / State AG routing ───────────────────────────────────────────────
    found.append(
        "File a complaint with the Consumer Financial Protection Bureau (CFPB): "
        "consumerfinance.gov/complaint"
    )
    found.append(
        f"Contact the {intake.state} Attorney General for state-level debt collection "
        "law complaints. Search '[your state] attorney general consumer complaint' "
        "to find the correct form."
    )

    # ── Interpretation ────────────────────────────────────────────────────────
    interpretation.append(
        "Medical debt collection is governed by the FDCPA when handled by third-party "
        "collectors (not the original hospital/provider). Your rights include disputing "
        "the debt, requesting validation, and filing complaints for violations."
    )
    if intake.in_collections:
        interpretation.append(
            "Because your account is in collections, FDCPA protections apply directly. "
            "Act promptly — the 30-day dispute window runs from the date of first written "
            "contact from the collector."
        )

    needs_verification.append(
        "FDCPA applies to third-party debt collectors. If the original provider "
        "(e.g., the hospital) is collecting its own debt, FDCPA may not apply — "
        "verify with a consumer law advocate."
    )
    needs_verification.append(
        "Complete all [BRACKETED] fields in the letter above before sending."
    )

    return AnswerCard(
        workflow="workflow_4",
        what_we_found=found,
        what_it_likely_means=interpretation,
        citations=[],   # FDCPA is statutory; no pilot.db sources needed
        confidence={"fdcpa_applicability": "medium"},
        what_needs_verification=needs_verification,
        recommended_next_step=(
            "Send the debt validation letter by certified mail within 30 days of "
            "first written contact from the collector. "
            "If the collector continues activity without validating, file a complaint "
            "with the CFPB at consumerfinance.gov/complaint. "
            "Escalation to a consumer law advocate is recommended for FDCPA violations "
            "or credit report disputes."
        ),
        dollar_at_stake=intake.amount_patient_responsibility,
        escalation_recommendation="suggested",
    )
