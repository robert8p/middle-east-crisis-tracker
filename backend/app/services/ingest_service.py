from __future__ import annotations

import logging
from datetime import datetime

from sqlalchemy import delete, select

from ..config import get_settings
from ..db import db_session
from ..models import ClusterRecord, EventRecord, SourceHealthRecord
from ..schemas import EventItem, ClusterItem, SourceHealthItem
from ..sources.registry import get_sources
from ..utils.time import utcnow_naive, hours_ago
from .clustering import cluster_events, similarity
from .normalization import is_relevant_item, normalize_raw_item
from .scoring import confidence_score, materiality_score, novelty_score

logger = logging.getLogger(__name__)


class IngestService:
    def __init__(self) -> None:
        self.settings = get_settings()

    def _load_recent_events(self) -> list[EventRecord]:
        with db_session() as db:
            stmt = select(EventRecord).where(EventRecord.created_at_utc >= hours_ago(self.settings.app_event_lookback_hours))
            return list(db.execute(stmt).scalars())

    def _persist_source_health(self, item: SourceHealthItem) -> None:
        with db_session() as db:
            existing = db.execute(select(SourceHealthRecord).where(SourceHealthRecord.source_name == item.source_name)).scalar_one_or_none()
            if existing is None:
                existing = SourceHealthRecord(source_name=item.source_name, source_type=item.source_type)
                db.add(existing)
            existing.source_type = item.source_type
            existing.enabled = item.enabled
            existing.last_success_utc = item.last_success_utc
            existing.last_attempt_utc = item.last_attempt_utc
            existing.last_error = item.last_error
            existing.last_response_time_ms = item.last_response_time_ms
            existing.fetch_failures = item.fetch_failures
            existing.items_ingested_last_run = item.items_ingested_last_run
            existing.cache_age_seconds = item.cache_age_seconds
            existing.degraded = item.degraded

    def _persist_events(self, events: list[EventItem]) -> None:
        with db_session() as db:
            existing_uids = set(db.execute(select(EventRecord.event_uid)).scalars())
            for item in events:
                if item.event_uid in existing_uids:
                    continue
                db.add(
                    EventRecord(
                        event_uid=item.event_uid,
                        title=item.title,
                        source=item.source,
                        source_type=item.source_type,
                        url=item.url,
                        published_at_utc=item.published_at_utc,
                        detected_event_time_utc=item.detected_event_time_utc,
                        countries_involved=item.countries_involved,
                        actors_involved=item.actors_involved,
                        locations=item.locations,
                        event_type=item.event_type,
                        asset_exposure_tags=item.asset_exposure_tags,
                        confidence_score=item.confidence_score,
                        confidence_band=item.confidence_band,
                        materiality_score=item.materiality_score,
                        materiality_band=item.materiality_band,
                        novelty_score=item.novelty_score,
                        corroboration_count=item.corroboration_count,
                        summary=item.summary,
                        why_it_matters=item.why_it_matters,
                        operational_impact=item.operational_impact,
                        market_impact=item.market_impact,
                        uncertainty_notes=item.uncertainty_notes,
                        raw_text=item.raw_text,
                        raw_payload=item.raw_payload,
                        fingerprint=item.fingerprint,
                    )
                )

    def _persist_clusters(self, clusters: list[ClusterItem]) -> None:
        with db_session() as db:
            db.execute(delete(ClusterRecord))
            for item in clusters:
                db.add(
                    ClusterRecord(
                        cluster_uid=item.cluster_uid,
                        canonical_title=item.canonical_title,
                        canonical_event_uid=item.canonical_event_uid,
                        event_uids=item.event_uids,
                        source_names=item.source_names,
                        time_min_utc=item.time_min_utc,
                        time_max_utc=item.time_max_utc,
                        countries_involved=item.countries_involved,
                        actors_involved=item.actors_involved,
                        locations=item.locations,
                        event_type=item.event_type,
                        asset_exposure_tags=item.asset_exposure_tags,
                        confidence_score=item.confidence_score,
                        confidence_band=item.confidence_band,
                        materiality_score=item.materiality_score,
                        materiality_band=item.materiality_band,
                        novelty_score=item.novelty_score,
                        corroboration_count=item.corroboration_count,
                        summary=item.summary,
                        why_it_matters=item.why_it_matters,
                        operational_impact=item.operational_impact,
                        market_impact=item.market_impact,
                        uncertainty_notes=item.uncertainty_notes,
                        supporting_sources=item.supporting_sources,
                    )
                )

    def run_ingestion(self) -> dict:
        recent_records = self._load_recent_events()
        recent_event_items = [
            EventItem(
                event_uid=r.event_uid,
                title=r.title,
                source=r.source,
                source_type=r.source_type,
                url=r.url,
                published_at_utc=r.published_at_utc,
                detected_event_time_utc=r.detected_event_time_utc,
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
                raw_text=r.raw_text,
                raw_payload=r.raw_payload,
                fingerprint=r.fingerprint,
            )
            for r in recent_records
        ]

        source_health_items: list[SourceHealthItem] = []
        normalized: list[EventItem] = []

        for source in get_sources():
            start = utcnow_naive()
            result = source.fetch()
            health = SourceHealthItem(
                source_name=result.source_name,
                source_type=result.source_type,
                enabled=source.enabled,
                last_attempt_utc=start,
                last_success_utc=None if result.error else utcnow_naive(),
                last_error=result.error,
                last_response_time_ms=result.response_time_ms,
                fetch_failures=1 if result.error else 0,
                items_ingested_last_run=len(result.items),
                cache_age_seconds=0,
                degraded=bool(result.error),
            )

            if result.error:
                logger.warning("source_failed source=%s error=%s", result.source_name, result.error)
                self._persist_source_health(health)
                source_health_items.append(health)
                continue

            for raw in result.items:
                try:
                    if not is_relevant_item(raw):
                        continue
                    item = normalize_raw_item(raw)
                    # Approximate corroboration against recent + current normalized items
                    peers = recent_event_items + normalized
                    item.corroboration_count = sum(
                        1
                        for peer in peers
                        if peer.source != item.source and similarity(item, peer) >= 0.60
                    )
                    item.confidence_score, item.confidence_band = confidence_score(item)
                    item.materiality_score, item.materiality_band = materiality_score(item)
                    similarity_to_recent = max((similarity(item, peer) for peer in peers), default=0.0)
                    item.novelty_score = novelty_score(item, similarity_to_recent)
                    normalized.append(item)
                except Exception as exc:
                    logger.warning("item_normalization_failed source=%s title=%s error=%s", result.source_name, raw.get("title", "")[:120], exc)

            self._persist_source_health(health)
            source_health_items.append(health)

        self._persist_events(normalized)

        # Load all recent again after persistence, then cluster
        all_records = self._load_recent_events()
        all_items = [
            EventItem(
                event_uid=r.event_uid,
                title=r.title,
                source=r.source,
                source_type=r.source_type,
                url=r.url,
                published_at_utc=r.published_at_utc,
                detected_event_time_utc=r.detected_event_time_utc,
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
                raw_text=r.raw_text,
                raw_payload=r.raw_payload,
                fingerprint=r.fingerprint,
            )
            for r in all_records
        ]

        clusters = cluster_events(all_items)
        self._persist_clusters(clusters)

        return {
            "ingested_events": len(normalized),
            "cluster_count": len(clusters),
            "sources_total": len(source_health_items),
            "sources_degraded": sum(1 for s in source_health_items if s.degraded),
            "generated_at_utc": utcnow_naive().isoformat(),
        }

    def recluster(self) -> dict:
        all_records = self._load_recent_events()
        all_items = [
            EventItem(
                event_uid=r.event_uid,
                title=r.title,
                source=r.source,
                source_type=r.source_type,
                url=r.url,
                published_at_utc=r.published_at_utc,
                detected_event_time_utc=r.detected_event_time_utc,
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
                raw_text=r.raw_text,
                raw_payload=r.raw_payload,
                fingerprint=r.fingerprint,
            )
            for r in all_records
        ]
        clusters = cluster_events(all_items)
        self._persist_clusters(clusters)
        return {"cluster_count": len(clusters), "generated_at_utc": utcnow_naive().isoformat()}