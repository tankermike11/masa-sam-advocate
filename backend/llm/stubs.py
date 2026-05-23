"""
LLM call wrappers — Phase 0 stubs.

Exactly two LLM call types exist in this application (PRD §3.3, §11).
All other logic is deterministic. Phase 0 stubs raise NotImplementedError.
Phase 1+ replaces these with real implementations using a BAA-covered model endpoint.
"""


def map_intake(member_answers: dict) -> dict:
    """
    Intake mapping LLM call.

    Converts member free-text answers into the validated intake schema object.
    Output MUST be schema-validated before the rule engine runs (PRD §11).

    On timeout/API error: caller retries once, then falls back to direct
    structured intake per the graceful-degradation spec (PRD §12).

    Returns:
        Validated intake schema dict.
    """
    raise NotImplementedError("map_intake — implement in Phase 1+")


def render_answer_card(determination: dict) -> str:
    """
    Answer-card rendering LLM call.

    Converts a fully-formed determination object into the answer card (Markdown).
    MUST NOT introduce facts, citations, or determinations not present in
    the determination object (enforced in prompt and tested in eval, PRD §11).

    On timeout/API error: caller retries once, then falls back to the plain
    structured template per the graceful-degradation spec (PRD §12).

    Returns:
        Rendered answer card as a Markdown string.
    """
    raise NotImplementedError("render_answer_card — implement in Phase 1+")
