"""
NSA rule predicate functions — one per rule_id (PRD §6.7).

The table (nsa_rules in pilot.db) is the spec; these functions are the implementation.
Each predicate returns True if the rule applies/fires for the given intake.
Exceptions are handled by the engine (treated as human_review, never as "no violation").

Registration pattern: @_p("RULE-ID") decorates a lambda-style function.
All 59 rule_ids from Categories A–K must be registered.

IMPORTANT: All rules are currently status="draft" (awaiting counsel review).
The engine degrades all draft-rule determinations to "human_review_required".
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Callable

from backend.intake.schema import (
    AmbulanceType,
    InsuranceSituation,
    IntakeSubmission,
    NetworkStatus,
    PlanFundingType,
    ServiceType,
)

PREDICATES: dict[str, Callable[[IntakeSubmission], bool]] = {}


def _p(rule_id: str) -> Callable:
    """Decorator that registers a predicate function under rule_id."""
    def decorator(fn: Callable[[IntakeSubmission], bool]) -> Callable[[IntakeSubmission], bool]:
        PREDICATES[rule_id] = fn
        return fn
    return decorator


# ── Category A: Federal Foundation ───────────────────────────────────────────

@_p("NSA-FED-001")
def _(intake: IntakeSubmission) -> bool:
    # NSA Part 149 applies: always fires as entry gate for any applicable case.
    return True


@_p("NSA-FED-002")
def _(intake: IntakeSubmission) -> bool:
    # Cannot determine from intake whether plan is excepted benefit/STLDI/HRA.
    # Unknown funding type → route to human review.
    return intake.plan_funding_type == PlanFundingType.unknown


@_p("NSA-FED-003")
def _(intake: IntakeSubmission) -> bool:
    # State-specified law applicability requires a state-law table not yet built.
    # Human review handles state-law routing.
    return False


@_p("NSA-FED-004")
def _(intake: IntakeSubmission) -> bool:
    # All-payer model agreement — cannot determine from structured intake.
    return False


# ── Category B: Emergency Services ───────────────────────────────────────────

@_p("NSA-EMERG-001")
def _(intake: IntakeSubmission) -> bool:
    # Plan must cover emergency services; applies when emergency service was denied.
    return (
        intake.service_type == ServiceType.emergency
        and intake.denial_present
    )


@_p("NSA-EMERG-002")
def _(intake: IntakeSubmission) -> bool:
    # Emergency services covered without regard to network status.
    return (
        intake.service_type == ServiceType.emergency
        and intake.provider_network_status == NetworkStatus.out_of_network
    )


@_p("NSA-EMERG-003")
def _(intake: IntakeSubmission) -> bool:
    # OON emergency cannot have stricter admin requirements than in-network.
    return (
        intake.service_type == ServiceType.emergency
        and intake.provider_network_status == NetworkStatus.out_of_network
    )


@_p("NSA-EMERG-004")
def _(intake: IntakeSubmission) -> bool:
    # OON emergency cost-sharing cannot exceed in-network amount.
    return (
        intake.service_type == ServiceType.emergency
        and intake.provider_network_status == NetworkStatus.out_of_network
        and intake.amount_patient_responsibility is not None
    )


@_p("NSA-EMERG-005")
def _(intake: IntakeSubmission) -> bool:
    # Cost-sharing uses recognized amount (QPA-dependent); needs expert verification.
    return (
        intake.service_type == ServiceType.emergency
        and intake.provider_network_status == NetworkStatus.out_of_network
    )


@_p("NSA-EMERG-006")
def _(intake: IntakeSubmission) -> bool:
    # OON emergency cost-sharing must count toward in-network deductible/OOP.
    return (
        intake.service_type == ServiceType.emergency
        and intake.provider_network_status == NetworkStatus.out_of_network
        and intake.denial_present
    )


# ── Category C: Non-Emergency OON at In-Network Facility ─────────────────────

@_p("NSA-NONEMERG-001")
def _(intake: IntakeSubmission) -> bool:
    # OON provider at in-network facility cannot balance bill without valid notice/consent.
    return (
        intake.facility_network_status == NetworkStatus.in_network
        and intake.provider_network_status == NetworkStatus.out_of_network
        and intake.service_type != ServiceType.emergency
        and not intake.notice_consent_claimed
    )


@_p("NSA-NONEMERG-002")
def _(intake: IntakeSubmission) -> bool:
    # Protected OON cost-sharing cannot exceed in-network cost-sharing.
    return (
        intake.facility_network_status == NetworkStatus.in_network
        and intake.provider_network_status == NetworkStatus.out_of_network
        and intake.service_type != ServiceType.emergency
    )


@_p("NSA-NONEMERG-003")
def _(intake: IntakeSubmission) -> bool:
    # Cost-sharing uses recognized amount; human review for rate confirmation.
    return (
        intake.facility_network_status == NetworkStatus.in_network
        and intake.provider_network_status == NetworkStatus.out_of_network
        and intake.service_type != ServiceType.emergency
    )


@_p("NSA-NONEMERG-004")
def _(intake: IntakeSubmission) -> bool:
    # Protected cost-sharing must count toward in-network deductible/OOP.
    return (
        intake.facility_network_status == NetworkStatus.in_network
        and intake.provider_network_status == NetworkStatus.out_of_network
        and intake.service_type != ServiceType.emergency
        and intake.denial_present
    )


@_p("NSA-NONEMERG-005")
def _(intake: IntakeSubmission) -> bool:
    # Claim pending > 30 days after necessary info received.
    if not intake.service_date:
        return False
    try:
        svc = date.fromisoformat(intake.service_date)
        return (date.today() - svc).days > 30
    except (ValueError, AttributeError):
        return False


# ── Category D: Notice and Consent ───────────────────────────────────────────

@_p("NSA-CONSENT-001")
def _(intake: IntakeSubmission) -> bool:
    # Any claimed consent → route to human review for timing/form check.
    return intake.notice_consent_claimed


@_p("NSA-CONSENT-002")
def _(intake: IntakeSubmission) -> bool:
    # Appointment ≥72 hours advance: notice must be ≥72 hours before service.
    if not intake.notice_consent_claimed:
        return False
    lead = intake.appointment_lead_time
    if lead is None or lead < 3:
        return False
    # If timestamps provided, do precise check.
    if intake.notice_timestamp and intake.service_timestamp:
        try:
            notice_dt = datetime.fromisoformat(intake.notice_timestamp)
            service_dt = datetime.fromisoformat(intake.service_timestamp)
            hours_before = (service_dt - notice_dt).total_seconds() / 3600
            return hours_before < 72
        except (ValueError, AttributeError):
            pass
    # Appointment ≥3 days advance but no timestamps → flag for review.
    return True


@_p("NSA-CONSENT-003")
def _(intake: IntakeSubmission) -> bool:
    # Same-day appointment: notice must be ≥3 hours before service.
    if not intake.notice_consent_claimed:
        return False
    lead = intake.appointment_lead_time
    if lead is None or lead != 0:
        return False
    if intake.notice_timestamp and intake.service_timestamp:
        try:
            notice_dt = datetime.fromisoformat(intake.notice_timestamp)
            service_dt = datetime.fromisoformat(intake.service_timestamp)
            hours_before = (service_dt - notice_dt).total_seconds() / 3600
            return hours_before < 3
        except (ValueError, AttributeError):
            pass
    return True  # same-day, no timestamps → flag


@_p("NSA-CONSENT-004")
def _(intake: IntakeSubmission) -> bool:
    # Consent must be voluntary; cannot verify from structured intake alone.
    return False


@_p("NSA-CONSENT-005")
def _(intake: IntakeSubmission) -> bool:
    # Authorized representative rules; not verifiable from intake.
    return False


# ── Category E: Non-Waivable Services ────────────────────────────────────────

@_p("NSA-NONWAIVE-001")
def _(intake: IntakeSubmission) -> bool:
    # Ancillary services (anesthesiology, pathology, etc.) cannot be balance-billed.
    return (
        intake.provider_network_status == NetworkStatus.out_of_network
        and intake.facility_network_status == NetworkStatus.in_network
    )


@_p("NSA-NONWAIVE-002")
def _(intake: IntakeSubmission) -> bool:
    # Unforeseen urgent need arising during service — applies if emergency with consent.
    return (
        intake.service_type == ServiceType.emergency
        and intake.notice_consent_claimed
    )


# ── Category F: Disclosure Requirements ──────────────────────────────────────

@_p("NSA-DISCLOSURE-001")
def _(intake: IntakeSubmission) -> bool:
    # Provider must have posted balance-billing disclosure; applies when OON bill received.
    return (
        intake.provider_network_status == NetworkStatus.out_of_network
        or intake.facility_network_status == NetworkStatus.out_of_network
    )


@_p("NSA-DISCLOSURE-002")
def _(intake: IntakeSubmission) -> bool:
    # Disclosure content must include all required elements.
    return (
        intake.provider_network_status == NetworkStatus.out_of_network
        or intake.facility_network_status == NetworkStatus.out_of_network
    )


@_p("NSA-DISCLOSURE-003")
def _(intake: IntakeSubmission) -> bool:
    # Disclosure must be provided by time payment is requested.
    return (
        intake.provider_network_status == NetworkStatus.out_of_network
        or intake.facility_network_status == NetworkStatus.out_of_network
    )


# ── Category G: Air Ambulance ─────────────────────────────────────────────────

@_p("NSA-AIR-001")
def _(intake: IntakeSubmission) -> bool:
    # If air ambulance benefits covered, OON cost-sharing must equal in-network.
    return (
        intake.ambulance_involved
        and intake.ambulance_type == AmbulanceType.air
        and intake.insurance_situation != InsuranceSituation.uninsured_self_pay
    )


@_p("NSA-AIR-002")
def _(intake: IntakeSubmission) -> bool:
    # Air ambulance cost-sharing uses QPA logic (QPA-dependent).
    return (
        intake.ambulance_involved
        and intake.ambulance_type == AmbulanceType.air
    )


@_p("NSA-AIR-003")
def _(intake: IntakeSubmission) -> bool:
    # Cost-sharing counts toward in-network deductible/OOP max.
    return (
        intake.ambulance_involved
        and intake.ambulance_type == AmbulanceType.air
    )


@_p("NSA-AIR-004")
def _(intake: IntakeSubmission) -> bool:
    # Plan must determine coverage within 30 days.
    return (
        intake.ambulance_involved
        and intake.ambulance_type == AmbulanceType.air
    )


# ── Category H: Good Faith Estimates (GFE) ────────────────────────────────────

@_p("GFE-001")
def _(intake: IntakeSubmission) -> bool:
    # Providers must supply GFE to uninsured/self-pay patients.
    return intake.insurance_situation == InsuranceSituation.uninsured_self_pay


@_p("GFE-002")
def _(intake: IntakeSubmission) -> bool:
    # GFE must be in writing and saveable; relevant when GFE was received.
    return (
        intake.insurance_situation == InsuranceSituation.uninsured_self_pay
        and intake.gfe_received
    )


@_p("GFE-003")
def _(intake: IntakeSubmission) -> bool:
    # GFE content requirements; applies when GFE received.
    return (
        intake.insurance_situation == InsuranceSituation.uninsured_self_pay
        and intake.gfe_received
    )


@_p("GFE-004")
def _(intake: IntakeSubmission) -> bool:
    # Co-provider GFE coordination; applies when GFE received.
    return (
        intake.insurance_situation == InsuranceSituation.uninsured_self_pay
        and intake.gfe_received
    )


@_p("GFE-005")
def _(intake: IntakeSubmission) -> bool:
    # Recurring-services GFE scope; applies when GFE received.
    return (
        intake.insurance_situation == InsuranceSituation.uninsured_self_pay
        and intake.gfe_received
    )


@_p("GFE-006")
def _(intake: IntakeSubmission) -> bool:
    # GFE is part of medical record; right to prior GFE copies.
    return intake.insurance_situation == InsuranceSituation.uninsured_self_pay


@_p("GFE-007")
def _(intake: IntakeSubmission) -> bool:
    # Good-faith error exception; applies when GFE received and charges are above estimate.
    return (
        intake.insurance_situation == InsuranceSituation.uninsured_self_pay
        and intake.gfe_received
    )


# ── Category I: Patient-Requested Price Determination (PPDR) ──────────────────

def _ppdr_base(intake: IntakeSubmission) -> bool:
    """Shared PPDR precondition: uninsured/self-pay with GFE received."""
    return (
        intake.insurance_situation == InsuranceSituation.uninsured_self_pay
        and intake.gfe_received
    )


@_p("PPDR-001")
def _(intake: IntakeSubmission) -> bool:
    # PPDR applies when charges ≥$400 above GFE.
    if not _ppdr_base(intake):
        return False
    if intake.amount_billed is None or not intake.gfe_expected_charges:
        return False
    total_expected = sum(
        p.expected_charge for p in intake.gfe_expected_charges
        if p.expected_charge is not None
    )
    if total_expected <= 0:
        return False
    return (intake.amount_billed - total_expected) >= 400


@_p("PPDR-002")
def _(intake: IntakeSubmission) -> bool:
    # Per-provider comparison; applies when GFE received.
    return _ppdr_base(intake) and bool(intake.gfe_expected_charges)


@_p("PPDR-003")
def _(intake: IntakeSubmission) -> bool:
    # Provider substitution; cannot determine from structured intake.
    return False


@_p("PPDR-004")
def _(intake: IntakeSubmission) -> bool:
    # 120-day deadline to initiate PPDR; applies when GFE received.
    return _ppdr_base(intake)


@_p("PPDR-005")
def _(intake: IntakeSubmission) -> bool:
    # Initiation notice requirements; applies when GFE received and threshold met.
    return _ppdr_base(intake) and intake.amount_billed is not None


@_p("PPDR-006")
def _(intake: IntakeSubmission) -> bool:
    # Insufficiency notice response window; not verifiable from intake alone.
    return False


@_p("PPDR-007")
def _(intake: IntakeSubmission) -> bool:
    # Provider must not move to collections while PPDR pending.
    return (
        _ppdr_base(intake)
        and intake.in_collections
    )


@_p("PPDR-008")
def _(intake: IntakeSubmission) -> bool:
    # Retaliation prohibition; not verifiable from structured intake.
    return False


# ── Category J: State-Law Routing ─────────────────────────────────────────────

@_p("STATE-ROUTE-001")
def _(intake: IntakeSubmission) -> bool:
    # State-specified law applies; requires state-law table not yet built.
    return False


@_p("STATE-ROUTE-002")
def _(intake: IntakeSubmission) -> bool:
    # Self-funded ERISA may not be subject to state insurance law.
    return intake.plan_funding_type == PlanFundingType.self_funded_erisa


@_p("STATE-ROUTE-003")
def _(intake: IntakeSubmission) -> bool:
    # Provider disclosures must include state protections; applies for OON cases.
    return (
        intake.provider_network_status == NetworkStatus.out_of_network
        or intake.facility_network_status == NetworkStatus.out_of_network
    )


@_p("STATE-ROUTE-004")
def _(intake: IntakeSubmission) -> bool:
    # HHS complaint referral routing; applies for any OON or balance-bill case.
    return (
        intake.provider_network_status == NetworkStatus.out_of_network
        or intake.facility_network_status == NetworkStatus.out_of_network
    )


# ── Category K: Ground Ambulance ──────────────────────────────────────────────

def _is_ground_ambulance(intake: IntakeSubmission) -> bool:
    return intake.ambulance_involved and intake.ambulance_type == AmbulanceType.ground


@_p("GROUND-001")
def _(intake: IntakeSubmission) -> bool:
    # Ground ambulance: outside scope of NSA balance-billing protections.
    return _is_ground_ambulance(intake)


@_p("GROUND-002")
def _(intake: IntakeSubmission) -> bool:
    # Ambulance type unknown → confirm before routing.
    return (
        intake.ambulance_involved
        and intake.ambulance_type == AmbulanceType.unknown
    )


@_p("GROUND-003")
def _(intake: IntakeSubmission) -> bool:
    # No federal NSA protection for ground ambulance; always explain the gap.
    return _is_ground_ambulance(intake)


@_p("GROUND-004")
def _(intake: IntakeSubmission) -> bool:
    # Some states protect ground ambulance; state-law check required → human review.
    return _is_ground_ambulance(intake)


@_p("GROUND-005")
def _(intake: IntakeSubmission) -> bool:
    # State law does NOT apply to self-funded ERISA plans.
    return (
        _is_ground_ambulance(intake)
        and intake.plan_funding_type in (PlanFundingType.self_funded_erisa, PlanFundingType.unknown)
    )


@_p("GROUND-006")
def _(intake: IntakeSubmission) -> bool:
    # Medicare/MA/Medicaid: covered benefit with program-specific rules.
    return (
        _is_ground_ambulance(intake)
        and intake.insurance_situation in (
            InsuranceSituation.medicare_only,
            InsuranceSituation.medicare_advantage,
            InsuranceSituation.medicaid,
        )
    )


@_p("GROUND-007")
def _(intake: IntakeSubmission) -> bool:
    # Verify claim was actually adjudicated before treating as balance bill.
    return (
        _is_ground_ambulance(intake)
        and (intake.denial_present or intake.amount_plan_paid is None)
        and intake.insurance_situation != InsuranceSituation.uninsured_self_pay
    )


@_p("GROUND-008")
def _(intake: IntakeSubmission) -> bool:
    # Self-pay with GFE → cross-reference PPDR pathway.
    return (
        _is_ground_ambulance(intake)
        and intake.insurance_situation == InsuranceSituation.uninsured_self_pay
    )


@_p("GROUND-009")
def _(intake: IntakeSubmission) -> bool:
    # Medicare reference rate provides negotiation anchor for ground ambulance.
    return _is_ground_ambulance(intake)


@_p("GROUND-010")
def _(intake: IntakeSubmission) -> bool:
    # MASA member with residual balance → route to MASA gap-coverage benefit.
    return _is_ground_ambulance(intake) and intake.is_masa_member


@_p("GROUND-011")
def _(intake: IntakeSubmission) -> bool:
    # Hardship discounts/payment plans available; surface for high-severity cases.
    # Severity check is done in the workflow (using TriageResult.severity).
    return _is_ground_ambulance(intake)
