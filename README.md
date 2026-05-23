# masa-sam-advocate

SAM Medical Bill Advocate — prototype per PRD v1.2. Built phase by phase; see `docs/PRD.md`.

## Prerequisites

- **Python 3.12.x** — install via `pyenv install 3.12.9` or the Windows py launcher. The `.python-version` file pins the version.
- **Node 18+** — for the React frontend.
- **`data/pilot.db`** — the finished pilot.db snapshot must be manually copied here before starting the backend. It is gitignored (455 MB binary) and is built by the companion repository per the **MASA Public Data Ingestion Layer — Data Completion Addendum v1.3** (`medical_billing_data` repo).

## Backend setup

```bash
# From repo root
pip install -r backend/requirements.txt
uvicorn backend.main:app --reload
```

The server performs a **precondition check at startup**. If `pilot.db` is missing or its three required tables (`sources`, `nsa_rules`, `ambulance_fee_schedule`) are empty, the server will log a detailed error and exit with code 1. See Phase 0 gate below.

## Frontend setup

```bash
cd frontend
npm install
npm run dev
```

Vite dev server starts on `http://localhost:5173` and proxies `/api/*` to the FastAPI backend at `http://localhost:8000`.

## Running tests

```bash
# From repo root
pytest backend/tests/test_preconditions.py -v
```

## Phase 0 gate

Once both servers are running, verify:

1. Backend startup log shows:
   ```
   Preconditions met — pilot.db table counts: sources=19, nsa_rules=59, ambulance_fee_schedule=520
   ```
2. `curl http://localhost:8000/health` returns `{"status":"ok", ...}` with correct counts.
3. `http://localhost:5173` displays the status table with all three row counts.
4. All 6 tests in `test_preconditions.py` pass.

**If the precondition check fails:** the Data Completion Addendum tasks have not been run yet in the `medical_billing_data` repository. Run them first, then copy the resulting `pilot.db` snapshot to `data/pilot.db`.
