"""Triage routing tests against the curated fixture set (Phase 1 gate)."""

import pytest

from backend.intake.schema import IntakeSubmission
from backend.triage.engine import triage
from backend.tests.fixtures.triage_fixtures import FIXTURES


@pytest.mark.parametrize("intake_kwargs,expected", FIXTURES)
def test_triage_routing(intake_kwargs: dict, expected: dict) -> None:
    intake = IntakeSubmission(**intake_kwargs)
    result = triage(intake)

    assert result.primary_workflow == expected["primary_workflow"], (
        f"primary_workflow: expected {expected['primary_workflow']!r}, "
        f"got {result.primary_workflow!r} | intake: {intake_kwargs}"
    )

    for cat in expected.get("rule_modules_include", []):
        assert cat in result.rule_modules, (
            f"Category '{cat}' must be in rule_modules {result.rule_modules}"
        )

    for cat in expected.get("rule_modules_exclude", []):
        assert cat not in result.rule_modules, (
            f"Category '{cat}' must NOT be in rule_modules {result.rule_modules}"
        )

    if "severity" in expected:
        assert result.severity == expected["severity"], (
            f"severity: expected {expected['severity']!r}, got {result.severity!r}"
        )

    if "escalation_recommendation" in expected:
        assert result.escalation_recommendation == expected["escalation_recommendation"], (
            f"escalation_recommendation: expected {expected['escalation_recommendation']!r}, "
            f"got {result.escalation_recommendation!r}"
        )

    for reason in expected.get("escalation_reasons_include", []):
        assert reason in result.escalation_reasons, (
            f"Reason '{reason}' must be in escalation_reasons {result.escalation_reasons}"
        )
