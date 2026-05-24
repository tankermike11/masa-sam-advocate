"""
FastAPI application entry point.

Startup (lifespan):
  1. check_preconditions() — logs a warning and continues in degraded mode if
     pilot.db tables are missing; does not exit so the container stays alive
     during the Railway volume seed window.
  2. init_app_db() — creates data/app.db and applies schema (idempotent)
  3. logs confirmed precondition row counts

Run from repo root:
  uvicorn backend.main:app --reload
"""

import logging
import sys
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from backend.db.app_db import get_app_db_path, init_app_db
from backend.db.pilot import get_pilot_db_path
from backend.db.preconditions import PreconditionError, check_preconditions
from backend.routers.cases import router as cases_router
from backend.routers.codes import router as codes_router
from backend.routers.escalation import router as escalation_router
from backend.routers.health import router as health_router
from backend.routers.workflows import router as workflows_router

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

FRONTEND_DIST = Path(__file__).parent.parent / "frontend" / "dist"


@asynccontextmanager
async def lifespan(app: FastAPI):
    pilot_db_path = get_pilot_db_path()
    logger.info(f"Checking pilot.db preconditions at: {pilot_db_path}")

    try:
        counts = check_preconditions(pilot_db_path)
        logger.info(
            "Preconditions met — pilot.db table counts: "
            + ", ".join(f"{k}={v}" for k, v in counts.items())
        )
    except PreconditionError as e:
        logger.warning("Preconditions not met — starting in degraded mode: " + str(e))

    app_db_path = get_app_db_path()
    init_app_db(app_db_path)
    logger.info(f"app.db initialized at: {app_db_path}")

    yield


app = FastAPI(
    title="SAM Medical Bill Advocate",
    description="MASA SAM — AI-assisted medical bill advocacy prototype",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(health_router)
app.include_router(cases_router)
app.include_router(workflows_router)
app.include_router(escalation_router)
app.include_router(codes_router)

if FRONTEND_DIST.exists():
    app.mount(
        "/assets",
        StaticFiles(directory=FRONTEND_DIST / "assets"),
        name="assets",
    )

    @app.get("/{full_path:path}", include_in_schema=False)
    async def serve_spa(full_path: str):
        return FileResponse(FRONTEND_DIST / "index.html")
