"""
Eval harness gate tests (PRD §15 Phase 5 gate).

Requires both pilot.db and MASA_Use_Case_Coverage_Analysis.xlsx.
Uses a small slice of the golden set (first 10 fixtures) for speed.
"""

from pathlib import Path

import pytest

PILOT_DB_PATH = Path("data/pilot.db")
DATASET_PATH = Path("MASA_Use_Case_Coverage_Analysis.xlsx")

pytestmark = pytest.mark.skipif(
    not PILOT_DB_PATH.exists() or not DATASET_PATH.exists(),
    reason="pilot.db and MASA_Use_Case_Coverage_Analysis.xlsx both required",
)

from eval.golden_set import GOLDEN_FIXTURES
from eval.harness import EvalResults, EvalScores, run_harness
from eval.report import POPULATION_CAVEAT, generate_report, generate_json_report
from backend.intake.schema import IntakeSubmission


# ── Dataset and fixture structure ─────────────────────────────────────────────

def test_golden_fixtures_loaded():
    assert len(GOLDEN_FIXTURES) > 0, "GOLDEN_FIXTURES is empty — check xlsx path"


def test_fixture_count_at_least_50():
    assert len(GOLDEN_FIXTURES) >= 50, f"Expected ≥50 fixtures; got {len(GOLDEN_FIXTURES)}"


def test_fixture_ids_unique():
    ids = [f.get("__fixture_id") for f in GOLDEN_FIXTURES]
    assert len(ids) == len(set(ids)), "Duplicate fixture IDs found"


def test_all_fixtures_produce_valid_intakesubmission():
    errors = []
    from pydantic import ValidationError
    for f in GOLDEN_FIXTURES:
        kwargs = {k: v for k, v in f.items() if not k.startswith("__")}
        try:
            IntakeSubmission(**kwargs)
        except ValidationError as exc:
            errors.append(f"{f.get('__fixture_id')}: {exc}")
    assert not errors, f"ValidationErrors in fixtures:\n" + "\n".join(errors[:5])


def test_all_fixtures_have_expected_labels():
    for f in GOLDEN_FIXTURES:
        fid = f.get("__fixture_id", "?")
        assert "__expected_primary_workflow" in f, f"Missing __expected_primary_workflow in {fid}"
        assert "__expected_problem_type" in f,     f"Missing __expected_problem_type in {fid}"


# ── Harness run (small slice for speed) ─────────────────────────────���────────

_SAMPLE = GOLDEN_FIXTURES[:10]


def test_harness_runs_without_unhandled_exception():
    results = run_harness(_SAMPLE)
    assert isinstance(results, EvalResults)
    assert results.total == len(_SAMPLE)


def test_all_8_metric_fields_present():
    results = run_harness(_SAMPLE)
    assert hasattr(results, "metric_triage_accuracy")
    assert hasattr(results, "metric_citation_validity")
    assert hasattr(results, "metric_code_decode_coverage")
    assert hasattr(results, "metric_nsa_correctness")
    assert hasattr(results, "metric_ground_ambulance_rate")
    assert hasattr(results, "metric_concrete_next_step")
    assert hasattr(results, "metric_human_review_escalated")
    assert hasattr(results, "metric_no_false_answer")


def test_no_false_answers_100pct():
    """Gate: no failure mode produces a false confident answer (PRD §16)."""
    results = run_harness(_SAMPLE)
    assert results.metric_no_false_answer == 1.0, (
        f"metric_no_false_answer = {results.metric_no_false_answer:.1%}; expected 100%"
    )


def test_citation_validity_100pct():
    """Gate: every cited fact resolves to a real source (PRD §16)."""
    results = run_harness(_SAMPLE)
    assert results.metric_citation_validity == 1.0, (
        f"metric_citation_validity = {results.metric_citation_validity:.1%}; expected 100%"
    )


def test_concrete_next_step_gte_95pct():
    """Gate: ≥95% of cases end in a concrete next step (PRD §16)."""
    results = run_harness(_SAMPLE)
    assert results.metric_concrete_next_step >= 0.95, (
        f"metric_concrete_next_step = {results.metric_concrete_next_step:.1%}; expected ≥95%"
    )


def test_triage_accuracy_reported():
    results = run_harness(_SAMPLE)
    # Just verify it's a float in [0,1]; target ≥85% is verified by run_eval.py
    assert 0.0 <= results.metric_triage_accuracy <= 1.0


# ── Report generation ─────────────────────────────────────────────────────────

def test_population_caveat_in_report():
    results = run_harness(_SAMPLE)
    report = generate_report(results)
    assert "CFPB complaints and Reddit" in report, "Population caveat missing from report"
    assert "55+" in report, "MASA member demographic missing from report"


def test_report_contains_all_8_metric_labels():
    results = run_harness(_SAMPLE)
    report = generate_report(results)
    for label in [
        "Triage classification accuracy",
        "Citation validity",
        "Code-decode coverage",
        "NSA rule-engine correctness",
        "Ground-ambulance node",
        "concrete next step",
        "Human-review rules",
        "false confident",
    ]:
        assert label.lower() in report.lower(), f"Metric label missing from report: {label!r}"


def test_json_report_structure():
    results = run_harness(_SAMPLE)
    json_data = generate_json_report(results)
    assert "metrics" in json_data
    assert "cases" in json_data
    assert "population_caveat" in json_data
    assert len(json_data["cases"]) == len(_SAMPLE)
    assert all("scores" in c for c in json_data["cases"])
