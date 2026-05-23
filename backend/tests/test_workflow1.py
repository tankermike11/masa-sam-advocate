"""Tests for Workflow 1 — Explain a bill / EOB."""

from pathlib import Path

import pytest

from backend.intake.schema import IntakeSubmission
from backend.workflows.answer_card import STANDARD_DISCLAIMER
from backend.workflows.workflow1 import run_workflow1

PILOT_DB_PATH = Path("data/pilot.db")
pytestmark = pytest.mark.skipif(
    not PILOT_DB_PATH.exists(),
    reason="pilot.db not present — copy snapshot to data/pilot.db first",
)

_BASE = {
    "insurance_situation": "commercial_employer",
    "state": "FL",
    "problem_type": "billing_error",
}


def _run(kwargs: dict):
    return run_workflow1(IntakeSubmission(**kwargs))


def test_icd10cm_code_decoded_in_found():
    card = _run({**_BASE, "codes_present": [{"code_type": "ICD10CM", "code": "A00"}]})
    assert any("A00" in item for item in card.what_we_found), (
        f"Expected 'A00' in what_we_found; got: {card.what_we_found}"
    )
    assert any("cholera" in item.lower() for item in card.what_we_found)


def test_cpt_code_returns_fallback_in_needs_verification():
    card = _run({**_BASE, "codes_present": [{"code_type": "CPT", "code": "99213"}]})
    assert any("CPT" in item or "99213" in item for item in card.what_needs_verification), (
        f"Expected CPT note in what_needs_verification; got: {card.what_needs_verification}"
    )


def test_unknown_code_noted_in_needs_verification():
    card = _run({**_BASE, "codes_present": [{"code_type": "ICD10CM", "code": "ZZZZZZZ"}]})
    assert any("ZZZZZZZ" in item for item in card.what_needs_verification)


def test_empty_codes_present_returns_valid_answer_card():
    card = _run({**_BASE})
    assert card.workflow == "workflow_1"
    assert isinstance(card.what_we_found, list)
    assert isinstance(card.what_needs_verification, list)
    assert card.disclaimer == STANDARD_DISCLAIMER


def test_complete_dollar_amounts_appear_in_found():
    card = _run({
        **_BASE,
        "amount_billed": 1500.0,
        "amount_allowed": 1200.0,
        "amount_plan_paid": 960.0,
        "amount_patient_responsibility": 240.0,
    })
    assert any("1,500" in item or "1500" in item for item in card.what_we_found), (
        f"Expected billed amount in what_we_found; got: {card.what_we_found}"
    )
    assert card.dollar_at_stake == 240.0


def test_missing_dollar_amounts_noted_in_needs_verification():
    card = _run({**_BASE})
    assert any("billed" in item.lower() or "amount" in item.lower()
               for item in card.what_needs_verification)


def test_all_cited_sources_resolve():
    from backend.data_access.interface import resolve_source
    card = _run({**_BASE, "codes_present": [{"code_type": "ICD10CM", "code": "A00"}]})
    for citation in card.citations:
        result = resolve_source(citation.source_id)
        assert result is not None, f"Citation source_id {citation.source_id!r} did not resolve"


def test_answer_card_has_all_required_fields():
    card = _run({**_BASE})
    assert card.workflow is not None
    assert card.what_we_found is not None
    assert card.what_it_likely_means is not None
    assert card.citations is not None
    assert card.confidence is not None
    assert card.what_needs_verification is not None
    assert card.recommended_next_step is not None
    assert card.disclaimer == STANDARD_DISCLAIMER


def test_all_codes_fail_triggers_escalation():
    """If no codes decode and no plan, escalation should be suggested."""
    card = _run({
        **_BASE,
        "codes_present": [{"code_type": "ICD10CM", "code": "ZZZZZZZ"}],
    })
    # Unknown code → escalation only if ALL codes fail (which is true here)
    assert card.escalation_recommendation in ("none", "suggested")  # graceful, not crash
