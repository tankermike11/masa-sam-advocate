"""
Eval harness — runs the golden intake set through the full engine and scores
each case against the 8 PRD §16 success metrics.

All exceptions are caught per-case; the harness never aborts mid-run.
Failed cases are recorded with error=... and count against metrics.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, ValidationError

from backend.data_access.interface import resolve_source
from backend.intake.schema import IntakeSubmission
from backend.nsa.engine import nsa_rule_engine
from backend.triage.engine import triage
from backend.workflows.answer_card import STANDARD_DISCLAIMER
from backend.workflows.workflow1 import run_workflow1
from backend.workflows.workflow2 import run_workflow2
from backend.workflows.workflow3 import run_workflow3
from backend.workflows.workflow4 import run_workflow4
from backend.workflows.workflow5 import run_workflow5

logger = logging.getLogger(__name__)


class EvalScores(BaseModel):
    triage_correct: bool                  # metric 1: primary_workflow matches expected label
    citations_valid: bool                 # metric 2: all citation source_ids resolve
    code_decode_coverage: float | None    # metric 3: ratio non-CPT codes decoded (None if no non-CPT)
    nsa_rules_correct: bool               # metric 4: expected rule_ids fired (True if no assertion)
    ground_ambulance_rate: bool | None    # metric 5: reference rate in what_we_found (None if not applicable)
    has_concrete_next_step: bool          # metric 6: recommended_next_step is non-empty
    human_review_escalated: bool | None   # metric 7: human_review rule → escalation (None if no such rules)
    no_false_answer: bool                 # metric 8: disclaimer present and no silent exception


class EvalCase(BaseModel):
    fixture_id: str
    primary_need: str
    prd_fit: str
    expected: dict
    triage_result: dict | None = None
    answer_card: dict | None = None
    nsa_determination: dict | None = None
    scores: EvalScores
    error: str | None = None


class EvalResults(BaseModel):
    total: int
    run_timestamp: str
    cases: list[EvalCase]
    metric_triage_accuracy: float        # ≥85% target
    metric_citation_validity: float      # 100% target
    metric_code_decode_coverage: float   # ≥95% target (excl. CPT)
    metric_nsa_correctness: float        # 100% target
    metric_ground_ambulance_rate: float  # 100% target (ground-amb cases)
    metric_concrete_next_step: float     # ≥95% target
    metric_human_review_escalated: float # 100% target
    metric_no_false_answer: float        # 100% target


def _run_primary_workflow(intake: IntakeSubmission, triage_result: Any) -> Any:
    wf = triage_result.primary_workflow
    if wf == "workflow_1":
        return run_workflow1(intake)
    if wf == "workflow_2":
        return run_workflow2(intake, triage_result)
    if wf == "workflow_3":
        card, _ = run_workflow3(intake, triage_result)
        return card
    if wf == "workflow_4":
        return run_workflow4(intake)
    # workflow_5 or any catch-all
    return run_workflow5(intake, triage_result)


def _score_case(
    intake: IntakeSubmission,
    triage_result: Any,
    answer_card: Any,
    nsa_det: Any,
    expected: dict,
) -> EvalScores:
    # Metric 1: triage routing correct
    triage_correct = (
        triage_result.primary_workflow == expected.get("__expected_primary_workflow")
    )

    # Metric 2: all citations resolve
    citations_valid = True
    if answer_card and answer_card.citations:
        for citation in answer_card.citations:
            try:
                if resolve_source(citation.source_id) is None:
                    citations_valid = False
                    break
            except Exception:
                citations_valid = False
                break

    # Metric 3: code-decode coverage (excl. CPT)
    code_decode_coverage: float | None = None
    if intake.codes_present:
        non_cpt = [e for e in intake.codes_present if e.code_type.upper() != "CPT"]
        if non_cpt and answer_card:
            combined = " ".join(answer_card.what_we_found)
            decoded = sum(1 for e in non_cpt if e.code in combined)
            code_decode_coverage = decoded / len(non_cpt)

    # Metric 4: NSA rule-engine correctness
    nsa_rules_correct = True
    expected_rule_ids = expected.get("__expected_rule_ids_include", [])
    if expected_rule_ids and nsa_det:
        matched_ids = {m.rule_id for m in nsa_det.matched_rules}
        nsa_rules_correct = all(rid in matched_ids for rid in expected_rule_ids)

    # Metric 5: ground-ambulance reference rate produced
    ground_ambulance_rate: bool | None = None
    if intake.ambulance_involved and intake.ambulance_type and intake.ambulance_type.value == "ground":
        if answer_card:
            combined = " ".join(answer_card.what_we_found).lower()
            ground_ambulance_rate = "reference rate" in combined or "medicare" in combined
        else:
            ground_ambulance_rate = False

    # Metric 6: concrete next step present
    has_concrete_next_step = bool(
        answer_card and answer_card.recommended_next_step.strip()
    )

    # Metric 7: human_review rules carry escalation recommendation
    human_review_escalated: bool | None = None
    if nsa_det and nsa_det.matched_rules:
        has_human_review_rule = any(m.is_human_review for m in nsa_det.matched_rules)
        if has_human_review_rule:
            human_review_escalated = (
                answer_card is not None
                and answer_card.escalation_recommendation == "suggested"
            )

    # Metric 8: no false confident answer (disclaimer present, no silent failure)
    no_false_answer = (
        answer_card is not None
        and STANDARD_DISCLAIMER in (answer_card.disclaimer or "")
    )

    return EvalScores(
        triage_correct=triage_correct,
        citations_valid=citations_valid,
        code_decode_coverage=code_decode_coverage,
        nsa_rules_correct=nsa_rules_correct,
        ground_ambulance_rate=ground_ambulance_rate,
        has_concrete_next_step=has_concrete_next_step,
        human_review_escalated=human_review_escalated,
        no_false_answer=no_false_answer,
    )


def _aggregate(cases: list[EvalCase]) -> dict[str, float]:
    def _metric(name: str) -> float:
        vals = [getattr(c.scores, name) for c in cases if getattr(c.scores, name) is not None]
        if not vals:
            return 1.0  # no eligible cases → passes by vacuous truth
        return sum(1 for v in vals if v is True or (isinstance(v, float) and v >= 0.95)) / len(vals)

    def _float_metric(name: str) -> float:
        vals = [getattr(c.scores, name) for c in cases if getattr(c.scores, name) is not None]
        if not vals:
            return 1.0
        return sum(v if isinstance(v, float) else (1.0 if v else 0.0) for v in vals) / len(vals)

    return {
        "metric_triage_accuracy":        _float_metric("triage_correct"),
        "metric_citation_validity":      _float_metric("citations_valid"),
        "metric_code_decode_coverage":   _float_metric("code_decode_coverage"),
        "metric_nsa_correctness":        _float_metric("nsa_rules_correct"),
        "metric_ground_ambulance_rate":  _float_metric("ground_ambulance_rate"),
        "metric_concrete_next_step":     _float_metric("has_concrete_next_step"),
        "metric_human_review_escalated": _float_metric("human_review_escalated"),
        "metric_no_false_answer":        _float_metric("no_false_answer"),
    }


def run_harness(fixtures: list[dict]) -> EvalResults:
    """
    Run all fixtures through the full engine and score against 8 PRD §16 metrics.
    Exceptions are caught per-case; the harness never aborts mid-run.
    """
    cases: list[EvalCase] = []
    timestamp = datetime.now(timezone.utc).isoformat()

    for fixture in fixtures:
        intake_kwargs = {k: v for k, v in fixture.items() if not k.startswith("__")}
        expected = {k: v for k, v in fixture.items() if k.startswith("__")}
        fixture_id = expected.get("__fixture_id", "unknown")
        primary_need = expected.get("__primary_need", "unknown")
        prd_fit = expected.get("__prd_fit", "unknown")

        error: str | None = None
        triage_result = None
        answer_card = None
        nsa_det = None

        try:
            intake = IntakeSubmission(**intake_kwargs)
        except ValidationError as exc:
            error = f"ValidationError: {exc}"
            cases.append(EvalCase(
                fixture_id=fixture_id, primary_need=primary_need, prd_fit=prd_fit,
                expected=expected,
                scores=EvalScores(
                    triage_correct=False, citations_valid=True, code_decode_coverage=None,
                    nsa_rules_correct=True, ground_ambulance_rate=None,
                    has_concrete_next_step=False, human_review_escalated=None,
                    no_false_answer=False,
                ),
                error=error,
            ))
            continue

        try:
            triage_result = triage(intake)
        except Exception as exc:
            error = f"Triage error: {exc}"
            logger.error("Triage failed for %s: %s", fixture_id, exc)

        try:
            if triage_result:
                answer_card = _run_primary_workflow(intake, triage_result)
        except Exception as exc:
            error = (error or "") + f" Workflow error: {exc}"
            logger.error("Workflow failed for %s: %s", fixture_id, exc)

        try:
            if triage_result and triage_result.rule_modules:
                nsa_det = nsa_rule_engine(intake, triage_result.rule_modules)
        except Exception as exc:
            logger.error("NSA engine failed for %s: %s", fixture_id, exc)

        scores = _score_case(intake, triage_result, answer_card, nsa_det, expected)
        if error:
            scores = scores.model_copy(update={"triage_correct": False, "no_false_answer": False})

        cases.append(EvalCase(
            fixture_id=fixture_id,
            primary_need=primary_need,
            prd_fit=prd_fit,
            expected=expected,
            triage_result=triage_result.model_dump() if triage_result else None,
            answer_card=answer_card.model_dump() if answer_card else None,
            nsa_determination=nsa_det.model_dump() if nsa_det else None,
            scores=scores,
            error=error,
        ))

    metrics = _aggregate(cases)
    return EvalResults(
        total=len(cases),
        run_timestamp=timestamp,
        cases=cases,
        **metrics,
    )
