# SAM Frontend Requirements — Guided Chat UI
## Prototype v1.0

**Companion to:** MASA SAM Medical Bill Advocate PRD v1.2 (`docs/PRD.md`)  
**Scope:** Member-facing guided intake + response interface; separate advocate admin screen  
**Status:** Requirements resolved — ready to build  
**Design system:** MASA Global brand (`masa-brand` skill)  
**Responsiveness:** Mobile-responsive; desktop-first for demo

---

## 1. Purpose and Goals

The backend engine (Phases 1–5) is complete and API-accessible. This document specifies the member-facing interface that makes the engine usable without raw JSON, plus a separate advocate admin screen for the queue view.

### Goals
- Let a member describe their billing problem through a guided, chat-style input sequence and receive a structured advocacy assessment in response
- Provide a demo-ready prototype surface for the MASA leadership and broker/HR positioning deck
- Keep all intake **structured** — no document upload, no OCR, no free-text PHI ingestion (consistent with PRD §2.3 scope decisions)
- Produce a case JSON at every intake completion so sessions are **replayable and testable** — feeds directly into the eval harness (`eval/run_eval.py`)

### Non-goals (this document)
- Production authentication or account management
- OCR or document upload (future, after PHI/data-flow design)
- Open-ended chatbot behavior — the interface redirects out-of-scope questions (PRD §6.1)
- Mobile-native app

---

## 2. Design System

All visual output follows the **MASA Global brand system** applied via the `masa-brand` skill. This covers colors, typography, component styling, spacing, and logo usage. The skill must be consulted before producing any styled output — do not guess at brand values.

Both the member-facing chat UI and the advocate admin screen use the same design system.

---

## 3. UX Paradigm

**Chat is the skin; the engine is deterministic underneath (PRD §6.1).**

The interface looks and feels like a messaging conversation but every member "turn" maps to a structured intake field or workflow selection. There are no free-form questions the engine improvises on.

```
Member                          SAM Engine
  │                                │
  │── "I have a problem with a bill" ──►  welcome / problem picker
  │◄── "What type of issue?"  ──────────  ProblemType step
  │── selects "Ambulance / surprise bill"
  │◄── "What state are you in?" ─────────  state step
  │── "FL"
  │◄── "What's your insurance?"  ────────  InsuranceSituation step
  │  ... (progressive intake, ~4–8 questions) ...
  │◄── ANSWER CARD rendered ─────────────  Workflow result
  │◄── "Would you like to: [Explain more] [Get documents] [Talk to advocate]"
  │── selects "Get documents"
  │◄── ANSWER CARD (Workflow 3) ──────────  Documents generated
  │── "Talk to an advocate"
  │◄── ESCALATION + GATE DECISION ────────  Escalation status + fee message
```

---

## 4. Member-Facing Chat UI

### 4.1 Welcome Screen
- MASA/SAM branding per design system
- Single CTA: **"Help me with a medical bill"**
- Brief explainer (2 sentences): what SAM does and doesn't do; links to the disclaimer
- No login required for the prototype
- **Footer:** small "Scenarios" link (→ `/scenarios`) and "Advocate Login" link (→ `/admin`); subtle, not prominent — below the fold or in a minimal footer bar

### 4.2 Guided Intake (4 phases, progressive)

Each phase is a sequence of chat bubbles + a response widget (picker, number input, toggle, or short text). The interface only asks what the current path requires — not all 30 fields upfront.

#### Phase 1 — Problem identification (always asked)

| Question | Widget | Field |
|---|---|---|
| "What best describes your situation?" | Card picker (7 options in plain English) | `problem_type` |
| "Which state did you receive care in?" | 2-letter text input with validation | `state` |
| "What's your health insurance situation?" | Card picker (6 options) | `insurance_situation` |

Plain-English labels for `problem_type`:
- "I got a surprise bill or out-of-network charge" → `surprise_out_of_network`
- "My insurance denied a claim" → `clean_denial`
- "My insurance underpaid or only partially covered a bill" → `partial_payment_underpayment`
- "I was balance-billed by a provider" → `balance_bill`
- "I think there's an error on my bill" → `billing_error`
- "I'm facing a very large medical bill" → `catastrophic_exposure`
- "A debt collector is contacting me about a medical bill" → `collections_credit_impact`

#### Phase 2 — Bill details (conditional on Phase 1 path)

**Path: billing_error / clean_denial / partial_payment**
| Question | Widget | Field |
|---|---|---|
| "What were the billing codes on your bill? (optional)" | Code search widget (all 11 types) | `codes_present` |
| "What was the total amount billed?" | Currency input | `amount_billed` |
| "What did your insurance say they'd pay?" | Currency input + "I don't know" toggle | `amount_allowed`, `amount_plan_paid` |
| "What is your current balance owed?" | Currency input | `amount_patient_responsibility` |
| "Was there a denial notice?" | Yes/No toggle | `denial_present` |
| If denial: "What reason did they give?" | Short text | `denial_reason_text` |

**Path: surprise_out_of_network / balance_bill**
| Question | Widget | Field |
|---|---|---|
| "Was this an ambulance?" | Yes / No | `ambulance_involved` |
| If yes: "Air or ground ambulance?" | Radio: Air / Ground / I don't know | `ambulance_type` |
| If yes: "What was the HCPCS code on the bill? (optional)" | Code search widget | `codes_present` |
| "Was the facility in-network?" | In-network / Out-of-network / Not sure | `facility_network_status` |
| "Was the provider in-network?" | In-network / Out-of-network / Not sure | `provider_network_status` |
| "Total amount billed?" | Currency input | `amount_billed` |
| "Your current balance owed?" | Currency input | `amount_patient_responsibility` |
| "Did the provider claim you signed a waiver?" | Yes / No | `notice_consent_claimed` |

**Path: collections_credit_impact**
| Question | Widget | Field |
|---|---|---|
| "Has this been sent to a collection agency?" | Yes / No | `in_collections` |
| "Has it been reported to your credit?" | Yes / No | `reported_to_credit` |
| "Have you received written debt validation?" | Yes / No | `debt_validated` |

**Path: catastrophic_exposure**
| Question | Widget | Field |
|---|---|---|
| "What is the total amount you're facing?" | Currency input | `amount_billed` |
| "Your current balance owed?" | Currency input | `amount_patient_responsibility` |
| (then branches to billing_error or surprise sub-path based on service type) | | |

#### Phase 3 — MASA membership (always asked)

| Question | Widget | Field |
|---|---|---|
| "Are you a MASA member?" | Yes / No | `is_masa_member` |
| If yes: "What is your plan tier?" | Dropdown: Emergency Shield Plus / Lifetime / Other | `masa_plan_tier` |

**Note on plan tier:** The dropdown must include the two waived tiers (`Emergency Shield Plus`, `Lifetime`) as named options to prevent typos that would incorrectly trigger a service charge. An "Other / I'm not sure" option maps to a string that falls outside the waived list, correctly applying the default fee.

#### Phase 4 — Advocacy capacity (always asked, one question)

| Question | Widget | Field |
|---|---|---|
| "How much help would you like?" | Card picker (3 options): "Guide me step by step" / "Give me the full picture" / "Handle this for me" | `advocacy_capacity` |

Maps to: `needs_hand_holding` / `self_directed` / `needs_proxy`

---

### 4.3 Intake Review + Submit

Before calling the API:
- Summary card: "Here's what you told us" — plain-English recap of the key fields
- Member can go back and edit any answer
- **"Analyze my case"** CTA → `POST /cases`
- Collapsible **"View case data"** panel showing the full intake JSON — the programmatic testing hook (see §8)

### 4.4 Triage Result (transitional)

While the API processes:
- Loading state: "SAM is reviewing your case…"

On response:
- Brief routing card: "We've identified this as a [plain-English problem type] case."
- Auto-advance to the primary workflow result after 1–2 seconds

### 4.5 Answer Card Display

The answer card (6 sections from PRD §7) renders as a structured card, not a wall of text.

```
┌──────────────────────────────────────────────────┐
│  What We Found                                   │
│  ────────────────────────────────────────────    │
│  • [fact 1 — cited]                              │
│  • [fact 2 — cited]                              │
│                                                  │
│  What It Likely Means  (interpretation only)     │
│  ────────────────────────────────────────────    │
│  • [interpretation 1]                            │
│                                                  │
│  What Still Needs Verification                   │
│  ────────────────────────────────────────────    │
│  • [gap 1]                                       │
│                                                  │
│  Recommended Next Step                           │
│  ────────────────────────────────────────────    │
│  [concrete action — bold, prominent]             │
│  Dollar at stake: $X,XXX                         │
│                                                  │
│  [Citations — expandable]  [Confidence — badge]  │
│  [Disclaimer — collapsed, expandable]            │
└──────────────────────────────────────────────────┘
```

**UPL framing:** "What It Likely Means" is visually labelled as interpretation. The disclaimer is always present, collapsed by default, expandable on tap. Protection determinations always use "likely" / "appears to" language — never definitive.

### 4.6 Post-Answer Action Bar

After the primary workflow answer card, a persistent bar offers context-relevant next actions:

```
[ Explain the codes ]  [ Get documents ]  [ Explain my options ]  [ Talk to an advocate ]
   Workflow 1             Workflow 3          Workflow 5               Escalation
```

Only the workflows relevant to the current triage are shown:
- Collections case: "Understand my rights" (Workflow 4) + "Talk to an advocate"
- Billing error: "Explain the codes" (Workflow 1) + "Get documents" (Workflow 3) + "Talk to an advocate"
- Ambulance case: "Get documents" (Workflow 3) + "Talk to an advocate"

Selecting a workflow calls `POST /cases/{case_id}/workflow{N}` and appends the new answer card below in the same chat thread.

### 4.7 Document Viewer

When Workflow 3 runs:
- Each document appears as a named card (e.g., "Itemized Bill Request Letter")
- Expand to read full text in a scrollable pane
- **Copy to clipboard** and **Download as .txt** buttons
- Persistent banner: *"This document requires counsel review before use. Complete all [BRACKETED] fields before sending."*
- Documents fetched from `GET /cases/{case_id}` → `generated_documents`

### 4.8 Escalation Flow

Triggered by "Talk to an advocate" or by engine-recommended escalation surfaced in the answer card.

1. Modal: "Request a human advocate"
   - Shows gate decision message from `POST /cases/{case_id}/escalate` (fee waived or charge applies)
   - "Confirm" CTA
2. Confirmation state: "Your case has been submitted. Case ID: [case_id]"

### 4.9 Session Persistence

- `case_id` stored in `sessionStorage` (tab-scoped; cleared on browser close — sufficient for prototype)
- On page refresh within a session, `GET /cases/{case_id}` restores all prior workflow outputs
- **"Copy case JSON"** always available in a footer drawer (see §8)

---

## 5. Scenarios Screen (`/scenarios`)

A separate screen for exploring pre-built demo cases. Accessible via the footer link on the welcome screen. The welcome screen itself stays clean.

### 5.1 Purpose

Gives a presenter or pilot tester a one-click path to the answer card for any key use case — useful for demos, internal walkthroughs, and eval fixture review.

### 5.2 Layout

A card grid of pre-built scenarios. Each card shows:
- Scenario name and a one-sentence description
- Key tags (e.g., "Ground Ambulance", "MASA Member", "$1,950 at stake")
- CTA: **"Run this scenario"**

Clicking "Run this scenario" pre-fills the full intake, skips the guided intake flow, jumps straight to the review screen (§4.3 "Here's what you told us"), and the member clicks **"Analyze my case"** to run it. The intake JSON is visible in the "View case data" panel so the tester can see exactly what was submitted.

### 5.3 Pre-Built Scenarios

| # | Name | Description | Key fields |
|---|---|---|---|
| 1 | **Ground Ambulance — MASA Member** | Emergency ground transport billed $2,400; MASA Emergency Shield Plus member; plan paid $450 | `surprise_out_of_network`, `ambulance_type=ground`, `A0427`, `amount_billed=2400`, `is_masa_member=true`, `masa_plan_tier=Emergency Shield Plus` |
| 2 | **Surprise OON Bill — Commercial** | OON emergency physician bill at in-network hospital; denial present; $3,200 billed | `surprise_out_of_network`, `service_type=emergency`, `facility_network_status=in_network`, `provider_network_status=out_of_network`, `denial_present=true`, `amount_billed=3200` |
| 3 | **Billing Error — Medicare Member** | Medicare Advantage member; ICD-10 and HCPCS codes on EOB that member can't interpret; $850 patient responsibility | `billing_error`, `insurance_situation=medicare_advantage`, `codes_present=[ICD10CM:I10, HCPCS:A0425]`, `amount_billed=850` |
| 4 | **Collections — Credit Harassment** | Medical bill sent to collections; reported to credit bureaus; member doesn't know their FDCPA rights | `collections_credit_impact`, `in_collections=true`, `reported_to_credit=true` |
| 5 | **Self-Pay PPDR** | Uninsured patient; received GFE for $900; billed $1,800; qualifies for dispute resolution | `surprise_out_of_network`, `insurance_situation=uninsured_self_pay`, `gfe_received=true`, `gfe_expected_charges=[{expected_charge:900}]`, `amount_billed=1800` |

These five scenarios cover: the flagship MASA ambulance case, standard NSA surprise billing, Medicare member EOB decode, the collections microflow, and the self-pay PPDR pathway — the full breadth of the engine in a demo.

### 5.4 Scenario Detail (expandable, optional)

Each scenario card can expand to show:
- The full intake JSON (for developer/tester reference)
- Expected triage routing (e.g., "Routes to Workflow 2 → Ground Ambulance Node")
- Key things to look for in the output (e.g., "Medicare reference rate should appear in What We Found")

This panel doubles as a lightweight demo script for the presenter.

---

## 6. Advocate Admin Screen

A separate screen, accessible at **`/admin`** (not linked from the member UI — navigate directly). No authentication in the prototype; the URL is the access control.

### 5.1 Queue View (`/admin`)

Displays all escalated cases (sourced from `GET /cases/queue`).

| Column | Source |
|---|---|
| Case ID | `case_id` |
| Submitted | `created_at` (formatted) |
| Status | `escalation_status` badge |
| Problem | `problem_type` (plain English) |
| Severity | `severity` badge (color-coded: minor/moderate/high/catastrophic) |
| Dollar at stake | `dollar_at_stake` |
| Coverage | `gate_decision.fee_applies` → "Covered" or "Fee applies" |
| Workflows run | `workflow_outputs_present` as chips |

- Rows sorted by `created_at` descending (newest first)
- Click any row → Case Detail screen (`/admin/cases/{id}`)
- Refresh button to poll for new cases (no real-time in prototype)

### 5.2 Case Detail (`/admin/cases/{id}`)

Sourced from `GET /cases/{id}`. Structured as collapsible panels:

1. **Case header** — case_id, created_at, escalation_status, gate_decision
2. **Member intake** — key fields from `intake` rendered in plain English (same summary layout as §4.3)
3. **Triage result** — problem_type, insurance_situation, severity, rule_modules, escalation_reasons
4. **Workflow outputs** — one expandable panel per workflow run; renders the answer card (same `AnswerCard` component as member UI)
5. **Generated documents** — same `DocumentViewer` component as member UI, with counsel-review banner
6. **Raw JSON** — collapsible panel showing the full case object for developer/support use

---

## 6. Code Search Widget

Covers all 11 code types: ICD10CM, ICD10PCS, HCPCS, CARC, RARC, RevenueCode, POS, Modifier, MSDRG, NDC, CPT.

**Input approach:** Unified search — member types any code or description fragment. The widget auto-detects the most likely type by format:

| Pattern | Detected type |
|---|---|
| Starts with letter, 5 chars (e.g., A0427) | HCPCS |
| Letter + digits, 3–7 chars (e.g., I10, A00.1) | ICD10CM |
| 7 alphanumeric chars starting with digits (e.g., 0016070) | ICD10PCS |
| 3-digit numeric (e.g., 305) | MSDRG |
| 3-digit numeric starting with 0 (e.g., 0001) | RevenueCode |
| 1–3 digit numeric (e.g., 1, 97) | CARC |
| 2-letter + digits (e.g., N130) | RARC |
| 11-digit numeric | NDC |
| 5-digit numeric (e.g., 99213) | CPT (returns fallback) |

If auto-detection is ambiguous, the widget shows a small "Type: [detected]" label the member can tap to override.

**Behavior:**
- Debounced at 300ms — calls `GET /codes/search?q={query}&code_type={detected_type}&limit=10`
- Returns description preview inline as member types
- Member selects → added as a chip to `codes_present`; multiple codes supported
- CPT: chip shows "CPT [code] — description not available (AMA licensed)"
- "Skip" link always available to proceed without codes

---

## 7. API Integration Map

| UI Action | API Call | Notes |
|---|---|---|
| Submit intake | `POST /cases` | Returns `case_id` + `triage_result` |
| Run workflow 1 | `POST /cases/{id}/workflow1` | |
| Run workflow 2 | `POST /cases/{id}/workflow2` | |
| Run workflow 3 | `POST /cases/{id}/workflow3` | Stores docs in `generated_documents` |
| Run workflow 4 | `POST /cases/{id}/workflow4` | |
| Run workflow 5 | `POST /cases/{id}/workflow5` | |
| Request escalation | `POST /cases/{id}/escalate` | Body: `{"trigger":"member_initiated"}` |
| Restore session | `GET /cases/{id}` | Loads all prior workflow outputs + documents |
| Code autocomplete | `GET /codes/search?q=&code_type=&limit=10` | **New backend endpoint** — see §9 |
| Advocate queue | `GET /cases/queue` | Admin screen only |
| Case detail | `GET /cases/{id}` | Admin screen + session restore |

---

## 8. Programmatic Testing Hook

Because intake is fully structured, every demo session produces a replayable JSON. The frontend makes this explicit:

- **"Copy case JSON"** in footer drawer → outputs the full intake as the exact dict the eval harness expects
- **Pre-fill mode** (dev/demo use): accepts an intake JSON pasted into a hidden input → pre-populates the intake steps with that data, allowing replay of any prior session
- The golden set (`eval/golden_set.py`) can be extended by copying a demo session's JSON into the fixture list with `__expected_*` labels added manually

This means any session from a live demo, a pilot tester, or a support call can become a test fixture with minimal effort.

---

## 9. New Backend Endpoint Required

**`GET /codes/search?q={query}&code_type={type}&limit=10`**

- New `search_codes(query, code_type, limit)` function in `backend/data_access/interface.py` using `WHERE description LIKE ? OR code LIKE ?` against the `codes` table
- Returns `[{code, code_type, description, short_description, source_id}]`
- CPT code_type: returns the sentinel fallback with `fallback` key, no DB query
- New router: `backend/routers/codes.py` → `GET /codes/search`
- Must be registered in `backend/main.py`

---

## 10. Routing

| Path | Screen |
|---|---|
| `/` | Welcome → intake flow |
| `/case/:caseId` | Active case — chat thread with answer cards |
| `/scenarios` | Pre-built scenario gallery |
| `/admin` | Advocate queue view |
| `/admin/cases/:caseId` | Case detail for advocate |

Client-side routing (React Router or equivalent). The Vite dev proxy (`/api` → backend) handles all API calls without CORS configuration.

---

## 11. Prototype Constraints

| Constraint | Rationale |
|---|---|
| No document upload or file input | PHI/data-flow design not complete; structured intake per PRD §2.3 |
| No login or account creation | Prototype-only; PRD explicitly excludes real auth |
| `/admin` access by URL only | No auth in prototype; not linked from member UI |
| All dollar amounts optional | Engine degrades gracefully on missing amounts |
| Disclaimer always present on answer cards | UPL compliance |
| Counsel-review banner on all documents | `counsel_required=True`; must not be suppressed |
| `sessionStorage` for session persistence | Tab-scoped; sufficient for demo; safer than `localStorage` without auth |
| Desktop-first layout | Demo will be on a desktop device; mobile-responsive CSS is included but not the primary test target |

---

## 12. Component Inventory

| Component | Used in |
|---|---|
| `ChatThread` | Member UI — scrollable message history |
| `IntakeStep` | Member UI — single question + response widget |
| `CardPicker` | Member UI — enum selections (problem type, insurance, advocacy capacity) |
| `CurrencyInput` | Member UI — dollar amount with "I don't know" toggle |
| `CodeSearchWidget` | Member UI — autocomplete across all 11 code types |
| `AnswerCard` | Member UI + Admin detail — 6-section answer card |
| `ActionBar` | Member UI — post-answer workflow CTA row |
| `DocumentViewer` | Member UI + Admin detail — expandable letter with copy/download |
| `EscalationModal` | Member UI — gate decision + confirm |
| `CaseDataDrawer` | Member UI — footer drawer with JSON export |
| `LoadingState` | Member UI — "SAM is reviewing your case…" |
| `QueueTable` | Admin queue — sortable case list |
| `CaseDetailPanel` | Admin detail — collapsible section panels |
| `SeverityBadge` | Admin queue + triage display — color-coded severity |
| `ScenarioCard` | Scenarios screen — pre-built case card with run CTA and expandable detail |
| `ScenariosGrid` | Scenarios screen — card grid layout |

---

## 13. Resolved Questions

All open questions are resolved. The document is build-ready.

| Question | Decision |
|---|---|
| Visual design system | MASA Global brand via `masa-brand` skill (§2) |
| Code search scope | All 11 code types with format-based auto-detection (§6) |
| Session persistence | `sessionStorage` only — tab-scoped, sufficient for prototype (§4.9) |
| Advocate queue view | Separate admin screen at `/admin` and `/admin/cases/:id` (§6) |
| Mobile responsiveness | Mobile-responsive CSS included; desktop-first for demo (§11) |
| Demo scenarios | Separate `/scenarios` screen (§5) — welcome screen stays clean |
| Admin nav link | Small footer link "Advocate Login" → `/admin` on welcome screen (§4.1) |
