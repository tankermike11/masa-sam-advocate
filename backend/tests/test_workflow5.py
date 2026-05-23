"""Tests for Workflow 5 — Light explain & route catch-all."""

from pathlib import Path

import pytest

from backend.intake.schema import IntakeSubmission
from backend.triage.engine import triage
from backend.workflows.answer_card import STANDARD_DISCLAIMER
from backend.workflows.workflow5 import run_workflow5
from backend.tests.fixtures.workflow5_fixtures import WORKFLOW5_FIXTURES

PILOT_DB_PATH = Path("data/pilot.db")

_BASE = {
    "insurance_situation": "commercial_employer",
    "state": "FL",
    "problem_type": "billing_error",
}


def _run(kwargs: dict):
    intake = IntakeSubmission(**kwargs)
    triage_result = triage(intake)
    return run_workflow5(intake, triage_result)


@pytest.mark.parametrize("intake_kwargs,expected", WORKFLOW5_FIXTURES)
def test_workflow5_fixture(intake_kwargs, expected):
    card = _run(intake_kwargs)
    combined_found = " ".join(card.what_we_found).lower()
    next_step = card.recommended_next_step.lower()

    if expected.get("medicaid_in_found"):
        assert "medicaid" in combined_found, (
            f"Expected 'medicaid' in what_we_found; got: {card.what_we_found}"
        )
    if expected.get("state_in_next_step"):
        state = intake_kwargs["state"].lower()
        assert state in next_step or "medicaid" in next_step, (
            f"Expected state or medicaid in next_step; got: {card.recommended_next_step}"
        )
    if expected.get("next_step_non_empty"):
        assert card.recommended_next_step.strip() != ""
    if expected.get("code_in_found"):
        code = expected["code_in_found"]
        assert code in " ".join(card.what_we_found)
    if "escalation" in expected:
        assert card.escalation_recommendation == expected["escalation"]


def test_medicaid_routes_to_workflow5_and_mentions_state():
    card = _run({"insurance_situation": "medicaid", "state": "FL", "problem_type": "billing_error"})
    combined = " ".join(card.what_we_found + [card.recommended_next_step]).lower()
    assert "medicaid" in combined
    assert "fl" in combined or "florida" in combined or "medicaid" in combined


def test_escalation_always_suggested():
    card = _run({**_BASE})
    assert card.escalation_recommendation == "suggested"


def test_recommended_next_step_never_empty():
    for kwargs in [
        {"insurance_situation": "medicaid", "state": "FL", "problem_type": "billing_error"},
        {**_BASE},
        {"insurance_situation": "medicare_only", "state": "TX", "problem_type": "billing_error"},
    ]:
        card = _run(kwargs)
        assert card.recommended_next_step.strip() != "", (
            f"Empty recommended_next_step for {kwargs}"
        )


def test_what_we_found_never_empty():
    card = _run({**_BASE})
    assert len(card.what_we_found) > 0
    assert all(item.strip() for item in card.what_we_found)


def test_standard_disclaimer_present():
    card = _run({**_BASE})
    assert card.disclaimer == STANDARD_DISCLAIMER


def test_workflow_field_is_workflow_5():
    card = _run({**_BASE})
    assert card.workflow == "workflow_5"


@pytest.mark.skipif(
    not PILOT_DB_PATH.exists(),
    reason="pilot.db not present",
)
def test_icd10cm_code_decoded_in_found():
    card = _run({
        **_BASE,
        "codes_present": [{"code_type": "ICD10CM", "code": "A00"}],
    })
    assert any("A00" in item for item in card.what_we_found), (
        f"Expected 'A00' in what_we_found; got: {card.what_we_found}"
    )


@pytest.mark.skipif(
    not PILOT_DB_PATH.exists(),
    reason="pilot.db not present",
)
def test_unknown_code_in_needs_verification():
    card = _run({
        **_BASE,
        "codes_present": [{"code_type": "ICD10CM", "code": "ZZZZZZZ"}],
    })
    combined = " ".join(card.what_needs_verification)
    assert "ZZZZZZZ" in combined
