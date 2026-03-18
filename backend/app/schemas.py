from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class EventItem(BaseModel):
    event_uid: str
    title: str
    source: str
    source_type: str
    url: str
    published_at_utc: datetime | None = None
    detected_event_time_utc: datetime | None = None
    countries_involved: list[str] = Field(default_factory=list)
    actors_involved: list[str] = Field(default_factory=list)
    locations: list[str] = Field(default_factory=list)
    event_type: str = "general_update"
    asset_exposure_tags: list[str] = Field(default_factory=list)
    confidence_score: float = 0.0
    confidence_band: str = "Unverified"
    materiality_score: float = 0.0
    materiality_band: str = "Low"
    novelty_score: float = 0.0
    corroboration_count: int = 0
    summary: str = ""
    why_it_matters: str = ""
    operational_impact: str = ""
    market_impact: str = ""
    uncertainty_notes: str = ""
    raw_text: str = ""
    raw_payload: dict[str, Any] = Field(default_factory=dict)
    fingerprint: str = ""


class ClusterItem(BaseModel):
    cluster_uid: str
    canonical_title: str
    canonical_event_uid: str
    event_uids: list[str] = Field(default_factory=list)
    source_names: list[str] = Field(default_factory=list)
    time_min_utc: datetime | None = None
    time_max_utc: datetime | None = None
    countries_involved: list[str] = Field(default_factory=list)
    actors_involved: list[str] = Field(default_factory=list)
    locations: list[str] = Field(default_factory=list)
    event_type: str = "general_update"
    asset_exposure_tags: list[str] = Field(default_factory=list)
    confidence_score: float = 0.0
    confidence_band: str = "Unverified"
    materiality_score: float = 0.0
    materiality_band: str = "Low"
    novelty_score: float = 0.0
    corroboration_count: int = 0
    summary: str = ""
    why_it_matters: str = ""
    operational_impact: str = ""
    market_impact: str = ""
    uncertainty_notes: str = ""
    supporting_sources: list[dict[str, Any]] = Field(default_factory=list)


class SourceHealthItem(BaseModel):
    source_name: str
    source_type: str
    enabled: bool = True
    last_success_utc: datetime | None = None
    last_attempt_utc: datetime | None = None
    last_error: str = ""
    last_response_time_ms: int = 0
    fetch_failures: int = 0
    items_ingested_last_run: int = 0
    cache_age_seconds: int = 0
    degraded: bool = False


class SituationSummary(BaseModel):
    label: str
    rationale: str
    confidence: str
    watchlist_scheduled: list[dict[str, str]] = Field(default_factory=list)
    watchlist_inferred: list[dict[str, str]] = Field(default_factory=list)
    market_transmission: list[dict[str, str]] = Field(default_factory=list)


class DashboardResponse(BaseModel):
    generated_at_utc: datetime
    situation: SituationSummary
    clusters: list[ClusterItem]
    sources: list[SourceHealthItem]
    stats: dict[str, Any]