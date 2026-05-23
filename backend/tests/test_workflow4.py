"""Tests for Workflow 4 — Collections microflow (no pilot.db needed)."""

import pytest

from backend.intake.schema import IntakeSubmission
from backend.workflows.answer_card import STANDARD_DISCLAIMER
from backend.workflows.workflow4 import run_workflow4
from backend.tests.fixtures.workflow4_fixtures import WORKFLOW4_FIXTURES

_BASE = {
    "insurance_situation": "commercial_employer",
    "state": "FL",
    "problem_type": "collections_credit_impact",
}


def _run(kwargs: dict):
    return run_workflow4(IntakeSubmission(**kwargs))


@pytest.mark.parametrize("intake_kwargs,expected", WORKFLOW4_FIXTURES)
def test_workflow4_fixture(intake_kwargs, expected):
    card = _run(intake_kwargs)
    combined_found = " ".join(card.what_we_found).lower()

    if expected.get("fdcpa_in_found"):
        assert "fdcpa" in combined_found or "fair debt" in combined_found, (
            f"Expected FDCPA in what_we_found; got: {card.what_we_found[:2]}"
        )
    if expected.get("cfpb_in_found"):
        assert "cfpb" in combined_found or "consumerfinance" in combined_found
    if expected.get("debt_letter_in_found"):
        assert "validation" in combined_found or "certified mail" in combined_found
    if expected.get("credit_mention_in_found"):
        assert "credit" in combined_found
    if "escalation" in expected:
        assert card.escalation_recommendation == expected["escalation"]


def test_fdcpa_rights_in_found():
    card = _run({**_BASE, "in_collections": True})
    combined = " ".join(card.what_we_found).lower()
    assert "fdcpa" in combined or "fair debt" in combined


def test_debt_validation_letter_present():
    card = _run({**_BASE, "in_collections": True})
    combined = " ".join(card.what_we_found)
    assert "1692g" in combined or "validation" in combined.lower()


def test_cfpb_routing_included():
    card = _run({**_BASE})
    combined = " ".join(card.what_we_found).lower()
    assert "cfpb" in combined or "consumerfinance" in combined


def test_escalation_always_suggested():
    card = _run({**_BASE})
    assert card.escalation_recommendation == "suggested"


def test_workflow_field_is_workflow_4():
    card = _run({**_BASE})
    assert card.workflow == "workflow_4"


def test_standard_disclaimer_present():
    card = _run({**_BASE})
    assert card.disclaimer == STANDARD_DISCLAIMER


def test_no_pilot_db_citations():
    card = _run({**_BASE})
    # Workflow 4 has no pilot.db dependency; citations should be empty
    assert card.citations == []


def test_no_crash_when_not_in_collections():
    card = _run({**_BASE})
    assert card is not None
    assert card.recommended_next_step


def test_state_appears_in_letter():
    card = _run({**_BASE, "state": "TX", "in_collections": True})
    combined = " ".join(card.what_we_found)
    assert "TX" in combined
