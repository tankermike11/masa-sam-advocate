"""
FastAPI application entry point.

Startup (lifespan):
  1. check_preconditions() — blocks startup and exits non-zero if pilot.db
     tables are missing or empty; logs the full Addendum reference on failure
  2. init_app_db() — creates data/app.db and applies schema (idempotent)
  3. logs confirmed precondition row counts

Run from repo root:
  uvicorn backend.main:app --reload
"""

import logging
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI

from backend.db.app_db import get_app_db_path, init_app_db
from backend.db.pilot import get_pilot_db_path
from backend.db.preconditions import PreconditionError, check_preconditions
from backend.routers.health import router as health_router

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    pilot_db_path = get_pilot_db_path()
    logger.info(f"Checking pilot.db preconditions at: {pilot_db_path}")

    try:
        counts = check_preconditions(pilot_db_path)
    except PreconditionError as e:
        logger.critical("\n" + "=" * 70)
        logger.critical(str(e))
        logger.critical("=" * 70 + "\n")
        sys.exit(1)

    logger.info(
        "Preconditions met — pilot.db table counts: "
        + ", ".join(f"{k}={v}" for k, v in counts.items())
    )

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
