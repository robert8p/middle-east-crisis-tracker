from __future__ import annotations

from datetime import datetime, timedelta

from ..schemas import EventItem, ClusterItem
from ..utils.text import jaccard, slug_hash, tokenize


def similarity(a: EventItem, b: EventItem) -> float:
    token_sim = jaccard(tokenize(a.title + " " + a.summary), tokenize(b.title + " " + b.summary))
    actor_sim = jaccard(a.actors_involved, b.actors_involved)
    country_sim = jaccard(a.countries_involved, b.countries_involved)
    loc_sim = jaccard(a.locations, b.locations)
    fp_bonus = 0.15 if a.fingerprint == b.fingerprint else 0.0

    time_bonus = 0.0
    if a.published_at_utc and b.published_at_utc:
        delta = abs(a.published_at_utc - b.published_at_utc)
        if delta <= timedelta(hours=6):
            time_bonus = 0.15
        elif delta <= timedelta(hours=18):
            time_bonus = 0.08

    return min(token_sim * 0.45 + actor_sim * 0.20 + country_sim * 0.10 + loc_sim * 0.10 + fp_bonus + time_bonus, 1.0)


def _event_time_sort_value(event: EventItem) -> float:
    dt = event.published_at_utc or event.detected_event_time_utc
    if isinstance(dt, datetime):
        return dt.timestamp()
    inserted_order = (event.raw_payload or {}).get("inserted_order", 0)
    try:
        return float(inserted_order)
    except (TypeError, ValueError):
        return 0.0


def _cluster_time_sort_value(cluster: ClusterItem) -> float:
    dt = cluster.time_max_utc or cluster.time_min_utc
    if isinstance(dt, datetime):
        return dt.timestamp()
    return 0.0


def cluster_events(events: list[EventItem]) -> list[ClusterItem]:
    if not events:
        return []

    groups: list[list[EventItem]] = []
    threshold = 0.54

    for event in sorted(events, key=_event_time_sort_value, reverse=True):
        placed = False
        for group in groups:
            sim = max(similarity(event, existing) for existing in group)
            if sim >= threshold:
                group.append(event)
                placed = True
                break
        if not placed:
            groups.append([event])

    clusters: list[ClusterItem] = []
    for group in groups:
        canonical = sorted(group, key=lambda e: (e.materiality_score, e.confidence_score, len(e.actors_involved), len(e.locations)), reverse=True)[0]
        cluster_uid = slug_hash("|".join(sorted(e.event_uid for e in group)))
        sources = []
        source_names = sorted(set(e.source for e in group))
        countries = sorted(set(x for e in group for x in e.countries_involved))
        actors = sorted(set(x for e in group for x in e.actors_involved))
        locations = sorted(set(x for e in group for x in e.locations))
        exposures = sorted(set(x for e in group for x in e.asset_exposure_tags))
        corroboration_count = max(len(source_names) - 1, 0)
        for e in group:
            sources.append(
                {
                    "source": e.source,
                    "url": e.url,
                    "title": e.title,
                    "published_at_utc": e.published_at_utc.isoformat() if e.published_at_utc else None,
                    "confidence_band": e.confidence_band,
                }
            )
        clusters.append(
            ClusterItem(
                cluster_uid=cluster_uid,
                canonical_title=canonical.title,
                canonical_event_uid=canonical.event_uid,
                event_uids=[e.event_uid for e in group],
                source_names=source_names,
                time_min_utc=min((e.published_at_utc for e in group if e.published_at_utc), default=None),
                time_max_utc=max((e.published_at_utc for e in group if e.published_at_utc), default=None),
                countries_involved=countries,
                actors_involved=actors,
                locations=locations,
                event_type=canonical.event_type,
                asset_exposure_tags=exposures,
                confidence_score=max(e.confidence_score for e in group),
                confidence_band=canonical.confidence_band,
                materiality_score=max(e.materiality_score for e in group),
                materiality_band=canonical.materiality_band,
                novelty_score=max(e.novelty_score for e in group),
                corroboration_count=corroboration_count,
                summary=canonical.summary,
                why_it_matters=canonical.why_it_matters,
                operational_impact=canonical.operational_impact,
                market_impact=canonical.market_impact,
                uncertainty_notes=canonical.uncertainty_notes,
                supporting_sources=sources,
            )
        )
    return sorted(clusters, key=lambda c: (c.materiality_score, c.confidence_score, c.time_max_utc or c.time_min_utc), reverse=True)