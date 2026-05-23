# MASA — SAM Medical Bill Advocate

## Prototype PRD v1.2

**Application & Triage Layer for AI-Assisted Medical Bill Advocacy**

Prepared for: Claude Code build — repository `masa-sam-advocate` (new)
Status: Build-ready
Companion documents: MASA Public Data Ingestion Layer PRD v1.1 (the data layer); MASA Public Data Ingestion Layer — Data Completion Addendum v1.3 (the three data-prep tasks this prototype depends on); SAM & AccessNow Strategy Document.

**Revision history**
- **v1.0 → v1.1** — Data-completion work moved to the companion Data Completion Addendum (executed in the `medical_billing_data` repository); ruleset updated from Tables A–J to A–K.
- **v1.1 → v1.2** — Review fixes: added the interaction model (§6.1), a graceful-degradation section (§12), the app-owned case store (§3.1), the `advocacy_capacity` intake field (§5.8), a reworked eval harness with an explicit golden set (§14), Medicaid routing precedence (§4.2/4.4), per-line vs. bill-level scope for Workflow 1 (§6.2), the CPT data limitation (§10), code search at intake (§5.2), a sub-$500 severity band (§4.3), and a pinned app Python version (§3.1).

---

## 1. Executive summary

This PRD specifies a working prototype of **SAM, the MASA Medical Bill Advocate** — a guided, member-facing advocacy tool that uses a chat-style interface over a structured triage and workflow engine. It is the application layer that sits on top of the Public Data Ingestion Layer. The data layer answers *what the codes and rules say*; this layer turns that into *advocacy* — a triaged assessment, a plain-English explanation, citation-backed reasoning, generated dispute documents, and a human-escalation path.

This is **Medical Bill Advocacy, not EOB interpretation**. Every interaction ends with a concrete next action and, where applicable, a dollar figure at stake. The ambulance / surprise-bill case is the sharpest entry wedge, but the advocacy logic is general and covers denials, underpayments, billing errors, balance bills, and collections. For framing: this advocacy logic sits **upstream of** MASA's ambulance gap coverage — it operates before MASA's "covers the gap above primary medical" benefit comes into play, and it applies far beyond transport.

### What the prototype is built to prove

1. That a guided advocate — structured triage + deterministic lookups + citation-backed explanation + human escalation — can resolve a real member's bill end-to-end.
2. That it produces, repeatably, the outcome metrics the broker/HR positioning deck needs (share of bills with identified errors, dollar exposure surfaced, share of cases reaching a concrete next step).
3. That it de-risks the post-ER coordination and concierge products that follow, by proving the engine and escalation seam first.

### Deliberate scope decisions (locked)

- **Audience: member only.** "Audience" is a parameter in the engine; HR/broker and plan/TPA experiences are *not* built in this prototype.
- **Intake: structured-first.** No document upload, no OCR, no PHI document-ingestion service. The member describes the bill through guided structured intake.
- **Interaction: guided flow, not open chatbot.** Chat is the interface skin; underneath it is a deterministic triage/workflow engine. See §6.1.
- **Escalation: in-house.** Escalation is handled by MASA staff initially. Partner integration (Wellthy or alternative) is future state; the case model is partner-agnostic.
- **Data: consume, don't build.** This prototype consumes the existing `pilot.db` SQLite database **read-only**, as a build-input snapshot. The database is built and maintained in the separate `medical_billing_data` repository; this prototype never writes to it.

---

## 2. Scope

### 2.1 In scope — P0 (build first)

- Structured intake (§5).
- Triage engine over Problem Type × Insurance Situation axes (§4).
- Workflow 1 — Explain a bill / EOB.
- Workflow 2 — Ambulance / surprise-bill triage, including the NSA rule engine and the ground-ambulance handling node.
- Workflow 3 — Document generation (four documents).
- Workflow 4 — Collections microflow.
- Workflow 5 — Light "explain & route" catch-all.
- Output contract / answer-card format (§7).
- Graceful degradation and failure-mode handling (§12).
- Escalation: member-initiated and engine-recommended; case creation; minimal advocate queue view (§8).
- Monetization seam: configurable escalation gate, no payment processing (§9).
- Eval harness and the curated golden intake set (§14).

### 2.2 In scope — P1 (next, if time allows)

- ZIP-to-locality precision for the ambulance reference rate (the data layer ships coarse, state-level geography at P0).
- Plan/benefit enrichment via Family B/F for non-ambulance workflows beyond the basic path.
- Expanded document template library.

### 2.3 Explicitly out of scope (non-goals)

- Document upload, OCR, and any PHI document-ingestion service.
- **Open-ended Q&A / general chatbot behavior.** The prototype answers within its defined workflows; free-form questions outside them are redirected, not answered (§6.1).
- HR/broker portal and plan/TPA IDR-eligibility tooling.
- Post-ER coordination, concierge, and NEMT products.
- Real authentication, payment processing, and production-grade account management.
- Deep state-specific surprise-billing answers — the prototype **detects and routes** state-specific cases to human review; it does not adjudicate them.
- Deep Medicaid adjudication — Medicaid cases are routed to state-specific resources, not answered.
- The deep debt-collection-defense product (FDCPA/FCRA workflows beyond the microflow) — separate strategic PRD.
- Penny-exact Medicare adjudication — the prototype produces a defensible *reference* rate, not an exact entitlement.
- Any build, schema change, or write to `pilot.db` — that is data-layer work (§2.4).

### 2.4 Preconditions (executed outside this repository)

This prototype depends on three tables that are **not built here**. They are built in the `medical_billing_data` repository per the **Data Completion Addendum v1.3**, because they are ingestion work that writes to `pilot.db`:

- `sources` — publisher/license registry, making every cited fact resolvable.
- `nsa_rules` — the counsel-reviewed NSA / GFE-PPDR / ground-ambulance ruleset (Tables A–K), loaded as a queryable table.
- `ambulance_fee_schedule` — Medicare ground-ambulance reference rates at state-level (or finer) geography.

The advocacy build begins by consuming the resulting `pilot.db` snapshot. Phase 0 (§15) verifies these tables are present and populated before any application code is written.

---

## 3. Architecture and posture

### 3.1 Repository and components

This prototype is a **separate repository** (`masa-sam-advocate`) from `medical_billing_data`. The two systems have different runtimes, dependency sets, lifecycles, and PHI postures; the data repository is the **sole writer** of `pilot.db`, and this application is strictly a **read-only consumer** of it.

Repository layout:

```
masa-sam-advocate/
├── CLAUDE.md
├── .python-version        pinned Python (3.12.x) — independent of the data repo's 3.14
├── backend/      FastAPI: triage engine, NSA rule engine, data-access module,
│                 workflow handlers, document generator, escalation/case service
├── frontend/     React + TypeScript chat-style guided interface
├── config/       pricing_rules.yaml, escalation_rules.yaml
├── eval/         eval harness + the curated golden intake set
├── data/         pilot.db snapshot (read-only) + app.db (case store) — both gitignored
└── README.md
```

Components:

- **Front end** — React + TypeScript. A chat-style guided interface; structured underneath (§6.1).
- **Back end** — Python (FastAPI), targeting a pinned Python version (3.12.x, in `.python-version`), independent of the data repository's Python 3.14. Houses the triage engine, NSA rule engine, data-access module, workflow handlers, document generator, and escalation/case service.
- **Read-only database** — `pilot.db` is a **build input**, not source. A finished snapshot — already containing `sources`, `nsa_rules`, and `ambulance_fee_schedule` — is copied into `data/pilot.db` (gitignored; the 455 MB binary is never committed). The data-access module reads it at a configurable path defaulting to `data/pilot.db`. The application never writes to it.
- **Case store** — a **separate, app-owned** SQLite database, `data/app.db`, holds case records (§8.2). It is the only database the application writes to. Keeping it separate from the read-only `pilot.db` snapshot preserves the single-writer boundary and means a refreshed `pilot.db` snapshot can be dropped in without touching case data.
- **Data-access module** — the adapter between workflows and data. Workflows call a clean interface (`lookup_code()`, `search_plan()`, `get_sbc_fields()`, `get_ambulance_reference_rate()`, `get_nsa_rules()`, `resolve_source()`) and never see SQL. Today the implementation is SQLite over the snapshot; it is swappable to live APIs later with no workflow changes.
- **Config** — `pricing_rules.yaml` for the escalation gate (§9); `escalation_rules.yaml` for thresholds and complexity flags.
- **Persistence** — lightweight. No real auth. Cases persist in `app.db` under a `case_id` so itemized-bill tracking and the advocate handoff work.

### 3.2 PHI posture

The prototype is **minimal-PHI by design**. Structured intake replaces document upload, so no EOBs, bills, or denial letters are ingested or stored. The data layer remains non-PHI. Member-entered free text may incidentally contain PHI; therefore:

- Free text is minimized in favor of structured fields.
- Any LLM call path that processes member free text uses a BAA-covered model endpoint.
- Free text is not persisted beyond the case record; the case record is not exported outside the escalation case service.

### 3.3 LLM boundary

The LLM **is** used for: mapping member answers (including limited free text) into structured rule-input fields; rendering rule-engine output, code lookups, and rate data into plain English; readability and tone.

The LLM is **not** the source of truth for, and must never be cited as the source of: code descriptors (from `codes`), NSA determinations (from the rule engine), reference rates (from `ambulance_fee_schedule`), deadlines (from `nsa_rules`), or any citation. **Rule evaluation is deterministic code.** LLM-generated interpretation is labeled as interpretation and is never cited.

---

## 4. Triage engine

The triage engine implements the **Billing Advocacy Axes Framework** from the SAM strategy document. It runs immediately after intake and produces a routing decision: which workflow to invoke, which rule modules to evaluate, and an escalation recommendation.

### 4.1 Axis 1 — Problem Type (primary)

| Problem Type | Routes to |
| --- | --- |
| Surprise / out-of-network bill | Workflow 2 + NSA rule engine |
| Clean denial | Workflow 1 + Workflow 3 (appeal) |
| Partial payment / underpayment | Workflow 1 |
| Balance bill | Workflow 2 + NSA rule engine + Workflow 3 (dispute letter) |
| Billing error | Workflow 1 + Workflow 3 (itemized-bill request) |
| Catastrophic exposure | Workflow 1/2 as applicable + escalation recommendation |
| Collections / credit impact | Workflow 4 (collections microflow) |

### 4.2 Axis 2 — Insurance Situation (primary)

Drives which rules and rights apply. **This is the member's health insurance situation — distinct from MASA plan tier, which only affects the escalation fee waiver (§9).**

`commercial_employer` · `commercial_individual` · `medicare_only` · `medicare_advantage` · `medicaid` · `uninsured_self_pay`

Given MASA's 55+ skew, `medicare_only` and `medicare_advantage` are first-class triage paths, not edge cases.

**Insurance Situation can short-circuit Problem Type.** Axis 2 is evaluated first and may override the Axis 1 routing table. Specifically: `medicaid` routes to Workflow 5 (light explain & route) and state-specific Medicaid resources **regardless of Problem Type**, because deep Medicaid adjudication is out of scope (§2.3). The triage engine applies Axis-2 overrides before consulting the Axis-1 table.

### 4.3 Enriching axes

- **Severity** — computed from the bill's dollar exposure: `minor` (< $500), `moderate` ($500–$5,000), `high` ($5,000–$25,000), `catastrophic` ($25,000+). Feeds the escalation recommendation. `minor` cases still receive full Workflow 1/5 help but do not, on severity alone, trigger an escalation recommendation.
- **Advocacy capacity** — `self_directed`, `needs_hand_holding`, `needs_proxy` — captured at intake (§5.8). Adjusts tone and the escalation recommendation.

### 4.4 Routing output

The triage engine returns a structured object: `problem_type`, `insurance_situation`, `severity`, `advocacy_capacity`, `primary_workflow`, `rule_modules`, `escalation_recommendation` (`none` / `suggested`), and `escalation_reasons` (list of complexity flags).

`rule_modules` selects which **categories within the single `nsa_rules` table** the rule engine evaluates — it is not a list of separate engines. For example `["nsa", "ground_ambulance"]` means "evaluate the general NSA categories and also category K (ground ambulance)." There is one rule engine over one `nsa_rules` table (§6.6).

No case dead-ends: anything not matching a deep workflow, and any Axis-2 override, routes to Workflow 5.

---

## 5. Structured intake specification

The intake schema is derived from two sources: the fields referenced across every `nsa_rules` "prototype logic" entry, and the fields Workflow 1 needs to decode a bill. Intake is progressive — the interface asks only what the chosen path needs — but the full field set is below.

### 5.1 Insurance and plan

- `insurance_situation` (enum, §4.2)
- `plan_funding_type` — `fully_insured` / `self_funded_erisa` / `unknown`. **An `unknown` answer is valid and routes funding-sensitive rules to human review — never force a guess.**
- `plan_identifier` (optional) — plan name, issuer, state, metal tier, or HIOS ID, used to attempt a Family B/F lookup
- `state` (required) — drives state-law routing

### 5.2 The bill / claim

- `codes_present` — list of `{code_type, code}` the member can read off the bill/EOB. **The interface offers code search / autocomplete backed by `lookup_code()`** so the member selects a recognized code and sees its description, rather than transcribing a code exactly. This keeps the structured-first approach low-friction.
- `amount_billed`, `amount_allowed`, `amount_plan_paid`, `amount_patient_responsibility` (any may be null) — these are **bill-level totals** (see Workflow 1 scope, §6.2)
- `denial_present` (bool); if true, `denial_codes` (CARC/RARC) and/or `denial_reason_text`
- `service_date`, `bill_date`, `denial_date` (any may be null)

### 5.3 The event

- `service_type` — `emergency` / `non_emergency` / `scheduled`
- `facility_network_status` — `in_network` / `out_of_network` / `unknown`
- `provider_network_status` — `in_network` / `out_of_network` / `unknown`
- `ambulance_involved` (bool); if true, `ambulance_type` — `ground` / `air` / `unknown`

### 5.4 Surprise-billing specifics

- `notice_consent_claimed` (bool) — did the provider claim the member signed a notice-and-consent waiver
- if true: `notice_timestamp`, `service_timestamp`, `appointment_lead_time` — captured to evaluate the Table D timing rules

### 5.5 Self-pay / GFE specifics (when `insurance_situation = uninsured_self_pay`)

- `gfe_received` (bool); if true, `gfe_expected_charge` per listed provider/facility
- used to evaluate GFE (Table H) and PPDR (Table I) rules

### 5.6 Collections specifics

- `in_collections` (bool), `reported_to_credit` (bool), `debt_validated` (bool)

### 5.7 MASA membership

- `is_masa_member` (bool); if true, `masa_plan_tier` — used **only** by the escalation gate (§9)

### 5.8 Member context

- `advocacy_capacity` — `self_directed` / `needs_hand_holding` / `needs_proxy`. Established by a short, plainly-worded intake question about how much support the member wants ("Would you like to handle this yourself with our guidance, or would you prefer more hands-on help?"). Consumed by triage (§4.3) to adjust tone and the escalation recommendation. If not answered, defaults to `needs_hand_holding`.

---

## 6. Core workflows

### 6.1 Interaction model

The product is a **guided flow**, not an open-ended chatbot. Chat is the interface skin; the engine underneath is deterministic.

- An interaction is anchored to a **case**. Intake → triage → one or more workflows → an answer card (§7) completes a workflow pass.
- After an answer card, the member can: request human escalation; start a **new workflow on the same case** (e.g., "explain the other charge," "now draft the appeal"); or start a new case. Follow-ups are interpreted as *workflow selections on the existing case*, not free-form questions.
- A member message that does not map to a workflow or a known intent is **redirected**, not improvised on — the interface restates the available actions and, if appropriate, offers escalation. Open-ended Q&A is a non-goal (§2.3).
- All workflow output uses the answer-card format (§7).

### 6.2 Workflow 1 — Explain a bill / EOB

**Scope:** per-line code semantics plus bill-level dollar reconciliation. The workflow decodes each entry in `codes_present` via `lookup_code()` (Family A) and explains, line by line, what each code means. It then reconciles the **bill-level totals** (`amount_billed` / `amount_allowed` / `amount_plan_paid` / `amount_patient_responsibility`) into a plain-English account of how the patient's share was reached and whether it looks consistent with the plan. Per-line *dollar* reconciliation is not attempted, because structured intake captures bill-level totals, not per-line charges — this is a deliberate scope boundary, not a limitation to be worked around.

If a plan is identified, the workflow pulls benefit/cost-sharing context via Family B (`plan_attributes`, `plan_benefits`) and Family F (`sbc_fields`). CPT codes return the unlicensed-fallback (category only — see §10). Where the explanation surfaces a likely error or a likely successful appeal, it hands off to Workflow 3.

### 6.3 Workflow 2 — Ambulance / surprise-bill triage (the wedge)

1. Triage classifies Problem Type and Insurance Situation.
2. The **NSA rule engine** evaluates applicable rules from `nsa_rules` (§6.7).
3. **Air ambulance** → NSA air-ambulance rules (Table G) apply; the engine produces a protection determination.
4. **Ground ambulance** → the **ground-ambulance handling node** (Table K). Ground ambulance is generally *not* protected by the federal No Surprises Act. The node states this honestly and produces a negotiation position: the Medicare **reference rate** from `ambulance_fee_schedule` as the anchor ("billed $1,800; the Medicare reference rate for this transport in your state is roughly $450"), plus routing — state-law check, negotiation guidance, GFE/PPDR if self-pay, and the MASA gap-coverage handoff for members.
5. Output: protection status, the dollar gap, deadlines, next steps, and (self-pay) the PPDR path.

The protection determination is always framed as *likely* / *appears to* — never as a definitive legal conclusion (§13).

### 6.4 Workflow 3 — Document generation

Generates four parameterized, citation-backed documents from case data:

1. Itemized-bill request letter
2. First-level internal appeal letter (parameterized by denial type)
3. Balance-bill dispute letter
4. PPDR initiation summary (self-pay)

The LLM fills parameterized templates; it does not free-draft legal language. Every document carries the relevant citations and the standard disclaimer. **Document templates and framing require counsel sign-off before any real member sees output (§13).**

### 6.5 Workflow 4 — Collections microflow

A deliberate, self-contained endpoint for the largest out-of-scope cluster in the use-case data (collections / credit harassment). It does not resolve the collection — it equips and routes: an FDCPA-rights explainer, a debt-validation letter template, and CFPB / state-AG complaint routing. Structured so the deep collections-defense product can later replace it without rework.

### 6.6 Workflow 5 — Light "explain & route"

Catch-all so no case dead-ends. For cases outside the deep workflows — including Axis-2 overrides such as Medicaid — it explains what it can from available data, educates the member on their situation, and routes to the right external resource or to human escalation.

### 6.7 NSA rule engine

- `nsa_rules` (built per the Data Completion Addendum) stores, for each rule, its category (A–K), human-readable "prototype logic," `system_action`, `citation`, deadlines, `qpa_dependent` flag, review `status`, and `source_id`.
- Each rule maps to a deterministic predicate function keyed by `rule_id`: `predicates[rule_id](intake) -> bool`. The table is the spec; the predicate functions are the implementation; the two are cross-checked in tests.
- `rule_modules` from triage selects which **categories** to evaluate; there is one engine over one table.
- The engine iterates the applicable rules, collects matched `system_action` items, and assembles the determination.
- The engine **never overrides a `human_review` action** — if any matched rule says human review, the case carries an escalation recommendation.
- If a predicate function raises an exception, the engine treats that rule as `human_review` — never as "no violation found" (§12).
- A rule whose `status` is not `counsel_approved` may run in dev and eval, but the UI must not surface a *definitive* determination from it; it degrades to "this needs human review."

---

## 7. Output contract (answer-card format)

Every user-facing answer follows the structure from data PRD v1.1 §12.3. This is also the UPL safety boundary — cited facts and labeled interpretation are kept visibly separate.

1. **What we found** — the underlying facts from the data layer / rule engine. Cited.
2. **What it likely means** — interpretation. Labeled as interpretation. Not cited.
3. **Citations** — every fact resolves to a real source via `resolve_source()`.
4. **Confidence** — per relevant field.
5. **What still needs verification** — gaps, stale-data warnings, `unknown`-input warnings, and any facts a lookup could not confirm (§12).
6. **Recommended next step** — a concrete action, plus a dollar figure where applicable.

---

## 8. Escalation

### 8.1 Trigger logic

- **Member-initiated** — always available, on every screen. This is the primary path.
- **Engine-recommended** — independently, the engine surfaces "we suggest a human advocate here" when an escalation reason fires. It **recommends; it never forces.** The member always decides.

Escalation reasons (configurable in `escalation_rules.yaml`): dollar exposure above threshold; `severity = catastrophic`; any matched rule with a `human_review` action; notice-and-consent dispute; `plan_funding_type = self_funded_erisa` combined with a state-law question; conflicting or `unknown` inputs on load-bearing fields; an unrecoverable technical failure in a workflow (§12).

### 8.2 Handoff and case model

Escalation creates an escalation case in `app.db` containing the full intake, the triage result, all workflow outputs, the generated documents, and the rule-engine trace. The case service is partner-agnostic so a future Wellthy (or alternative) integration consumes the same case object.

`case` object: `case_id`, `created_at`, `intake`, `triage_result`, `workflow_outputs`, `generated_documents`, `escalation_status` (`none` / `recommended` / `requested` / `in_queue`), `gate_decision`.

### 8.3 Advocate queue view

A minimal **read-only** internal view listing escalation cases with their structured detail — enough to demonstrate the handoff in a leadership demo. No advocate workflow tooling is built.

---

## 9. Monetization seam

The prototype implements a **configurable escalation gate**, not a payment system. No payment processing is built.

The AI service itself is ungated (the prototype is member-only). When a member requests or accepts escalation, the gate reads `pricing_rules.yaml`, evaluates `is_masa_member` and `masa_plan_tier`, decides whether a service charge applies or is waived, and displays the corresponding message. It does not collect payment.

`pricing_rules.yaml` (illustrative — values are placeholders pending the monetization decision):

```yaml
member:
  escalation_fee_default: "service_charge"
  waived_tiers: ["Emergency Shield Plus", "Lifetime"]
  message_charged: "..."
  message_waived: "..."
non_member:        # future state — not exercised in the member-only prototype
  ai_service: "$5/month (covers all SAM AI products)"
  escalation_fee: "service_charge"
```

When the monetization model is settled, the change is to this file, not to the build.

---

## 10. Data dependencies

| Workflow | Needs |
| --- | --- |
| Workflow 1 — Explain | Family A `codes`; Family B `plan_attributes` / `plan_benefits`; Family F `sbc_fields`; `sources` |
| Workflow 2 — Ambulance/surprise | `nsa_rules`; `ambulance_fee_schedule`; Family A (ambulance HCPCS + modifiers); `sources` |
| Workflow 3 — Documents | Case data; `nsa_rules` citations; `sources` |
| Workflow 4 — Collections | Templates only — no DB dependency |
| Workflow 5 — Light route | Family A as available; `sources` |

Family D (Medicaid), Family G (payer policies), Family H (NPPES) are **not** required by the prototype. Family B/F coverage is partial (SBC fields exist for ~2,326 of ~5,290 plans); `plan_attributes` is the more complete fallback for deductible/OOP data, and the data-access module prefers it. Monetary values in the existing Family A/B/F tables are stored as raw strings — the data-access module parses them; `ambulance_fee_schedule.reference_rate` is the exception and is stored as integer cents.

**CPT data limitation — read this before setting expectations.** CPT codes are AMA-licensed and are **not** in `pilot.db` (only a detection sentinel). Physician, outpatient, and procedural bills are predominantly CPT-coded, so for a large share of real bills Workflow 1 will decode ICD/HCPCS/revenue lines fully but return only a **category-level fallback** for CPT lines. This is a structural limitation of the licensed-data boundary, not a bug. Leadership and the eval rubric should expect partial decoding on CPT-heavy bills; full CPT decoding would require an AMA license and is a future commercial decision.

---

## 11. LLM requirements

See §3.3 for the boundary. Implementation notes:

- The intake-mapping LLM call converts member answers into the structured intake object; its output is validated against the schema before the rule engine runs.
- The rendering LLM call converts a fully-formed determination object into the answer card; it may not introduce facts, citations, or determinations not present in the determination object.
- Golden-fixture tests pin both call types so behavior is stable across model updates.

---

## 12. Graceful degradation and failure modes

The engine has defined behavior for technical failure, separate from data gaps (handled by the output contract) and unclassifiable cases (handled by Workflow 5). The governing principle: **every failure degrades toward "we could not determine this — here is a human," never toward a false confident answer.** All failures are logged.

- **Data lookup fails** (DB error, unexpected missing row) — the workflow continues with what it has; the unverifiable fact is surfaced in the answer card's "what still needs verification" and never fabricated. If a load-bearing fact cannot be retrieved, the case carries an escalation recommendation.
- **LLM failure on intake mapping** (timeout/error) — retry once; on persistent failure, fall back to asking the member the structured questions directly. The engine never proceeds on an unvalidated intake object.
- **LLM failure on answer-card rendering** (timeout/error) — retry once; on persistent failure, present the structured determination in a plain, unpolished template rather than failing the request.
- **Incomplete intake** — the engine proceeds with available fields, marks missing fields, and routes to human review if a *load-bearing* field is missing.
- **Rule predicate raises** — the engine treats that rule as `human_review` (§6.7), never as "no violation."
- **Unrecoverable workflow failure** — the member is shown a plain error and offered escalation; an escalation case is created with whatever was gathered.

---

## 13. Legal and compliance

- **UPL / unauthorized insurance advice.** All user-facing output is framed as information and self-help support, not legal or licensed insurance advice. Standard disclaimers appear at the application layer. Protection determinations are always phrased as *likely* / *appears to*.
- **Counsel gate (blocking).** Document templates and the framing of protection determinations must be reviewed and signed off by counsel before any real member sees output. This review runs in parallel with the build; it is not a final-phase task.
- **Ruleset review status.** `nsa_rules` rows carry a `status` field. Only `counsel_approved` rules may drive a definitive UI determination; others degrade to "needs human review."
- **Regulatory flux.** Rules dependent on the Qualifying Payment Amount (QPA) methodology carry a `qpa_dependent` flag — the QPA methodology has been subject to litigation and rulemaking change, so these are the rules counsel rechecks first. The ground-ambulance "no federal protection" rule (GROUND-003) is similarly time-sensitive and should be re-reviewed if federal legislation advances.
- **Deadlines.** All deadlines are human-reviewed structured fields (`nsa_rules.deadline_days` / `deadline_basis`), never LLM-derived.
- **PHI.** Per §3.2 — minimal-PHI by design.

---

## 14. Eval harness

The 2,848-row use-case dataset (`MASA_Use_Case_Coverage_Analysis.xlsx`) is the basis of the prototype's acceptance test and outcome metrics, but it cannot be used raw — its rows are *need descriptions* (Primary Need / Capability / Gap), not filled intake forms, and carry no ground-truth triage labels.

**The golden intake set — a distinct deliverable.** Before the harness can score anything, a one-time **curated golden set of ~150 intake fixtures** is built: a stratified sample across `Primary Need`, each converted into a complete intake object **and labeled with the expected triage outcome** (expected `problem_type`, `insurance_situation`, and `primary_workflow`). This labeled set is the denominator for accuracy metrics and is a separate artifact from the harness code, version-controlled under `eval/`.

**Curation, not generation.** If an LLM is used to draft intake objects from the use-case rows, the drafts and especially the expected-outcome labels must be **human-reviewed and corrected** — otherwise the harness is testing the LLM with LLM-authored inputs and labels, which is not a real test. The golden set is treated as human-curated ground truth.

**Population caveat.** The use cases were mined from CFPB complaints and Reddit, which skew toward the general population and toward collections-heavy issues. MASA's members skew older (55+), Medicare/Medicare Advantage, and ambulance-centric. The eval therefore demonstrates *the engine works on complaint-derived cases* — it does not, on its own, demonstrate *the engine works for MASA's specific member population*. This caveat should be stated wherever eval results are reported; a MASA-representative test set is a recommended follow-on.

**Run.** Each golden fixture is run through the full engine; its answer card, routing, and escalation recommendation are captured. A human grading rubric scores each: triage classification correct (against the label); explanation accurate; citations valid and resolving; recommended next step correct; would the member be better off than with nothing. Output is a graded report that doubles as the source of the broker-deck metrics (share of bills with identified errors, dollar exposure surfaced, share of cases reaching a concrete next step).

---

## 15. Phased build plan for Claude Code

| Phase | Goal | Gate |
| --- | --- | --- |
| **0 — Scaffold + precondition check** | Scaffold the repo (FastAPI back end, React/TS front end, config files, `app.db`). Copy in the `pilot.db` snapshot. Verify `sources`, `nsa_rules`, and `ambulance_fee_schedule` exist and are populated. | Repo runs; all three precondition tables present and non-empty. **If absent, stop — the Data Completion Addendum must be run first in `medical_billing_data`.** |
| **1 — Engine core** | Data-access module; triage engine (incl. Axis-2 overrides); structured intake. | Triage returns correct routing on a fixture set; intake schema validated. |
| **2 — Workflows 1 & 2** | Explain workflow; ambulance/surprise workflow; NSA rule engine + predicate functions; ground-ambulance node; output contract; graceful-degradation handling. | Rule engine passes golden fixtures; ground-ambulance node returns a reference rate; answer cards render; failure modes degrade per §12. |
| **3 — Workflows 3, 4, 5** | Document generation (four documents); collections microflow; light route. | All four documents generate with valid citations; no case dead-ends. |
| **4 — Escalation + gate** | Member-initiated and engine-recommended escalation; case model in `app.db`; advocate queue view; monetization gate. | Escalation creates a complete case object; gate reads `pricing_rules.yaml` correctly. |
| **5 — Eval** | Curate the golden intake set; build the eval harness; stratified run; graded report. | Golden set curated and human-reviewed; harness runs the ~150-case sample and emits the graded report. |

---

## 16. Success metrics

Measured against the curated golden intake set (§14).

| Metric | Target |
| --- | --- |
| Triage classification accuracy vs. golden labels | ≥85% |
| Citation validity (every cited fact resolves to a real source) | 100% |
| Code-decode coverage for bill/EOB lines, excl. CPT | ≥95% |
| NSA rule-engine correctness on golden fixtures | 100% |
| Ground-ambulance node produces a reference rate | 100% of ground-ambulance cases |
| Eval cases ending in a concrete next step | ≥95% |
| Cases with `human_review`-flagged rules carrying an escalation recommendation | 100% |
| Graceful degradation: no failure mode produces a false confident answer | 100% |

---

*End of PRD v1.2. Data-completion work is specified in the companion document: MASA Public Data Ingestion Layer — Data Completion Addendum v1.3, executed in the `medical_billing_data` repository.*
