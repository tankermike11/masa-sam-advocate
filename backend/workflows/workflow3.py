"""
Workflow 3 — Document generation (PRD §6.4).

Generates up to four parameterized, citation-backed documents from case data.
The LLM fills parameterized templates; it does not free-draft legal language.

COUNSEL GATE (PRD §13): All documents carry counsel_required=True.
Templates must receive counsel sign-off before any real member sees output.
This review runs in parallel with the build.

Returns (AnswerCard, list[GeneratedDocument]) so the router can persist
both the meta-card (workflow_outputs) and the documents (generated_documents).
"""

from __future__ import annotations

import logging
from datetime import date

from pydantic import BaseModel

from backend.data_access.interface import lookup_code
from backend.intake.schema import InsuranceSituation, IntakeSubmission
from backend.nsa.engine import NSADetermination, nsa_rule_engine
from backend.triage.engine import TriageResult
from backend.workflows.answer_card import (
    AnswerCard,
    Citation,
    STANDARD_DISCLAIMER,
    build_citations,
)

logger = logging.getLogger(__name__)

_SOURCE_MAP = {
    "ICD10CM": "a01_icd10cm", "ICD10PCS": "a02_icd10pcs",
    "HCPCS": "a03_hcpcs",     "CARC": "a05_carc",
    "RARC": "a06_rarc",        "REVENUECODE": "a07_revenue",
    "POS": "a08_pos",          "MODIFIER": "a09_modifiers",
    "MSDRG": "a10_ms_drg",     "NDC": "a11_ndc",
}


class GeneratedDocument(BaseModel):
    document_type: str        # "itemized_bill_request" | "internal_appeal"
                              #  | "balance_bill_dispute" | "ppdr_initiation"
    content: str              # full text (parameterized, not LLM-free-drafted)
    citations: list[Citation]
    disclaimer: str = STANDARD_DISCLAIMER
    counsel_required: bool = True  # always True — counsel sign-off required before member use


# ── Public entry point ────────────────────────────────────────────────────────

def run_workflow3(
    intake: IntakeSubmission,
    triage_result: TriageResult,
) -> tuple[AnswerCard, list[GeneratedDocument]]:
    """
    Generate applicable documents and return the meta AnswerCard + document list.
    Re-runs the NSA engine internally; does not depend on Workflow 2 having been run.
    """
    determination = nsa_rule_engine(intake, triage_result.rule_modules)

    documents: list[GeneratedDocument] = []
    doc_names: list[str] = []
    all_source_ids: list[str] = []

    def _add(doc: GeneratedDocument, label: str) -> None:
        documents.append(doc)
        doc_names.append(label)
        all_source_ids.extend(c.source_id for c in doc.citations)

    # Always generate itemized-bill request
    _add(_generate_itemized_bill_request(intake, determination), "Itemized bill request letter")

    if intake.denial_present:
        _add(_generate_internal_appeal(intake, triage_result, determination), "First-level internal appeal letter")

    if triage_result.problem_type in ("balance_bill", "surprise_out_of_network"):
        _add(_generate_balance_bill_dispute(intake, triage_result, determination), "Balance-bill dispute letter")

    if (
        intake.insurance_situation == InsuranceSituation.uninsured_self_pay
        and intake.gfe_received
    ):
        _add(_generate_ppdr_initiation(intake, determination), "PPDR initiation summary")

    found = [f"{len(documents)} document(s) generated:"] + [f"  - {n}" for n in doc_names]

    card = AnswerCard(
        workflow="workflow_3",
        what_we_found=found,
        what_it_likely_means=[
            "These documents are parameterized templates based on your case data.",
            "Each contains [PLACEHOLDER] fields you must complete before sending.",
            "Counsel review required before any document is sent to a real member (PRD §13).",
        ],
        citations=build_citations(list(dict.fromkeys(all_source_ids))),
        confidence={
            "document_generation": "high",
            "legal_framing": "pending_counsel_review",
        },
        what_needs_verification=[
            "All [BRACKETED PLACEHOLDER] fields must be completed by the member.",
            "Counsel sign-off required on all templates before member use (§13).",
        ],
        recommended_next_step=(
            "Review each document, complete all [BRACKETED] fields, "
            "and send via certified mail with return receipt requested. "
            "Keep a copy of all correspondence."
        ),
        escalation_recommendation=determination.escalation_recommendation,
        dollar_at_stake=intake.amount_patient_responsibility,
    )

    return card, documents


# ── Document generators ───────────────────────────────────────────────────────

def _generate_itemized_bill_request(
    intake: IntakeSubmission,
    determination: NSADetermination,
) -> GeneratedDocument:
    service_date = intake.service_date or "[SERVICE DATE — from your bill]"
    amount = f"${intake.amount_billed:,.2f}" if intake.amount_billed else "[BILLED AMOUNT]"
    codes_line = ""
    source_ids = ["e01_nsa_rules"]
    if intake.codes_present:
        codes_line = "Billing codes referenced: " + ", ".join(
            f"{e.code_type} {e.code}" for e in intake.codes_present
        )
        for e in intake.codes_present:
            sid = _SOURCE_MAP.get(e.code_type.upper())
            if sid:
                source_ids.append(sid)

    content = f"""[DATE: {date.today().isoformat()}]

[YOUR NAME]
[YOUR ADDRESS]
[CITY, STATE, ZIP]

Re: Request for Itemized Bill
Service Date: {service_date}
Billed Amount: {amount}
{codes_line}

To Whom It May Concern:

I am writing to request a complete itemized bill for services rendered on {service_date}.
Please provide a detailed statement including:

  1. A line-by-line itemization of all charges
  2. The procedure and diagnosis codes (CPT, ICD-10, HCPCS) for each service
  3. The name of each provider who rendered services
  4. The service date for each charge
  5. The applicable diagnosis code(s) supporting each billed service

Patients are entitled to receive an itemized statement of charges. Please provide this
within 30 days of receipt of this letter.

If you have questions, contact me at [YOUR PHONE / EMAIL].

Sincerely,
[YOUR SIGNATURE]
[YOUR PRINTED NAME]

IMPORTANT: Complete all [BRACKETED] fields before sending.
{STANDARD_DISCLAIMER}
"""
    return GeneratedDocument(
        document_type="itemized_bill_request",
        content=content,
        citations=build_citations(list(dict.fromkeys(source_ids))),
    )


def _generate_internal_appeal(
    intake: IntakeSubmission,
    triage_result: TriageResult,
    determination: NSADetermination,
) -> GeneratedDocument:
    service_date = intake.service_date or "[SERVICE DATE]"
    amount = f"${intake.amount_billed:,.2f}" if intake.amount_billed else "[AMOUNT DENIED]"
    plan = intake.plan_identifier or "[PLAN NAME]"
    source_ids = ["e01_nsa_rules"]

    # Decode denial codes
    decoded: list[str] = []
    for code in intake.denial_codes:
        for code_type in ("CARC", "RARC"):
            try:
                result = lookup_code(code_type, code)
                if result and result.get("description"):
                    decoded.append(f"{code} ({code_type}): {result['description']}")
                    sid = _SOURCE_MAP.get(code_type)
                    if sid:
                        source_ids.append(sid)
                    break
            except Exception:
                pass
        else:
            decoded.append(code)
    if intake.denial_reason_text:
        decoded.append(f"Stated reason: {intake.denial_reason_text}")
    denial_block = "\n".join(f"  - {d}" for d in decoded) if decoded else "  [DENIAL REASON — from your EOB]"

    rule_cites = [
        f"  - {m.rule_id}: {m.citation}"
        for m in determination.matched_rules[:3]
        if m.citation
    ]
    source_ids.extend(determination.cited_sources)
    rule_block = "\n".join(rule_cites) if rule_cites else "  [Applicable federal/state regulations — see counsel review]"

    content = f"""[DATE: {date.today().isoformat()}]

[YOUR NAME]
[YOUR ADDRESS]
[CITY, STATE, ZIP]

[PLAN APPEALS ADDRESS — from your insurance card or EOB]

Re: First-Level Internal Appeal
Plan / Insurer: {plan}
Member ID: [YOUR MEMBER ID]
Claim Number: [CLAIM NUMBER — from your EOB]
Service Date: {service_date}
Amount at Issue: {amount}

To the Appeals Department:

I am submitting this first-level internal appeal for the denial described above.

Denial reason(s) as stated on my Explanation of Benefits:
{denial_block}

Basis for appeal:

I believe this denial may be inconsistent with my plan benefits and applicable federal
protections for the following reasons:

  1. [DESCRIBE YOUR CLINICAL OR COVERAGE ARGUMENT — e.g., "The service was medically
     necessary as documented by my treating physician Dr. [NAME]"]

  2. [REFERENCE APPLICABLE PLAN LANGUAGE — e.g., "My plan's Summary of Benefits covers
     emergency services at the in-network cost-sharing level"]

Applicable regulations (pending counsel review):
{rule_block}

I respectfully request that you overturn this denial and process the claim for benefits
as outlined in my plan documents. Please provide a written decision within the required
timeframe and, if upheld, information about external review rights.

Enclosures: [ATTACH: EOB, medical records, physician letter if applicable]

Sincerely,
[YOUR SIGNATURE]
[YOUR PRINTED NAME]

IMPORTANT: Complete all [BRACKETED] fields. Counsel review recommended before sending.
{STANDARD_DISCLAIMER}
"""
    return GeneratedDocument(
        document_type="internal_appeal",
        content=content,
        citations=build_citations(list(dict.fromkeys(source_ids))),
    )


def _generate_balance_bill_dispute(
    intake: IntakeSubmission,
    triage_result: TriageResult,
    determination: NSADetermination,
) -> GeneratedDocument:
    service_date = intake.service_date or "[SERVICE DATE]"
    billed = f"${intake.amount_billed:,.2f}" if intake.amount_billed else "[BILLED AMOUNT]"
    responsibility = (
        f"${intake.amount_patient_responsibility:,.2f}"
        if intake.amount_patient_responsibility
        else "[DISPUTED AMOUNT]"
    )
    source_ids = list(dict.fromkeys(["e01_nsa_rules"] + determination.cited_sources))

    rule_cites = [
        f"  - {m.rule_id}: {m.citation}"
        for m in determination.matched_rules[:5]
        if m.citation and not m.is_human_review
    ]
    rule_block = "\n".join(rule_cites) if rule_cites else "  [Applicable federal/state regulations — see counsel review]"

    is_ground = (
        intake.ambulance_involved
        and intake.ambulance_type is not None
        and intake.ambulance_type.value == "ground"
    )
    if is_ground:
        protection_text = (
            "Ground ambulance services are not currently protected by the federal No Surprises Act. "
            "However, your state may have applicable protections, and the Medicare reference rate "
            "provides a negotiation basis."
        )
        action_text = "reduce the balance to a reasonable amount consistent with the Medicare reference rate for this service"
    else:
        protection_text = (
            "Federal regulations under the No Surprises Act (45 CFR Part 149) may limit the "
            "amount you can be charged for out-of-network services in certain circumstances."
        )
        action_text = "apply the appropriate in-network cost-sharing amount as required by applicable law"

    content = f"""[DATE: {date.today().isoformat()}]

[YOUR NAME]
[YOUR ADDRESS]
[CITY, STATE, ZIP]

[PROVIDER/FACILITY NAME AND ADDRESS — from your bill]

Re: Dispute of Balance Bill
Service Date: {service_date}
Account Number: [ACCOUNT NUMBER — from your bill]
Amount Billed: {billed}
Amount in Dispute: {responsibility}

To Whom It May Concern:

I am writing to formally dispute the balance bill referenced above.

{protection_text}

Applicable citations (pending counsel review):
{rule_block}

I respectfully request that you {action_text}.

Please respond in writing within 30 days confirming:
  1. The corrected amount owed under applicable law and plan terms
  2. Any process for further dispute resolution

Enclosures: [ATTACH: EOB, plan Summary of Benefits, relevant correspondence]

Sincerely,
[YOUR SIGNATURE]
[YOUR PRINTED NAME]

IMPORTANT: Complete all [BRACKETED] fields. Counsel review required before sending.
{STANDARD_DISCLAIMER}
"""
    return GeneratedDocument(
        document_type="balance_bill_dispute",
        content=content,
        citations=build_citations(source_ids),
    )


def _generate_ppdr_initiation(
    intake: IntakeSubmission,
    determination: NSADetermination,
) -> GeneratedDocument:
    service_date = intake.service_date or "[SERVICE DATE]"
    billed = f"${intake.amount_billed:,.2f}" if intake.amount_billed else "[BILLED AMOUNT]"

    gfe_lines: list[str] = []
    total_expected = 0.0
    for gfe in intake.gfe_expected_charges:
        name = gfe.provider_name or "[PROVIDER]"
        charge = gfe.expected_charge or 0.0
        total_expected += charge
        gfe_lines.append(f"  - {name}: ${charge:,.2f}")
    gfe_block = "\n".join(gfe_lines) if gfe_lines else "  [GFE EXPECTED CHARGES — from your Good Faith Estimate]"

    if intake.amount_billed is not None and total_expected > 0:
        discrepancy = intake.amount_billed - total_expected
        discrepancy_text = (
            f"${discrepancy:,.2f} (billed ${intake.amount_billed:,.2f} "
            f"vs. GFE ${total_expected:,.2f})"
        )
    else:
        discrepancy_text = "[CALCULATE: billed amount minus GFE expected charge]"

    content = f"""[DATE: {date.today().isoformat()}]

[YOUR NAME]
[YOUR ADDRESS]
[CITY, STATE, ZIP]

[PROVIDER/FACILITY NAME AND ADDRESS — from your bill or GFE]

Re: Patient-Provider Dispute Resolution (PPDR) Initiation Notice
Service Date: {service_date}
Account Number: [ACCOUNT NUMBER — from your bill]
Amount Billed: {billed}

To Whom It May Concern:

I am initiating a Patient-Provider Dispute Resolution (PPDR) request pursuant to
45 CFR Part 149, Subpart F, regarding charges that substantially exceed the
Good Faith Estimate (GFE) I received prior to services.

Good Faith Estimate — Expected Charges:
{gfe_block}

Actual Charges Billed: {billed}
Amount in Excess of GFE: {discrepancy_text}

Pursuant to federal regulations, charges that exceed the GFE by $400 or more for
any individual provider or facility may be disputed through PPDR (45 CFR 149.610).

I request that:
  1. You hold collection activity and suspend any late fees while this dispute is pending
     (45 CFR 149.620(c))
  2. You provide PPDR process contact information within the applicable timeframe

Required enclosures (I will provide with this notice):
  [ ] Copy of the Good Faith Estimate
  [ ] Copy of the bill/invoice showing charges above the GFE
  [ ] Contact information for all providers listed on the GFE

Note: PPDR initiation deadline is 120 calendar days from receipt of the initial bill
with charges substantially above the GFE (45 CFR 149.610(a)).

Sincerely,
[YOUR SIGNATURE]
[YOUR PRINTED NAME]

IMPORTANT: Note the 120-day deadline. Complete all [BRACKETED] fields and attach
required documents before sending. Counsel review required before use.
{STANDARD_DISCLAIMER}
"""
    return GeneratedDocument(
        document_type="ppdr_initiation",
        content=content,
        citations=build_citations(["e01_nsa_rules"]),
    )
