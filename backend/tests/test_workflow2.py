"""Tests for Workflow 2 — Ambulance / surprise-bill triage."""

from pathlib import Path

import pytest

from backend.intake.schema import IntakeSubmission
from backend.triage.engine import triage
from backend.workflows.answer_card import STANDARD_DISCLAIMER
from backend.workflows.workflow2 import run_workflow2

PILOT_DB_PATH = Path("data/pilot.db")
pytestmark = pytest.mark.skipif(
    not PILOT_DB_PATH.exists(),
    reason="pilot.db not present — copy snapshot to data/pilot.db first",
)

_BASE = {
    "insurance_situation": "commercial_employer",
    "state": "FL",
    "problem_type": "surprise_out_of_network",
}


def _run(kwargs: dict):
    intake = IntakeSubmission(**kwargs)
    triage_result = triage(intake)
    return run_workflow2(intake, triage_result)


def test_ground_ambulance_mentions_federal_gap():
    card = _run({**_BASE, "ambulance_involved": True, "ambulance_type": "ground"})
    combined = " ".join(card.what_we_found).lower()
    assert "not protected" in combined or "no surprises act" in combined, (
        f"Expected federal gap explanation; got: {card.what_we_found}"
    )


def test_ground_ambulance_escalation_is_suggested():
    card = _run({**_BASE, "ambulance_involved": True, "ambulance_type": "ground"})
    assert card.escalation_recommendation == "suggested"


def test_air_ambulance_does_not_mention_federal_gap():
    card = _run({**_BASE, "ambulance_involved": True, "ambulance_type": "air"})
    combined = " ".join(card.what_we_found).lower()
    # Air ambulance goes through NSA engine, not the ground node
    assert "ground ambulance" not in combined


def test_ground_ambulance_with_hcpcs_returns_reference_rate():
    card = _run({
        **_BASE,
        "ambulance_involved": True,
        "ambulance_type": "ground",
        "codes_present": [{"code_type": "HCPCS", "code": "A0425"}],
        "amount_billed": 1800.0,
    })
    combined = " ".join(card.what_we_found).lower()
    assert "reference rate" in combined or "medicare" in combined, (
        f"Expected reference rate in what_we_found; got: {card.what_we_found}"
    )


def test_ground_ambulance_invalid_state_no_crash():
    card = _run({
        "insurance_situation": "commercial_employer",
        "state": "XX",
        "problem_type": "surprise_out_of_network",
        "ambulance_involved": True,
        "ambulance_type": "ground",
    })
    assert card is not None
    combined_verif = " ".join(card.what_needs_verification).lower()
    assert "reference rate" in combined_verif or "not found" in combined_verif


def test_ground_ambulance_masa_member_routing():
    card = _run({
        **_BASE,
        "ambulance_involved": True,
        "ambulance_type": "ground",
        "is_masa_member": True,
    })
    assert "masa" in card.recommended_next_step.lower(), (
        f"Expected MASA mention in recommended_next_step; got: {card.recommended_next_step}"
    )


def test_ground_ambulance_catastrophic_has_hardship_options():
    card = _run({
        **_BASE,
        "ambulance_involved": True,
        "ambulance_type": "ground",
        "amount_patient_responsibility": 30000.0,
    })
    combined = " ".join(card.what_it_likely_means).lower()
    assert "hardship" in combined or "payment plan" in combined, (
        f"Expected hardship options; got: {card.what_it_likely_means}"
    )


def test_ground_ambulance_self_pay_gfe_mentions_ppdr():
    card = _run({
        **_BASE,
        "insurance_situation": "uninsured_self_pay",
        "ambulance_involved": True,
        "ambulance_type": "ground",
        "gfe_received": True,
    })
    combined = " ".join(card.what_we_found + card.what_it_likely_means + [card.recommended_next_step]).lower()
    assert "ppdr" in combined or "good faith estimate" in combined or "dispute" in combined


def test_non_ambulance_surprise_bill_uses_nsa_engine():
    card = _run({**_BASE})
    # Non-ambulance goes through NSA engine; escalation = suggested (all rules draft)
    assert card.escalation_recommendation == "suggested"


def test_disclaimer_present_on_all_outputs():
    for kwargs in [
        {**_BASE, "ambulance_involved": True, "ambulance_type": "ground"},
        {**_BASE, "ambulance_involved": True, "ambulance_type": "air"},
        {**_BASE},
    ]:
        card = _run(kwargs)
        assert card.disclaimer == STANDARD_DISCLAIMER
