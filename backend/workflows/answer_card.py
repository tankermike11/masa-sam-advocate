"""
Output contract — answer-card format (PRD §7).

Every workflow produces one AnswerCard. The six sections map directly to the PRD spec.
Cited facts and labeled interpretation are kept visibly separate (UPL safety boundary).

In Phase 2 the LLM rendering stub is not yet implemented; render_fallback() is the
actual output rendered for members. It produces readable Markdown from the structured
determination. The LLM call (Phase 2+) will replace this with polished prose without
changing any facts, citations, or determinations.
"""

from __future__ import annotations

import logging

from pydantic import BaseModel, Field

from backend.data_access.interface import resolve_source

logger = logging.getLogger(__name__)

STANDARD_DISCLAIMER = (
    "This information is for self-help and educational purposes only. "
    "It is not legal advice or licensed insurance advice. "
    "Protection determinations are preliminary and not a definitive legal conclusion. "
    "Consult a qualified professional before acting on this information."
)


class Citation(BaseModel):
    source_id: str
    publisher: str | None = None
    canonical_url: str | None = None


class AnswerCard(BaseModel):
    workflow: str                                      # "workflow_1" | "workflow_2"
    what_we_found: list[str] = Field(default_factory=list)    # cited facts
    what_it_likely_means: list[str] = Field(default_factory=list)  # interpretation only
    citations: list[Citation] = Field(default_factory=list)
    confidence: dict[str, str] = Field(default_factory=dict)  # field → high/medium/low/unknown
    what_needs_verification: list[str] = Field(default_factory=list)
    recommended_next_step: str = ""
    dollar_at_stake: float | None = None
    escalation_recommendation: str = "none"            # "none" | "suggested"
    disclaimer: str = STANDARD_DISCLAIMER


def build_citations(source_ids: list[str]) -> list[Citation]:
    """Resolve source IDs to Citation objects; silently skips unresolvable IDs."""
    seen: set[str] = set()
    citations: list[Citation] = []
    for sid in source_ids:
        if sid in seen:
            continue
        seen.add(sid)
        try:
            source = resolve_source(sid)
        except Exception as exc:
            logger.warning("resolve_source(%r) failed: %s", sid, exc)
            source = None
        if source:
            citations.append(Citation(
                source_id=source["source_id"],
                publisher=source.get("publisher"),
                canonical_url=source.get("canonical_url"),
            ))
    return citations


def render_fallback(card: AnswerCard) -> str:
    """
    Plain Markdown renderer for Phase 2.

    Produces a readable, structured block covering all six answer-card sections.
    Replaces LLM rendering until the LLM call is implemented.
    """
    lines: list[str] = [
        f"## {card.workflow.replace('_', ' ').title()} — Advocacy Assessment",
        "",
        "### What We Found",
    ]
    lines += [f"- {item}" for item in card.what_we_found] or ["- No findings available."]
    lines += [
        "",
        "### What It Likely Means",
        "*The following is interpretation, not legal or insurance advice.*",
    ]
    lines += [f"- {item}" for item in card.what_it_likely_means] or ["- No interpretation available."]
    lines.append("")

    if card.citations:
        lines.append("### Citations")
        for c in card.citations:
            url = f" — {c.canonical_url}" if c.canonical_url else ""
            lines.append(f"- [{c.publisher or c.source_id}] ({c.source_id}{url})")
        lines.append("")

    if card.confidence:
        lines.append("### Confidence")
        for field, level in card.confidence.items():
            lines.append(f"- {field}: {level}")
        lines.append("")

    if card.what_needs_verification:
        lines.append("### What Still Needs Verification")
        lines += [f"- {item}" for item in card.what_needs_verification]
        lines.append("")

    if card.dollar_at_stake is not None:
        lines += [f"**Dollar at stake:** ${card.dollar_at_stake:,.2f}", ""]

    lines += [
        "### Recommended Next Step",
        card.recommended_next_step or "No specific next step identified; consider escalation.",
        "",
        "---",
        f"*{card.disclaimer}*",
    ]
    return "\n".join(lines)
