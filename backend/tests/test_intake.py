"""Tests for the structured intake schema (PRD §5)."""

import pytest
from pydantic import ValidationError

from backend.intake.schema import (
    AdvocacyCapacity,
    InsuranceSituation,
    IntakeSubmission,
    PlanFundingType,
    ProblemType,
)

_REQUIRED = {
    "insurance_situation": "commercial_employer",
    "state": "FL",
    "problem_type": "clean_denial",
}


def test_required_fields_accepted():
    intake = IntakeSubmission(**_REQUIRED)
    assert intake.insurance_situation == InsuranceSituation.commercial_employer
    assert intake.state == "FL"
    assert intake.problem_type == ProblemType.clean_denial


def test_missing_insurance_situation_raises():
    with pytest.raises(ValidationError):
        IntakeSubmission(state="FL", problem_type="clean_denial")


def test_missing_state_raises():
    with pytest.raises(ValidationError):
        IntakeSubmission(insurance_situation="commercial_employer", problem_type="clean_denial")


def test_missing_problem_type_raises():
    with pytest.raises(ValidationError):
        IntakeSubmission(insurance_situation="commercial_employer", state="FL")


def test_advocacy_capacity_defaults_to_needs_hand_holding():
    intake = IntakeSubmission(**_REQUIRED)
    assert intake.advocacy_capacity == AdvocacyCapacity.needs_hand_holding


def test_state_normalized_to_uppercase():
    intake = IntakeSubmission(**{**_REQUIRED, "state": "fl"})
    assert intake.state == "FL"


def test_state_too_long_raises():
    with pytest.raises(ValidationError):
        IntakeSubmission(**{**_REQUIRED, "state": "FLA"})


def test_state_non_alpha_raises():
    with pytest.raises(ValidationError):
        IntakeSubmission(**{**_REQUIRED, "state": "F1"})


def test_invalid_insurance_situation_raises():
    with pytest.raises(ValidationError):
        IntakeSubmission(**{**_REQUIRED, "insurance_situation": "not_a_value"})


def test_invalid_problem_type_raises():
    with pytest.raises(ValidationError):
        IntakeSubmission(**{**_REQUIRED, "problem_type": "not_a_value"})


def test_list_fields_default_to_empty():
    intake = IntakeSubmission(**_REQUIRED)
    assert intake.codes_present == []
    assert intake.denial_codes == []
    assert intake.gfe_expected_charges == []


def test_boolean_flags_default_false():
    intake = IntakeSubmission(**_REQUIRED)
    assert intake.denial_present is False
    assert intake.ambulance_involved is False
    assert intake.in_collections is False
    assert intake.is_masa_member is False


def test_dollar_amounts_default_none():
    intake = IntakeSubmission(**_REQUIRED)
    assert intake.amount_billed is None
    assert intake.amount_patient_responsibility is None


def test_plan_funding_type_defaults_unknown():
    intake = IntakeSubmission(**_REQUIRED)
    assert intake.plan_funding_type == PlanFundingType.unknown


def test_all_insurance_situation_values_valid():
    for val in InsuranceSituation:
        intake = IntakeSubmission(**{**_REQUIRED, "insurance_situation": val.value})
        assert intake.insurance_situation == val


def test_all_problem_type_values_valid():
    for val in ProblemType:
        intake = IntakeSubmission(**{**_REQUIRED, "problem_type": val.value})
        assert intake.problem_type == val
