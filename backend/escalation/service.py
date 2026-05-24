"""
Escalation service — monetization gate and case escalation logic (PRD §8, §9).

Gate: reads pricing_rules.yaml, evaluates is_masa_member + masa_plan_tier,
returns a fee decision. No payment processing — decision only.

Escalation: updates cases.escalation_status and cases.gate_decision in app.db.
The member always decides; the engine recommends but never forces (PRD §8.1).
"""

from __future__ import annotations

import json
import logging
from functools import lru_cache

import yaml

from backend.config_loader import _resolve_config
from pydantic import BaseModel

from backend.db.app_db import get_app_conn
from backend.intake.schema import IntakeSubmission

logger = logging.getLogger(__name__)


class GateDecision(BaseModel):
    fee_applies: bool
    message: str
    tier_matched: str | None = None   # the waived tier name if fee is waived


class EscalationResult(BaseModel):
    case_id: str
    escalation_status: str   # "requested" | "recommended"
    gate_decision: GateDecision


class CaseNotFoundError(LookupError):
    """Raised when the requested case_id does not exist in app.db."""
    pass


@lru_cache(maxsize=1)
def _load_pricing_config() -> dict:
    with open(_resolve_config("pricing_rules.yaml")) as f:
        return yaml.safe_load(f)


def evaluate_gate(is_masa_member: bool, masa_plan_tier: str | None) -> GateDecision:
    """
    Evaluate the monetization gate for an escalation request (PRD §9).

    Returns GateDecision with fee_applies=False (waived) or True (charged).
    Never collects payment — decision and message only.
    """
    config = _load_pricing_config()

    if is_masa_member:
        member_cfg = config["member"]
        waived_tiers: list[str] = member_cfg.get("waived_tiers", [])
        if masa_plan_tier in waived_tiers:
            return GateDecision(
                fee_applies=False,
                message=member_cfg["message_waived"],
                tier_matched=masa_plan_tier,
            )
        return GateDecision(
            fee_applies=True,
            message=member_cfg["message_charged"],
            tier_matched=None,
        )

    # non_member: future state — not exercised in the member-only prototype (PRD §9)
    return GateDecision(
        fee_applies=True,
        message="A service charge applies for human escalation.",
        tier_matched=None,
    )


_TRIGGER_TO_STATUS: dict[str, str] = {
    "member_initiated": "requested",
    "engine_recommended": "recommended",
}


def request_escalation(
    case_id: str,
    trigger: str,
    intake_json: str,
) -> EscalationResult:
    """
    Evaluate the gate and update the case's escalation_status + gate_decision.

    trigger "member_initiated"   → escalation_status = "requested"
    trigger "engine_recommended" → escalation_status = "recommended"

    Raises:
        ValueError: if trigger is not a recognised value
        CaseNotFoundError: if case_id does not exist in app.db
    """
    new_status = _TRIGGER_TO_STATUS.get(trigger)
    if new_status is None:
        raise ValueError(
            f"Unknown escalation trigger {trigger!r}. "
            f"Must be one of: {sorted(_TRIGGER_TO_STATUS)}"
        )

    intake = IntakeSubmission.model_validate_json(intake_json)
    gate = evaluate_gate(intake.is_masa_member, intake.masa_plan_tier)

    with get_app_conn() as conn:
        row = conn.execute(
            "SELECT case_id FROM cases WHERE case_id = ?", (case_id,)
        ).fetchone()
        if row is None:
            raise CaseNotFoundError(f"Case {case_id!r} not found in app.db.")

        conn.execute(
            "UPDATE cases SET escalation_status = ?, gate_decision = ? WHERE case_id = ?",
            (new_status, json.dumps(gate.model_dump()), case_id),
        )
        conn.commit()

    logger.info(
        "Escalation recorded: case=%r trigger=%r status=%r fee_applies=%s tier=%r",
        case_id, trigger, new_status, gate.fee_applies, gate.tier_matched,
    )
    return EscalationResult(case_id=case_id, escalation_status=new_status, gate_decision=gate)
