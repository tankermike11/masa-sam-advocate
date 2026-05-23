"""
Report generation for the eval harness (PRD §14, §16).

The population caveat from PRD §14 must appear in every report.
"""

from __future__ import annotations

import json
from datetime import datetime

from eval.harness import EvalResults

POPULATION_CAVEAT = (
    "The use cases were mined from CFPB complaints and Reddit, which skew toward the "
    "general population and toward collections-heavy issues. MASA's members skew older "
    "(55+), Medicare/Medicare Advantage, and ambulance-centric. The eval therefore "
    "demonstrates *the engine works on complaint-derived cases* — it does not, on its "
    "own, demonstrate *the engine works for MASA's specific member population*. "
    "This caveat should be stated wherever eval results are reported; a MASA-representative "
    "test set is a recommended follow-on."
)

_TARGETS = {
    "metric_triage_accuracy":        ("Triage classification accuracy",         0.85,  ">=85%"),
    "metric_citation_validity":      ("Citation validity",                       1.00,  "100%"),
    "metric_code_decode_coverage":   ("Code-decode coverage (excl. CPT)",        0.95,  ">=95%"),
    "metric_nsa_correctness":        ("NSA rule-engine correctness",             1.00,  "100%"),
    "metric_ground_ambulance_rate":  ("Ground-ambulance node produces rate",     1.00,  "100%"),
    "metric_concrete_next_step":     ("Cases ending in concrete next step",      0.95,  ">=95%"),
    "metric_human_review_escalated": ("Human-review rules → escalation",         1.00,  "100%"),
    "metric_no_false_answer":        ("No false confident answer",               1.00,  "100%"),
}


def generate_report(results: EvalResults) -> str:
    """Return a Markdown eval report. Population caveat is always included."""
    lines: list[str] = []

    lines += [
        "# MASA SAM Eval Report",
        "",
        f"**Run:** {results.run_timestamp}  ",
        f"**Fixtures:** {results.total}  ",
        f"**Errors:** {sum(1 for c in results.cases if c.error)}",
        "",
        "---",
        "",
        "## POPULATION CAVEAT",
        "",
        POPULATION_CAVEAT,
        "",
        "---",
        "",
        "## Summary Metrics",
        "",
        "| Metric | Target | Actual | Status |",
        "|--------|--------|--------|--------|",
    ]

    for attr, (label, target, target_str) in _TARGETS.items():
        actual = getattr(results, attr)
        passed = actual >= target
        status = "✓" if passed else "✗"
        lines.append(f"| {label} | {target_str} | {actual:.1%} | {status} |")

    lines += ["", "---", "", "## Broker-Deck Metrics", ""]

    # Share of bills with identified errors (what_we_found has 2+ items = something found)
    identified = sum(
        1 for c in results.cases
        if c.answer_card and len(c.answer_card.get("what_we_found", [])) > 1
    )
    lines.append(f"- **Share of bills with identified issues:** {identified / max(results.total, 1):.1%} ({identified}/{results.total})")

    # Dollar exposure surfaced
    total_dollar = sum(
        c.answer_card.get("dollar_at_stake") or 0.0
        for c in results.cases
        if c.answer_card and c.answer_card.get("dollar_at_stake")
    )
    lines.append(f"- **Dollar exposure surfaced:** ${total_dollar:,.2f} across {results.total} cases")

    lines.append(f"- **Share of cases reaching a concrete next step:** {results.metric_concrete_next_step:.1%}")

    lines += ["", "---", "", "## Failures Requiring Attention", ""]

    failed = [
        c for c in results.cases
        if c.error
        or not c.scores.triage_correct
        or not c.scores.citations_valid
        or not c.scores.has_concrete_next_step
        or not c.scores.no_false_answer
    ]

    if failed:
        lines += [
            "| Fixture ID | Primary Need | Triage | Citations | Next Step | No False Ans | Error |",
            "|------------|--------------|--------|-----------|-----------|-------------|-------|",
        ]
        for c in failed[:50]:  # cap at 50 rows
            t = "✓" if c.scores.triage_correct else "✗"
            ci = "✓" if c.scores.citations_valid else "✗"
            ns = "✓" if c.scores.has_concrete_next_step else "✗"
            nf = "✓" if c.scores.no_false_answer else "✗"
            err = (c.error or "")[:60].replace("|", "/")
            lines.append(f"| {c.fixture_id} | {c.primary_need} | {t} | {ci} | {ns} | {nf} | {err} |")
        if len(failed) > 50:
            lines.append(f"_...and {len(failed) - 50} more_")
    else:
        lines.append("_No failures — all cases passed all automated checks._")

    lines += ["", "---", "", "## Case-Level Detail", "",
              "| Fixture ID | Primary Need | PRD Fit | Workflow | Triage | Cites | Next Step |",
              "|------------|--------------|---------|----------|--------|-------|-----------|"]

    for c in results.cases[:200]:  # cap for readability
        wf = (c.triage_result or {}).get("primary_workflow", "—")
        t = "✓" if c.scores.triage_correct else "✗"
        ci = "✓" if c.scores.citations_valid else "✗"
        ns = "✓" if c.scores.has_concrete_next_step else "✗"
        lines.append(f"| {c.fixture_id} | {c.primary_need[:30]} | {c.prd_fit} | {wf} | {t} | {ci} | {ns} |")

    if len(results.cases) > 200:
        lines.append(f"_...{len(results.cases) - 200} more cases omitted_")

    lines += [
        "", "---", "", "## Notes", "",
        f"- **Fixture source:** MASA_Use_Case_Coverage_Analysis.xlsx (stratified sample, seed=42)",
        f"- **Fixture count:** {results.total}",
        f"- **PRD Fit filter:** STRONG, MODERATE, PARTIAL rows only",
        f"- **State default:** FL (dataset has no state column)",
        f"- **LLM calls:** All still stubs (answer-card rendering is Python fallback, not LLM-polished)",
        f"- **NSA rules status:** All 59 rules are `status=draft`; all NSA determinations degrade to `human_review_required`",
        "",
        "> " + POPULATION_CAVEAT.replace("\n", " "),
        "",
    ]

    return "\n".join(lines)


def generate_json_report(results: EvalResults) -> dict:
    """Machine-readable report: all metrics + per-case scores (no full answer-card content)."""
    return {
        "run_timestamp": results.run_timestamp,
        "total_fixtures": results.total,
        "population_caveat": POPULATION_CAVEAT,
        "metrics": {
            attr: {
                "label": label,
                "target": target,
                "target_str": target_str,
                "actual": getattr(results, attr),
                "passed": getattr(results, attr) >= target,
            }
            for attr, (label, target, target_str) in _TARGETS.items()
        },
        "cases": [
            {
                "fixture_id": c.fixture_id,
                "primary_need": c.primary_need,
                "prd_fit": c.prd_fit,
                "expected_workflow": c.expected.get("__expected_primary_workflow"),
                "actual_workflow": (c.triage_result or {}).get("primary_workflow"),
                "scores": c.scores.model_dump(),
                "error": c.error,
            }
            for c in results.cases
        ],
    }
