# Railway Deployment — Claude Code Requirements

## Context

This is a billing advocacy demo app with:
- **Backend**: FastAPI + Python 3.12, SQLite via stdlib `sqlite3` (no ORM)
- **Frontend**: React 18 + TypeScript + Vite
- **Databases**: `pilot.db` (455 MB, read-only reference data) and `app.db` (writable case store)
- **Config files**: `escalation_rules.yaml` and `pricing_rules.yaml`

The app currently runs as two local processes (backend on one port, frontend dev server on another). The goal is to deploy it as a single service on Railway with a persistent volume holding both SQLite files.

Assume the standard project layout:
```
/
├── backend/
│   ├── main.py
│   ├── requirements.txt
│   ├── data/
│   │   ├── pilot.db          ← 455MB, read-only reference data
│   │   ├── escalation_rules.yaml
│   │   └── pricing_rules.yaml
│   ├── db/
│   │   ├── pilot.py          ← read-only context manager
│   │   ├── app_db.py         ← writable context manager + init_app_db()
│   │   └── preconditions.py  ← startup gate
│   └── ... (all other modules)
├── frontend/
│   ├── package.json
│   ├── vite.config.ts
│   ├── src/
│   │   └── lib/
│   │       └── api.ts        ← only file that calls fetch()
│   └── ...
└── (repo root)
```

---

## Required Changes

### 1. Create `Dockerfile` at repo root

Multi-stage build: React first, then Python. `pilot.db` is **not** copied into the image — it lives on the Railway volume.

```dockerfile
# Stage 1: build React
FROM node:20-alpine AS frontend-build
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# Stage 2: Python runtime
FROM python:3.12-slim
WORKDIR /app

COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ ./backend/

# Copy built React assets from stage 1
COPY --from=frontend-build /app/frontend/dist ./frontend/dist

# Volume mount point — pilot.db and app.db live here at runtime
RUN mkdir -p /data

ENV PYTHONPATH=/app
ENV DATA_DIR=/data

EXPOSE 8000
CMD ["sh", "-c", "uvicorn backend.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
```

---

### 2. Create `railway.toml` at repo root

```toml
[build]
builder = "DOCKERFILE"
dockerfilePath = "Dockerfile"

[deploy]
healthcheckPath = "/health"
healthcheckTimeout = 30
restartPolicyType = "ON_FAILURE"
restartPolicyMaxRetries = 3
```

---

### 3. Modify `backend/db/pilot.py` — read path from environment

Currently the path to `pilot.db` is likely hardcoded or relative. Change it to read from the `PILOT_DB_PATH` environment variable, with a local fallback:

```python
import os
from pathlib import Path

PILOT_DB_PATH = Path(os.getenv("PILOT_DB_PATH", "backend/data/pilot.db"))
```

Use `PILOT_DB_PATH` everywhere this module references the database file. Do not change the read-only connection logic (`file:path?mode=ro`) — only the path resolution.

---

### 4. Modify `backend/db/app_db.py` — read path from environment

Same pattern:

```python
import os
from pathlib import Path

APP_DB_PATH = Path(os.getenv("APP_DB_PATH", "backend/data/app.db"))
```

Use `APP_DB_PATH` everywhere this module references the writable database. The `init_app_db()` function must create the file (and its parent directory) if either does not exist — this handles first boot on a fresh volume:

```python
def init_app_db():
    APP_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    # ... rest of existing init logic unchanged
```

---

### 5. Modify `backend/db/preconditions.py` — use env-resolved paths

If this module references `pilot.db` or `app.db` by path directly, update those references to use the same env-resolved constants from `pilot.py` and `app_db.py` respectively. Do not duplicate the path resolution — import the constants.

---

### 6. Modify YAML config loading — support volume path

The two YAML files (`escalation_rules.yaml`, `pricing_rules.yaml`) are currently loaded from a path relative to the source tree. Add a fallback that checks `DATA_DIR` first, so they can optionally be placed on the volume for hot-update without a redeploy:

```python
import os
from pathlib import Path

DATA_DIR = Path(os.getenv("DATA_DIR", "backend/data"))

def _resolve_config(filename: str) -> Path:
    """Check volume path first, fall back to source tree."""
    volume_path = DATA_DIR / filename
    source_path = Path(__file__).parent.parent / "data" / filename
    return volume_path if volume_path.exists() else source_path
```

Apply `_resolve_config("escalation_rules.yaml")` and `_resolve_config("pricing_rules.yaml")` wherever the YAML files are opened. The `@lru_cache` behaviour is unchanged.

---

### 7. Modify `backend/main.py` — serve React and expose health endpoint

**7a. Path resolution at top of file:**

```python
import os
from pathlib import Path

FRONTEND_DIST = Path(__file__).parent.parent / "frontend" / "dist"
```

**7b. Serve React static files** — add this block *after* all API routers are registered, so the catch-all route never shadows `/api/*` or `/health`:

```python
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

if FRONTEND_DIST.exists():
    # Serve hashed asset files (JS, CSS, images)
    app.mount(
        "/assets",
        StaticFiles(directory=FRONTEND_DIST / "assets"),
        name="assets",
    )

    @app.get("/{full_path:path}", include_in_schema=False)
    async def serve_spa(full_path: str):
        """Catch-all: return index.html for all non-API routes (React Router)."""
        return FileResponse(FRONTEND_DIST / "index.html")
```

**7c. Startup event** — call `init_app_db()` on startup so `app.db` is created on a fresh volume automatically:

```python
from backend.db.app_db import init_app_db

@app.on_event("startup")
async def startup():
    init_app_db()
```

If a lifespan context manager already exists instead of `on_event`, add `init_app_db()` inside it.

**7d. Confirm `/health` returns 200** — this endpoint must exist and return a 200-status response for Railway's health check. If it already exists, no change needed. If it is currently raising on precondition failures in a way that returns non-200, ensure it returns `{"status": "degraded"}` with a 200 status rather than a 500, so Railway doesn't restart-loop on a missing `pilot.db` before the volume seed.

---

### 8. Modify `frontend/src/lib/api.ts` — dynamic API base URL

The frontend currently calls the backend at a localhost address. Update `api.ts` so it uses a Vite environment variable in production and falls back to the local dev address:

```typescript
const API_BASE = import.meta.env.VITE_API_URL ?? "";
```

All `fetch()` calls should prepend `API_BASE` to their paths. For example:

```typescript
// Before
const res = await fetch("/cases", { ... });

// After
const res = await fetch(`${API_BASE}/cases`, { ... });
```

When `VITE_API_URL` is not set (production, single-service Railway deploy), `API_BASE` is `""` and all requests go to the same origin — which is correct since FastAPI serves both the API and the React app. When running locally with a separate Vite dev server, set `VITE_API_URL=http://localhost:8000` in `frontend/.env.local`.

---

### 9. Create `frontend/.env.local` (local dev only, not committed)

```
VITE_API_URL=http://localhost:8000
```

Add `frontend/.env.local` to `.gitignore` if not already present.

---

### 10. Create `backend/seed_volume.py` — one-time pilot.db seeder

This script is run once after first deploy via `railway run python backend/seed_volume.py`. It copies `pilot.db` from the Docker image into the persistent volume. It is idempotent — safe to run multiple times.

```python
"""
One-time seed script: copies pilot.db from the image into the persistent volume.
Run once after first deploy: railway run python backend/seed_volume.py
"""
import os
import shutil
import sys
from pathlib import Path

DST = Path(os.getenv("PILOT_DB_PATH", "/data/pilot.db"))

# Candidate source locations (inside the Docker image)
SOURCES = [
    Path("/app/backend/data/pilot.db"),
    Path("backend/data/pilot.db"),
]

def main():
    if DST.exists():
        size_mb = DST.stat().st_size / 1_000_000
        print(f"pilot.db already present at {DST} ({size_mb:.1f} MB). Skipping.")
        return

    src = next((p for p in SOURCES if p.exists()), None)
    if src is None:
        print("ERROR: pilot.db not found in image. Ensure it is present at "
              "backend/data/pilot.db and that the Docker image was built with it.")
        sys.exit(1)

    size_mb = src.stat().st_size / 1_000_000
    print(f"Copying {src} → {DST} ({size_mb:.1f} MB)...")
    DST.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, DST)
    print("Seed complete.")

if __name__ == "__main__":
    main()
```

**Important:** For the seed deploy only, `pilot.db` must be present inside the Docker image. Temporarily add this line to the `Dockerfile` Stage 2, run the seed, then remove it and redeploy:

```dockerfile
# TEMPORARY — remove after seed deploy
COPY backend/data/pilot.db /app/backend/data/pilot.db
```

---

### 11. Create `frontend/vite.config.ts` proxy (local dev only)

If the existing `vite.config.ts` does not already proxy `/api` to the local backend, add it so the frontend dev server works without setting `VITE_API_URL`:

```typescript
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      "/api": {
        target: "http://localhost:8000",
        changeOrigin: true,
      },
      "/cases": {
        target: "http://localhost:8000",
        changeOrigin: true,
      },
      "/codes": {
        target: "http://localhost:8000",
        changeOrigin: true,
      },
      "/health": {
        target: "http://localhost:8000",
        changeOrigin: true,
      },
    },
  },
});
```

Adjust proxy paths to match the actual API route prefixes in use. Do not proxy `/assets` — those are served by Vite itself in dev.

---

## Files to Create (summary)

| File | Action |
|---|---|
| `Dockerfile` | Create |
| `railway.toml` | Create |
| `backend/seed_volume.py` | Create |
| `frontend/.env.local` | Create (do not commit) |

## Files to Modify (summary)

| File | Change |
|---|---|
| `backend/main.py` | Serve React, startup init_app_db, confirm /health |
| `backend/db/pilot.py` | Env-resolved PILOT_DB_PATH |
| `backend/db/app_db.py` | Env-resolved APP_DB_PATH, mkdir in init |
| `backend/db/preconditions.py` | Import path constants rather than redefining |
| `backend/escalation/service.py` (or wherever YAML loads) | Use _resolve_config() |
| `backend/triage/engine.py` (or wherever YAML loads) | Use _resolve_config() |
| `frontend/src/lib/api.ts` | Dynamic API_BASE from VITE_API_URL |
| `frontend/vite.config.ts` | Add dev proxy |
| `.gitignore` | Add frontend/.env.local |

---

## Acceptance Criteria

Before handing off to deployment, confirm:

- [ ] `docker build -t masa-demo .` completes without error locally
- [ ] `docker run -p 8000:8000 -v $(pwd)/backend/data:/data masa-demo` starts successfully
- [ ] `curl http://localhost:8000/health` returns 200
- [ ] `curl http://localhost:8000/` returns the React app HTML
- [ ] `curl http://localhost:8000/codes/search?q=99282` returns JSON (confirms pilot.db is readable)
- [ ] Frontend dev server (`npm run dev` in `/frontend`) proxies API calls correctly to `localhost:8000`

---

## Deployment Steps (run after all code changes pass acceptance criteria)

### Prerequisites
- Railway account at railway.app (free signup)
- Railway CLI installed: `npm install -g @railway/cli`
- GitHub repo with all changes committed and pushed

### Step 1 — Seed deploy (one-time)

Temporarily add `pilot.db` to the Docker image for the first deploy:

```
# In Dockerfile Stage 2, add temporarily:
COPY backend/data/pilot.db /app/backend/data/pilot.db
```

Commit and push this change.

### Step 2 — Create Railway project

```bash
railway login
railway init          # creates a new project, select "Empty Project"
railway link          # links current directory to the project
```

### Step 3 — First deploy

```bash
railway up
```

Watch the build logs. Expect 3–5 minutes for the first build (Node + Python deps + 455MB file).

### Step 4 — Add persistent volume

In the Railway dashboard:
- Open your project → your service → **Volumes** tab
- Click **New Volume**
- Mount path: `/data`
- Size: `2 GB`
- Click **Add**

Railway will automatically redeploy the service with the volume mounted.

### Step 5 — Set environment variables

```bash
railway variables set \
  PILOT_DB_PATH=/data/pilot.db \
  APP_DB_PATH=/data/app.db \
  DATA_DIR=/data \
  PYTHONUNBUFFERED=1
```

Railway will trigger another redeploy. Wait for it to complete.

### Step 6 — Seed pilot.db onto the volume

```bash
railway run python backend/seed_volume.py
```

Expected output:
```
Copying /app/backend/data/pilot.db → /data/pilot.db (455.x MB)...
Seed complete.
```

This takes 10–30 seconds. It is idempotent — safe to re-run.

### Step 7 — Remove pilot.db from Dockerfile and redeploy

Remove the temporary `COPY` line from the Dockerfile, commit, push:

```bash
# Remove: COPY backend/data/pilot.db /app/backend/data/pilot.db
git add Dockerfile
git commit -m "remove seed copy from Dockerfile"
git push
railway up
```

This final deploy produces your lean production image (no 455MB file baked in).

### Step 8 — Verify

```bash
# Get your public URL
railway open

# Check health endpoint
curl https://your-app.up.railway.app/health

# Check a live API call
curl "https://your-app.up.railway.app/codes/search?q=99282"
```

Both should return JSON. Navigate to the URL in a browser — the full React app should load and function identically to local dev.

### Step 9 — Teardown after demo

```bash
# In Railway dashboard: Settings → Danger Zone → Delete Service
# Or to just stop billing without deleting:
# Service → Settings → toggle off "Auto-deploy"
# Then manually stop the service from the dashboard
```

Volume storage ($0.25/GB/mo) continues billing even when the service is stopped. Delete the volume too if you're fully done.

---

## Cost Estimate

| Scenario | Estimated total |
|---|---|
| 1-week demo (light usage, ~4 hrs/day running) | ~$3–5 |
| 2-week demo (always-on) | ~$10–12 |
| Full month always-on | ~$15–18 |

Hobby plan subscription: $5/mo flat. Usage on top is metered per vCPU-minute and GB-RAM-minute. A 512MB RAM service running 4 hours/day for 2 weeks adds roughly $3–6 in usage charges.
