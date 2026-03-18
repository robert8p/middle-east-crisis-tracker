from __future__ import annotations

import logging

from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from .config import get_settings
from .db import Base, engine
from .logging_config import configure_logging
from .routers.api import router as api_router
from .routers.admin import router as admin_router
from .routers.frontend import router as frontend_router
from .services.ingest_service import IngestService
from .utils.time import utcnow_naive

configure_logging()
logger = logging.getLogger(__name__)

settings = get_settings()
app = FastAPI(title="Middle East Crisis Tracker", version="1.0.0")

Base.metadata.create_all(bind=engine)

app.mount("/static", StaticFiles(directory="backend/app/static"), name="static")
app.include_router(frontend_router)
app.include_router(api_router)
app.include_router(admin_router)

scheduler: BackgroundScheduler | None = None


@app.get("/health")
def health():
    return {"ok": True, "service": "middle-east-crisis-tracker", "generated_at_utc": utcnow_naive().isoformat()}


@app.on_event("startup")
def startup_event():
    global scheduler
    try:
        IngestService().run_ingestion()
    except Exception as exc:
        logger.exception("initial_ingestion_failed: %s", exc)

    if settings.app_enable_background_refresh:
        scheduler = BackgroundScheduler()
        scheduler.add_job(IngestService().run_ingestion, "interval", minutes=settings.app_refresh_interval_minutes, max_instances=1, coalesce=True)
        scheduler.start()
        logger.info("scheduler_started interval_minutes=%s", settings.app_refresh_interval_minutes)


@app.on_event("shutdown")
def shutdown_event():
    if scheduler:
        scheduler.shutdown(wait=False)