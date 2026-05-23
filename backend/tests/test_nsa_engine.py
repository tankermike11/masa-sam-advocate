"""Tests for the NSA rule engine (PRD §6.7)."""

import pytest

from backend.intake.schema import IntakeSubmission
from backend.nsa.engine import nsa_rule_engine
from backend.nsa.predicates import PREDICATES
from backend.tests.fixtures.nsa_fixtures import NSA_FIXTURES

# All rule_ids that must be registered in PREDICATES
_EXPECTED_RULE_IDS = [
    "NSA-FED-001", "NSA-FED-002", "NSA-FED-003", "NSA-FED-004",
    "NSA-EMERG-001", "NSA-EMERG-002", "NSA-EMERG-003", "NSA-EMERG-004",
    "NSA-EMERG-005", "NSA-EMERG-006",
    "NSA-NONEMERG-001", "NSA-NONEMERG-002", "NSA-NONEMERG-003",
    "NSA-NONEMERG-004", "NSA-NONEMERG-005",
    "NSA-CONSENT-001", "NSA-CONSENT-002", "NSA-CONSENT-003",
    "NSA-CONSENT-004", "NSA-CONSENT-005",
    "NSA-NONWAIVE-001", "NSA-NONWAIVE-002",
    "NSA-DISCLOSURE-001", "NSA-DISCLOSURE-002", "NSA-DISCLOSURE-003",
    "NSA-AIR-001", "NSA-AIR-002", "NSA-AIR-003", "NSA-AIR-004",
    "GFE-001", "GFE-002", "GFE-003", "GFE-004", "GFE-005", "GFE-006", "GFE-007",
    "PPDR-001", "PPDR-002", "PPDR-003", "PPDR-004", "PPDR-005",
    "PPDR-006", "PPDR-007", "PPDR-008",
    "STATE-ROUTE-001", "STATE-ROUTE-002", "STATE-ROUTE-003", "STATE-ROUTE-004",
    "GROUND-001", "GROUND-002", "GROUND-003", "GROUND-004", "GROUND-005",
    "GROUND-006", "GROUND-007", "GROUND-008", "GROUND-009", "GROUND-010", "GROUND-011",
]


def test_all_rule_ids_have_predicates():
    """Every rule_id used in pilot.db must have a registered predicate."""
    missing = [rid for rid in _EXPECTED_RULE_IDS if rid not in PREDICATES]
    assert not missing, f"Missing predicates for: {missing}"


def test_total_predicate_count():
    assert len(PREDICATES) == 59


def test_empty_rule_modules_returns_empty_determination():
    intake = IntakeSubmission(
        insurance_situation="commercial_employer", state="FL", problem_type="clean_denial"
    )
    det = nsa_rule_engine(intake, [])
    assert det.matched_rules == []
    assert det.actions == []
    assert det.escalation_recommendation == "none"


def test_draft_rules_always_produce_human_review_required():
    intake = IntakeSubmission(
        insurance_situation="commercial_employer", state="FL",
        problem_type="surprise_out_of_network",
        ambulance_involved=True, ambulance_type="ground",
    )
    det = nsa_rule_engine(intake, ["K"])
    assert det.protection_determination == "human_review_required"
    assert det.has_counsel_approved_rules is False


def test_draft_rules_always_escalate():
    intake = IntakeSubmission(
        insurance_situation="commercial_employer", state="FL",
        problem_type="surprise_out_of_network",
    )
    det = nsa_rule_engine(intake, ["A", "B"])
    assert det.escalation_recommendation == "suggested"
    assert "no_counsel_approved_rules" in det.escalation_reasons


def test_predicate_exception_treated_as_human_review(monkeypatch):
    """A predicate that raises must not produce 'no violation' — it triggers human_review."""
    def bad_predicate(intake):
        raise ValueError("simulated predicate failure")

    monkeypatch.setitem(PREDICATES, "GROUND-001", bad_predicate)
    intake = IntakeSubmission(
        insurance_situation="commercial_employer", state="FL",
        problem_type="surprise_out_of_network",
        ambulance_involved=True, ambulance_type="ground",
    )
    det = nsa_rule_engine(intake, ["K"])
    exception_rules = [m for m in det.matched_rules if m.predicate_exception]
    assert any(m.rule_id == "GROUND-001" for m in exception_rules)
    assert det.escalation_recommendation == "suggested"
    assert "predicate_evaluation_failed" in det.escalation_reasons


@pytest.mark.parametrize("intake_kwargs,rule_modules,expected", NSA_FIXTURES)
def test_nsa_engine_routing(intake_kwargs, rule_modules, expected):
    intake = IntakeSubmission(**intake_kwargs)
    det = nsa_rule_engine(intake, rule_modules)

    matched_ids = {m.rule_id for m in det.matched_rules}

    for rid in expected.get("rule_ids_include", []):
        assert rid in matched_ids, (
            f"Expected rule {rid!r} in matched_rules; got {sorted(matched_ids)}"
        )

    if "escalation_recommendation" in expected:
        assert det.escalation_recommendation == expected["escalation_recommendation"]

    if "has_counsel_approved_rules" in expected:
        assert det.has_counsel_approved_rules == expected["has_counsel_approved_rules"]

    if "protection_determination" in expected:
        assert det.protection_determination == expected["protection_determination"]
