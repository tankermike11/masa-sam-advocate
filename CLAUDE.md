# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project directive

This project is built strictly per `docs/PRD.md` (SAM Medical Bill Advocate, PRD v1.2).
Repo layout, conventions, phases, and scope are defined there — follow it phase by phase.
Build one PRD phase per planning cycle; do not skip ahead. **Phase 0 is a hard gate.**

## Development commands

### Backend (FastAPI, Python 3.12.x)

```bash
# Install dependencies
cd backend && pip install -r requirements.txt

# Run the dev server
uvicorn backend.main:app --reload

# Run all tests
pytest

# Run a single test file
pytest backend/tests/test_triage.py

# Run eval harness
python eval/run_eval.py
```

### Frontend (React + TypeScript)

```bash
cd frontend
npm install
npm run dev        # dev server
npm run build      # production build
npm run typecheck  # type-check without building
npm test           # run tests
```

## Architecture

### Component overview

```
masa-sam-advocate/
├── backend/          FastAPI app
│   ├── data_access/  Clean DB interface (lookup_code, search_plan, get_ambulance_reference_rate, etc.)
│   ├── triage/       Triage engine — axes evaluation, routing, escalation flags
│   ├── workflows/    One module per workflow (1–5) + NSA rule engine
│   ├── documents/    Parameterized document templates (4 types)
│   ├── escalation/   Case service — creates/reads from app.db
│   └── llm/          LLM call wrappers (intake mapping + answer-card rendering)
├── frontend/         React + TypeScript chat-style interface
├── config/           pricing_rules.yaml, escalation_rules.yaml
├── eval/             Golden intake set (~150 fixtures) + harness
└── data/             pilot.db (read-only snapshot) + app.db (case store) — gitignored
```

### Two databases, strict roles

- **`data/pilot.db`** — read-only build input. The app **never writes to it**. Drop a fresh snapshot here when the data layer updates.
- **`data/app.db`** — app-owned case store. The only database the app writes to. Managed by the escalation/case service.

### Data-access module is the only SQL layer

Workflows and the rule engine never run SQL. They call the data-access interface:
`lookup_code()`, `search_plan()`, `get_sbc_fields()`, `get_ambulance_reference_rate()`, `get_nsa_rules()`, `resolve_source()`.
This keeps the SQLite backend swappable to live APIs without touching workflow logic.

### Triage engine — Axis 2 overrides Axis 1

Evaluate `insurance_situation` (Axis 2) **before** `problem_type` (Axis 1). `medicaid` short-circuits to Workflow 5 regardless of problem type. All other Axis-2 values proceed to the Axis-1 routing table. Triage output: `{ problem_type, insurance_situation, severity, advocacy_capacity, primary_workflow, rule_modules, escalation_recommendation, escalation_reasons }`.

### NSA rule engine

One engine, one `nsa_rules` table, categories A–K. `rule_modules` from triage selects which categories to evaluate. Each rule maps to a deterministic predicate: `predicates[rule_id](intake) -> bool`. Predicate exceptions degrade to `human_review`, never to "no violation found." Rules without `status = counsel_approved` may not drive a definitive UI determination.

### LLM boundary (enforced in code)

The LLM does two things only:
1. **Intake mapping** — converts member free-text answers into the validated intake schema object. Output is schema-validated before the rule engine runs.
2. **Answer-card rendering** — converts a fully-formed determination object into the answer card. May not introduce facts, citations, or determinations not present in the determination object.

The LLM is never the source of truth for code descriptors, NSA determinations, reference rates, deadlines, or citations — those come from the DB and rule engine.

### Answer-card format (output contract)

Every workflow produces this structure: **What we found** (cited) → **What it likely means** (labeled as interpretation) → **Citations** (all resolve via `resolve_source()`) → **Confidence** → **What still needs verification** → **Recommended next step** (with dollar figure where applicable).

### Escalation and case model

`app.db` case object: `case_id`, `created_at`, `intake`, `triage_result`, `workflow_outputs`, `generated_documents`, `escalation_status`, `gate_decision`. The escalation gate reads `pricing_rules.yaml` at request time — changing fees means editing the YAML, not the code.

### Graceful degradation rule

Every failure path degrades toward "we could not determine this — here is a human." A false confident answer is a worse outcome than an escalation. Specifically: DB errors surface in the answer card's "what still needs verification"; rule predicate exceptions become `human_review`; LLM failures retry once then fall back to unpolished structured output; unrecoverable workflow failures always offer escalation.

## Key constraints

- **Python 3.12.x** (pinned in `.python-version`) — independent of the data repo's Python version.
- **CPT codes are not in `pilot.db`** (AMA license required). Workflow 1 returns a category-level fallback for CPT lines. This is expected behavior, not a bug.
- **Monetary values** in Family A/B/F tables are raw strings — the data-access module parses them. Exception: `ambulance_fee_schedule.reference_rate` is stored as integer cents.
- **Document templates require counsel sign-off** before any real member sees output (§13 of PRD). During the prototype build, this is a parallel track.
- **`pilot.db` is gitignored** (455 MB binary). A snapshot must be copied to `data/pilot.db` manually before running the app.
