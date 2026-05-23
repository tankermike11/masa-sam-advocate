"""
Workflow 1 — Explain a bill / EOB (PRD §6.2).

Scope: per-line code semantics + bill-level dollar reconciliation.
NOT per-line dollar reconciliation (intake captures bill-level totals only).

Graceful degradation: individual lookup failures are caught and noted in
what_needs_verification; the workflow never aborts on a single code or plan failure.
"""

from __future__ import annotations

import logging

from backend.data_access.interface import lookup_code, search_plan, get_sbc_fields
from backend.intake.schema import IntakeSubmission
from backend.workflows.answer_card import AnswerCard, build_citations

logger = logging.getLogger(__name__)

_SOURCE_MAP = {
    "ICD10CM":    "a01_icd10cm",
    "ICD10PCS":   "a02_icd10pcs",
    "HCPCS":      "a03_hcpcs",
    "CARC":       "a05_carc",
    "RARC":       "a06_rarc",
    "RevenueCode":"a07_revenue",
    "POS":        "a08_pos",
    "Modifier":   "a09_modifiers",
    "MSDRG":      "a10_ms_drg",
    "NDC":        "a11_ndc",
    "CPT":        "a04_cpt_handling",
}


def run_workflow1(intake: IntakeSubmission) -> AnswerCard:
    """
    Explain each code on the bill and reconcile bill-level dollar amounts.
    Returns a fully structured AnswerCard (all 6 sections populated).
    """
    found: list[str] = []
    interpretation: list[str] = []
    needs_verification: list[str] = []
    source_ids: list[str] = []
    confidence: dict[str, str] = {}
    codes_decoded = 0

    # ── Step 1: Decode codes ──────────────────────────────────────────────────
    for entry in intake.codes_present:
        try:
            result = lookup_code(entry.code_type, entry.code)
        except Exception as exc:
            logger.error("lookup_code(%r, %r) failed: %s", entry.code_type, entry.code, exc)
            needs_verification.append(
                f"Code {entry.code_type}/{entry.code}: lookup failed — verify manually."
            )
            continue

        if result is None:
            needs_verification.append(
                f"Code {entry.code_type}/{entry.code}: not found in database — verify code is correct."
            )
            confidence[entry.code] = "unknown"
            continue

        if "fallback" in result:
            # CPT code — AMA license boundary
            needs_verification.append(
                f"CPT code {entry.code}: {result['fallback']}"
            )
            confidence[entry.code] = "low"
            source_ids.append(result["source_id"])
            continue

        desc = result.get("description") or result.get("short_description") or "(no description)"
        found.append(f"{entry.code_type} {entry.code}: {desc}")
        codes_decoded += 1
        confidence[entry.code] = "high"
        sid = result.get("source_id") or _SOURCE_MAP.get(entry.code_type.upper())
        if sid:
            source_ids.append(sid)

    # ── Step 2: Plan lookup ───────────────────────────────────────────────────
    plan_data: dict | None = None
    if intake.plan_identifier:
        try:
            plans = search_plan(intake.plan_identifier, intake.state)
            if plans:
                plan_id = plans[0]["plan_id"]
                plan_data = get_sbc_fields(plan_id)
                if plan_data:
                    src = "f02_downloader" if plan_data.get("_source") == "sbc" else "b02_plan_attributes_puf"
                    source_ids.append(src)
                    plan_name = plans[0].get("plan_name", plan_id)
                    found.append(f"Plan identified: {plan_name} ({plans[0].get('metal_level', '')} {plans[0].get('plan_year', '')})")
                    confidence["plan_data"] = "medium" if plan_data.get("_source") == "plan_attributes" else "high"
                else:
                    needs_verification.append(
                        f"Plan '{intake.plan_identifier}' found but no benefit data available."
                    )
                    confidence["plan_data"] = "unknown"
            else:
                needs_verification.append(
                    f"Plan '{intake.plan_identifier}' not found; benefit context unavailable."
                )
                confidence["plan_data"] = "unknown"
        except Exception as exc:
            logger.error("Plan lookup failed for %r: %s", intake.plan_identifier, exc)
            needs_verification.append("Plan benefit lookup failed; verify manually.")
            confidence["plan_data"] = "unknown"

    # ── Step 3: Bill-level dollar reconciliation ──────────────────────────────
    billed = intake.amount_billed
    allowed = intake.amount_allowed
    paid = intake.amount_plan_paid
    responsibility = intake.amount_patient_responsibility

    if billed is not None and allowed is not None:
        found.append(f"Provider billed ${billed:,.2f}; plan recognized ${allowed:,.2f}.")
        confidence["billing_amounts"] = "high"
        if billed > allowed:
            interpretation.append(
                f"The billed amount (${billed:,.2f}) exceeds the plan's recognized amount "
                f"(${allowed:,.2f}) by ${billed - allowed:,.2f}. This is normal when providers "
                f"bill above the plan's contracted rate."
            )
    elif billed is not None:
        found.append(f"Provider billed ${billed:,.2f}.")
        needs_verification.append("Plan's recognized (allowed) amount not provided.")
        confidence["billing_amounts"] = "medium"
    else:
        needs_verification.append("Billed amount not provided; full reconciliation unavailable.")
        confidence["billing_amounts"] = "unknown"

    if paid is not None and responsibility is not None and allowed is not None:
        total_accounted = paid + responsibility
        if total_accounted < allowed - 0.01:
            interpretation.append(
                f"Plan paid ${paid:,.2f} + patient responsibility ${responsibility:,.2f} = "
                f"${total_accounted:,.2f}, which is less than the recognized amount (${allowed:,.2f}). "
                f"There may be an underpayment worth investigating."
            )
    if responsibility is None:
        needs_verification.append("Patient responsibility amount not provided.")

    # ── Step 4: Escalation check ──────────────────────────────────────────────
    escalation = "none"
    if codes_decoded == 0 and not intake.codes_present:
        pass  # No codes provided — not a failure
    elif codes_decoded == 0 and intake.codes_present:
        needs_verification.append(
            "None of the provided codes could be decoded. Manual review recommended."
        )
        escalation = "suggested"

    if plan_data is None and intake.plan_identifier and not intake.codes_present:
        escalation = "suggested"

    # ── Step 5: Build recommended next step ───────────────────────────────────
    if escalation == "suggested":
        next_step = (
            "Data was insufficient for a complete assessment. "
            "Request escalation to a human advocate for detailed review."
        )
    elif any("underpayment" in i for i in interpretation):
        next_step = (
            "File an internal appeal citing the underpayment identified above. "
            "Request an itemized bill and Explanation of Benefits from your plan."
        )
    elif billed and responsibility and (billed - (responsibility or 0)) > 500:
        next_step = (
            "Request an itemized bill to verify each charge. "
            "Compare line items against your Explanation of Benefits."
        )
    else:
        next_step = (
            "Review the decoded charges and dollar amounts above. "
            "If anything appears incorrect, contact your plan's member services."
        )

    if responsibility is not None:
        next_step += f" Dollar at stake: ${responsibility:,.2f}."

    # ── Interpretation additions ───────────────────────────────────────────────
    if not interpretation:
        if codes_decoded > 0:
            interpretation.append(
                "The codes on this bill appear to be standard medical billing codes. "
                "No obvious anomalies were detected from the structured data alone."
            )
        else:
            interpretation.append(
                "Insufficient data to provide interpretation. "
                "A human advocate can review the full bill."
            )

    return AnswerCard(
        workflow="workflow_1",
        what_we_found=found,
        what_it_likely_means=interpretation,
        citations=build_citations(list(dict.fromkeys(source_ids))),
        confidence=confidence,
        what_needs_verification=needs_verification,
        recommended_next_step=next_step,
        dollar_at_stake=responsibility,
        escalation_recommendation=escalation,
    )
