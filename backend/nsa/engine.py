"""
NSA rule engine (PRD §6.7).

One engine, one nsa_rules table, categories A–K.
rule_modules from triage selects which categories to evaluate.

IMPORTANT: All 59 rules are currently status="draft" (no counsel_approved rows).
Per PRD §13, the engine runs correctly but every determination degrades to
"human_review_required" and carries escalation_recommendation="suggested".
This is correct behavior, not a bug.

Exception handling: predicate raises → treated as human_review, never as "no violation".
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from pydantic import BaseModel

from backend.data_access.interface import get_nsa_rules
from backend.nsa.predicates import PREDICATES

if TYPE_CHECKING:
    from backend.intake.schema import IntakeSubmission

logger = logging.getLogger(__name__)


class MatchedRule(BaseModel):
    rule_id: str
    category: str
    system_action: str
    citation: str | None
    status: str
    is_human_review: bool        # True if system_action contains "human review"
    predicate_exception: bool = False


class NSADetermination(BaseModel):
    rule_modules: list[str]
    matched_rules: list[MatchedRule]
    actions: list[str]               # deduplicated system_actions from matched rules
    protection_determination: str    # "likely_protected" | "not_protected" | "human_review_required"
    escalation_recommendation: str   # "none" | "suggested"
    escalation_reasons: list[str]
    has_counsel_approved_rules: bool  # always False until counsel review completed
    cited_sources: list[str]          # source_ids from matched rules


def _is_human_review(system_action: str) -> bool:
    return "human review" in system_action.lower()


def nsa_rule_engine(
    intake: "IntakeSubmission",
    rule_modules: list[str],
) -> NSADetermination:
    """
    Evaluate applicable NSA rules for the given intake.

    Returns NSADetermination. Predicate exceptions degrade the rule to human_review
    and never produce a "no violation" result.
    """
    if not rule_modules:
        return NSADetermination(
            rule_modules=[],
            matched_rules=[],
            actions=[],
            protection_determination="human_review_required",
            escalation_recommendation="none",
            escalation_reasons=[],
            has_counsel_approved_rules=False,
            cited_sources=[],
        )

    rules = get_nsa_rules(rule_modules)
    matched: list[MatchedRule] = []
    predicate_exceptions: list[str] = []

    for rule in rules:
        rule_id = rule["rule_id"]
        predicate = PREDICATES.get(rule_id)

        if predicate is None:
            logger.warning("No predicate registered for rule_id=%r; treating as human_review", rule_id)
            matched.append(MatchedRule(
                rule_id=rule_id,
                category=rule["category"],
                system_action=rule["system_action"] or "human_review",
                citation=rule.get("citation"),
                status=rule["status"],
                is_human_review=True,
                predicate_exception=False,
            ))
            continue

        try:
            fired = predicate(intake)
        except Exception as exc:
            logger.error(
                "Predicate for rule_id=%r raised %s: %s; treating as human_review",
                rule_id, type(exc).__name__, exc,
                exc_info=True,
            )
            matched.append(MatchedRule(
                rule_id=rule_id,
                category=rule["category"],
                system_action="Human review — predicate evaluation failed.",
                citation=rule.get("citation"),
                status=rule["status"],
                is_human_review=True,
                predicate_exception=True,
            ))
            predicate_exceptions.append(rule_id)
            continue

        if fired:
            matched.append(MatchedRule(
                rule_id=rule_id,
                category=rule["category"],
                system_action=rule["system_action"] or "",
                citation=rule.get("citation"),
                status=rule["status"],
                is_human_review=_is_human_review(rule["system_action"] or ""),
                predicate_exception=False,
            ))

    # Deduplicate actions (preserve order)
    seen_actions: set[str] = set()
    actions: list[str] = []
    for m in matched:
        if m.system_action and m.system_action not in seen_actions:
            seen_actions.add(m.system_action)
            actions.append(m.system_action)

    has_counsel_approved = any(m.status == "counsel_approved" for m in matched)
    has_human_review = any(m.is_human_review for m in matched)
    has_exception = bool(predicate_exceptions)

    # Escalation triggers (PRD §6.7 + §8.1)
    escalation_reasons: list[str] = []
    if has_human_review:
        escalation_reasons.append("human_review_rule_matched")
    if has_exception:
        escalation_reasons.append("predicate_evaluation_failed")
    if not has_counsel_approved:
        # All rules are draft → degrade to human review (PRD §13)
        escalation_reasons.append("no_counsel_approved_rules")

    escalation = "suggested" if escalation_reasons else "none"

    # Protection determination
    matched_ids = {m.rule_id for m in matched}
    if not has_counsel_approved:
        determination = "human_review_required"
    elif "GROUND-003" in matched_ids:
        determination = "not_protected"
    elif any("Explain likely NSA protection" in m.system_action for m in matched):
        determination = "likely_protected"
    else:
        determination = "human_review_required"

    cited_sources = list({rule["source_id"] for rule in rules if rule["source_id"]})

    return NSADetermination(
        rule_modules=rule_modules,
        matched_rules=matched,
        actions=actions,
        protection_determination=determination,
        escalation_recommendation=escalation,
        escalation_reasons=escalation_reasons,
        has_counsel_approved_rules=has_counsel_approved,
        cited_sources=cited_sources,
    )
