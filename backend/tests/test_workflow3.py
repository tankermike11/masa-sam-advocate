"""Tests for Workflow 3 — Document generation (Phase 3 gate: all 4 documents with valid citations)."""

from pathlib import Path

import pytest

from backend.data_access.interface import resolve_source
from backend.intake.schema import IntakeSubmission
from backend.triage.engine import triage
from backend.workflows.answer_card import STANDARD_DISCLAIMER
from backend.workflows.workflow3 import GeneratedDocument, run_workflow3
from backend.tests.fixtures.workflow3_fixtures import WORKFLOW3_FIXTURES

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


def _run(kwargs: dict) -> tuple:
    intake = IntakeSubmission(**kwargs)
    triage_result = triage(intake)
    return run_workflow3(intake, triage_result)


@pytest.mark.parametrize("intake_kwargs,expected", WORKFLOW3_FIXTURES)
def test_document_selection(intake_kwargs, expected):
    card, docs = _run(intake_kwargs)
    doc_types = {d.document_type for d in docs}

    for dt in expected.get("document_types_include", []):
        assert dt in doc_types, f"Expected document type {dt!r}; got {doc_types}"

    for dt in expected.get("document_types_exclude", []):
        assert dt not in doc_types, f"Document type {dt!r} should NOT be generated; got {doc_types}"


def test_itemized_bill_request_generates():
    _, docs = _run({**_BASE, "amount_billed": 500.0,
                    "codes_present": [{"code_type": "ICD10CM", "code": "A00"}]})
    types = {d.document_type for d in docs}
    assert "itemized_bill_request" in types


def test_internal_appeal_generates_for_denial():
    _, docs = _run({**_BASE, "denial_present": True, "denial_codes": ["1"]})
    types = {d.document_type for d in docs}
    assert "internal_appeal" in types


def test_balance_bill_dispute_generates_for_balance_bill():
    _, docs = _run({**_BASE, "problem_type": "balance_bill", "amount_billed": 1800.0})
    types = {d.document_type for d in docs}
    assert "balance_bill_dispute" in types


def test_ppdr_initiation_generates_for_self_pay_with_gfe():
    _, docs = _run({
        **_BASE,
        "insurance_situation": "uninsured_self_pay",
        "problem_type": "surprise_out_of_network",
        "gfe_received": True,
        "gfe_expected_charges": [{"provider_name": "Provider A", "expected_charge": 900.0}],
        "amount_billed": 1800.0,
    })
    types = {d.document_type for d in docs}
    assert "ppdr_initiation" in types


def test_all_document_citations_resolve():
    """Gate test: every cited source_id in every document must resolve."""
    _, docs = _run({
        **_BASE,
        "denial_present": True,
        "denial_codes": ["1"],
        "problem_type": "balance_bill",
    })
    for doc in docs:
        for citation in doc.citations:
            result = resolve_source(citation.source_id)
            assert result is not None, (
                f"Citation source_id {citation.source_id!r} in {doc.document_type} "
                f"did not resolve — check pilot.db sources table"
            )


def test_counsel_required_on_all_documents():
    _, docs = _run({**_BASE})
    for doc in docs:
        assert doc.counsel_required is True, (
            f"Document {doc.document_type!r} missing counsel_required=True"
        )


def test_standard_disclaimer_in_all_documents():
    _, docs = _run({**_BASE})
    for doc in docs:
        assert STANDARD_DISCLAIMER in doc.disclaimer or STANDARD_DISCLAIMER in doc.content, (
            f"Document {doc.document_type!r} missing STANDARD_DISCLAIMER"
        )


def test_answer_card_has_all_required_fields():
    card, _ = _run({**_BASE})
    assert card.workflow == "workflow_3"
    assert card.what_we_found
    assert card.what_it_likely_means
    assert card.what_needs_verification
    assert card.recommended_next_step
    assert card.disclaimer == STANDARD_DISCLAIMER


def test_no_ppdr_without_gfe_received():
    _, docs = _run({
        **_BASE,
        "insurance_situation": "uninsured_self_pay",
        "problem_type": "surprise_out_of_network",
        "gfe_received": False,
    })
    types = {d.document_type for d in docs}
    assert "ppdr_initiation" not in types


def test_answer_card_lists_generated_documents():
    card, docs = _run({**_BASE, "denial_present": True})
    combined = " ".join(card.what_we_found)
    assert any("document" in item.lower() for item in card.what_we_found)
