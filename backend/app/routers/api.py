from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import ClusterRecord, EventRecord, SourceHealthRecord
from ..schemas import ClusterItem, DashboardResponse, SourceHealthItem
from ..services.situation import build_situation
from ..utils.time import utcnow_naive

router = APIRouter(prefix="/api", tags=["api"])


@router.get("/dashboard", response_model=DashboardResponse)
def dashboard(db: Session = Depends(get_db)) -> DashboardResponse:
    cluster_rows = list(
        db.execute(
            select(ClusterRecord).order_by(ClusterRecord.materiality_score.desc(), ClusterRecord.confidence_score.desc(), ClusterRecord.time_max_utc.desc().nullslast())
        ).scalars()
    )
    source_rows = list(db.execute(select(SourceHealthRecord).order_by(SourceHealthRecord.source_name.asc())).scalars())
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
        for r in cluster_rows
    ]
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

    stats = {
        "cluster_count": len(clusters),
        "source_count": len(sources),
        "degraded_sources": sum(1 for s in sources if s.degraded),
        "event_count": db.execute(select(func.count()).select_from(EventRecord)).scalar_one(),
        "critical_clusters": sum(1 for c in clusters if c.materiality_band == "Critical"),
        "shipping_exposed_clusters": sum(1 for c in clusters if "shipping" in c.asset_exposure_tags),
    }

    return DashboardResponse(
        generated_at_utc=utcnow_naive(),
        situation=build_situation(clusters),
        clusters=clusters,
        sources=sources,
        stats=stats,
    )