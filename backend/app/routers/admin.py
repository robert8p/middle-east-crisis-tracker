from __future__ import annotations

from fastapi import APIRouter, Depends, Header, HTTPException, Query
from fastapi.responses import PlainTextResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..config import get_settings
from ..db import get_db
from ..models import SourceHealthRecord, ClusterRecord
from ..schemas import SourceHealthItem, ClusterItem
from ..services.export_service import export_csv, export_json
from ..services.ingest_service import IngestService

router = APIRouter(prefix="/admin", tags=["admin"])
settings = get_settings()


def require_admin_token(x_admin_token: str | None = Header(default=None)) -> None:
    if x_admin_token != settings.app_admin_token:
        raise HTTPException(status_code=401, detail="Invalid admin token")


@router.get("/status")
def status(db: Session = Depends(get_db)):
    source_rows = list(db.execute(select(SourceHealthRecord).order_by(SourceHealthRecord.source_name.asc())).scalars())
    cluster_count = db.execute(select(ClusterRecord)).scalars().all()
    return {
        "sources": len(source_rows),
        "degraded_sources": sum(1 for s in source_rows if s.degraded),
        "clusters": len(cluster_count),
        "last_successes": {s.source_name: s.last_success_utc.isoformat() if s.last_success_utc else None for s in source_rows},
    }


@router.get("/sources", response_model=list[SourceHealthItem])
def sources(db: Session = Depends(get_db)):
    rows = list(db.execute(select(SourceHealthRecord).order_by(SourceHealthRecord.source_name.asc())).scalars())
    return [
        SourceHealthItem(
            source_name=r.source_name,
            source_type=r.source_type,
            enabled=r.enabled,
            last_success_utc=r.last_success_utc,
            last_attempt_utc=r.last_attempt_utc,
            last_error=r.last_error,
            last_response_time_ms=r.last_response_time_ms,
            fetch_failures=r.fetch_failures,
            items_ingested_last_run=r.items_ingested_last_run,
            cache_age_seconds=r.cache_age_seconds,
            degraded=r.degraded,
        )
        for r in rows
    ]


@router.post("/reingest", dependencies=[Depends(require_admin_token)])
def reingest():
    return IngestService().run_ingestion()


@router.post("/recluster", dependencies=[Depends(require_admin_token)])
def recluster():
    return IngestService().recluster()


@router.get("/export")
def export(
    format: str = Query(default=None),
    db: Session = Depends(get_db),
):
    fmt = format or settings.app_export_default_format
    rows = list(db.execute(select(ClusterRecord).order_by(ClusterRecord.materiality_score.desc())).scalars())
    clusters = [
        ClusterItem(
            cluster_uid=r.cluster_uid,
            canonical_title=r.canonical_title,
            canonical_event_uid=r.canonical_event_uid,
            event_uids=r.event_uids,
            source_names=r.source_names,
            time_min_utc=r.time_min_utc,
            time_max_utc=r.time_max_utc,
            countries_involved=r.countries_involved,
            actors_involved=r.actors_involved,
            locations=r.locations,
            event_type=r.event_type,
            asset_exposure_tags=r.asset_exposure_tags,
            confidence_score=r.confidence_score,
            confidence_band=r.confidence_band,
            materiality_score=r.materiality_score,
            materiality_band=r.materiality_band,
            novelty_score=r.novelty_score,
            corroboration_count=r.corroboration_count,
            summary=r.summary,
            why_it_matters=r.why_it_matters,
            operational_impact=r.operational_impact,
            market_impact=r.market_impact,
            uncertainty_notes=r.uncertainty_notes,
            supporting_sources=r.supporting_sources,
        )
        for r in rows
    ]
    if fmt == "csv":
        return PlainTextResponse(export_csv(clusters), media_type="text/csv")
    if fmt != "json":
        raise HTTPException(status_code=400, detail="format must be json or csv")
    source_rows = list(db.execute(select(SourceHealthRecord)).scalars())
    sources = [
        SourceHealthItem(
            source_name=r.source_name,
            source_type=r.source_type,
            enabled=r.enabled,
            last_success_utc=r.last_success_utc,
            last_attempt_utc=r.last_attempt_utc,
            last_error=r.last_error,
            last_response_time_ms=r.last_response_time_ms,
            fetch_failures=r.fetch_failures,
            items_ingested_last_run=r.items_ingested_last_run,
            cache_age_seconds=r.cache_age_seconds,
            degraded=r.degraded,
        )
        for r in source_rows
    ]
    return PlainTextResponse(export_json(clusters, sources), media_type="application/json")