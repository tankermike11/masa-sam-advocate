"""
Structured intake schema — Pydantic v2 models and enums (PRD §5).

IntakeSubmission is the single validated object that flows into the triage engine
and all downstream workflows. The LLM intake-mapping call (Phase 1+) produces one
of these; direct structured intake produces one directly.
"""

from enum import Enum

from pydantic import BaseModel, Field, field_validator


class InsuranceSituation(str, Enum):
    commercial_employer = "commercial_employer"
    commercial_individual = "commercial_individual"
    medicare_only = "medicare_only"
    medicare_advantage = "medicare_advantage"
    medicaid = "medicaid"
    uninsured_self_pay = "uninsured_self_pay"


class PlanFundingType(str, Enum):
    fully_insured = "fully_insured"
    self_funded_erisa = "self_funded_erisa"
    unknown = "unknown"


class ProblemType(str, Enum):
    surprise_out_of_network = "surprise_out_of_network"
    clean_denial = "clean_denial"
    partial_payment_underpayment = "partial_payment_underpayment"
    balance_bill = "balance_bill"
    billing_error = "billing_error"
    catastrophic_exposure = "catastrophic_exposure"
    collections_credit_impact = "collections_credit_impact"


class ServiceType(str, Enum):
    emergency = "emergency"
    non_emergency = "non_emergency"
    scheduled = "scheduled"


class NetworkStatus(str, Enum):
    in_network = "in_network"
    out_of_network = "out_of_network"
    unknown = "unknown"


class AmbulanceType(str, Enum):
    ground = "ground"
    air = "air"
    unknown = "unknown"


class AdvocacyCapacity(str, Enum):
    self_directed = "self_directed"
    needs_hand_holding = "needs_hand_holding"
    needs_proxy = "needs_proxy"


class CodeEntry(BaseModel):
    code_type: str
    code: str


class GfeProvider(BaseModel):
    provider_name: str | None = None
    expected_charge: float | None = None


class IntakeSubmission(BaseModel):
    # ── Required ─────────────────────────────────────────────────────────────
    insurance_situation: InsuranceSituation
    state: str                    # two-letter US state code
    problem_type: ProblemType

    # ── Plan ─────────────────────────────────────────────────────────────────
    plan_funding_type: PlanFundingType = PlanFundingType.unknown
    plan_identifier: str | None = None

    # ── Bill / claim ─────────────────────────────────────────────────────────
    codes_present: list[CodeEntry] = Field(default_factory=list)
    amount_billed: float | None = None
    amount_allowed: float | None = None
    amount_plan_paid: float | None = None
    amount_patient_responsibility: float | None = None
    denial_present: bool = False
    denial_codes: list[str] = Field(default_factory=list)
    denial_reason_text: str | None = None
    service_date: str | None = None
    bill_date: str | None = None
    denial_date: str | None = None

    # ── Event ─────────────────────────────────────────────────────────────────
    service_type: ServiceType | None = None
    facility_network_status: NetworkStatus = NetworkStatus.unknown
    provider_network_status: NetworkStatus = NetworkStatus.unknown
    ambulance_involved: bool = False
    ambulance_type: AmbulanceType | None = None

    # ── Surprise-billing specifics ────────────────────────────────────────────
    notice_consent_claimed: bool = False
    notice_timestamp: str | None = None
    service_timestamp: str | None = None
    appointment_lead_time: int | None = None   # days

    # ── Self-pay / GFE ────────────────────────────────────────────────────────
    gfe_received: bool = False
    gfe_expected_charges: list[GfeProvider] = Field(default_factory=list)

    # ── Collections ───────────────────────────────────────────────────────────
    in_collections: bool = False
    reported_to_credit: bool = False
    debt_validated: bool = False

    # ── MASA membership ───────────────────────────────────────────────────────
    is_masa_member: bool = False
    masa_plan_tier: str | None = None

    # ── Member context ────────────────────────────────────────────────────────
    # Defaults to needs_hand_holding per PRD §5.8 if not answered.
    advocacy_capacity: AdvocacyCapacity = AdvocacyCapacity.needs_hand_holding

    @field_validator("state")
    @classmethod
    def state_must_be_two_letters(cls, v: str) -> str:
        v = v.upper()
        if len(v) != 2 or not v.isalpha():
            raise ValueError("state must be a two-letter US state code (e.g. 'FL')")
        return v
