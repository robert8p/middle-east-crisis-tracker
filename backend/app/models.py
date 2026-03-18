from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, Integer, String, Text, JSON, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from .db import Base


class EventRecord(Base):
    __tablename__ = "events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    event_uid: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    title: Mapped[str] = mapped_column(String(500))
    source: Mapped[str] = mapped_column(String(120), index=True)
    source_type: Mapped[str] = mapped_column(String(50))
    url: Mapped[str] = mapped_column(String(1000))
    published_at_utc: Mapped[datetime | None] = mapped_column(DateTime(timezone=False), nullable=True)
    detected_event_time_utc: Mapped[datetime | None] = mapped_column(DateTime(timezone=False), nullable=True)
    countries_involved: Mapped[list] = mapped_column(JSON, default=list)
    actors_involved: Mapped[list] = mapped_column(JSON, default=list)
    locations: Mapped[list] = mapped_column(JSON, default=list)
    event_type: Mapped[str] = mapped_column(String(80), index=True)
    asset_exposure_tags: Mapped[list] = mapped_column(JSON, default=list)
    confidence_score: Mapped[float] = mapped_column(Float, default=0.0)
    confidence_band: Mapped[str] = mapped_column(String(32), default="Unverified")
    materiality_score: Mapped[float] = mapped_column(Float, default=0.0)
    materiality_band: Mapped[str] = mapped_column(String(32), default="Low")
    novelty_score: Mapped[float] = mapped_column(Float, default=0.0)
    corroboration_count: Mapped[int] = mapped_column(Integer, default=0)
    summary: Mapped[str] = mapped_column(Text, default="")
    why_it_matters: Mapped[str] = mapped_column(Text, default="")
    operational_impact: Mapped[str] = mapped_column(Text, default="")
    market_impact: Mapped[str] = mapped_column(Text, default="")
    uncertainty_notes: Mapped[str] = mapped_column(Text, default="")
    raw_text: Mapped[str] = mapped_column(Text, default="")
    raw_payload: Mapped[dict] = mapped_column(JSON, default=dict)
    fingerprint: Mapped[str] = mapped_column(String(128), index=True)
    created_at_utc: Mapped[datetime] = mapped_column(DateTime(timezone=False), default=datetime.utcnow)
    updated_at_utc: Mapped[datetime] = mapped_column(DateTime(timezone=False), default=datetime.utcnow, onupdate=datetime.utcnow)


class ClusterRecord(Base):
    __tablename__ = "clusters"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    cluster_uid: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    canonical_title: Mapped[str] = mapped_column(String(500))
    canonical_event_uid: Mapped[str] = mapped_column(String(128), index=True)
    event_uids: Mapped[list] = mapped_column(JSON, default=list)
    source_names: Mapped[list] = mapped_column(JSON, default=list)
    time_min_utc: Mapped[datetime | None] = mapped_column(DateTime(timezone=False), nullable=True)
    time_max_utc: Mapped[datetime | None] = mapped_column(DateTime(timezone=False), nullable=True)
    countries_involved: Mapped[list] = mapped_column(JSON, default=list)
    actors_involved: Mapped[list] = mapped_column(JSON, default=list)
    locations: Mapped[list] = mapped_column(JSON, default=list)
    event_type: Mapped[str] = mapped_column(String(80), index=True)
    asset_exposure_tags: Mapped[list] = mapped_column(JSON, default=list)
    confidence_score: Mapped[float] = mapped_column(Float, default=0.0)
    confidence_band: Mapped[str] = mapped_column(String(32), default="Unverified")
    materiality_score: Mapped[float] = mapped_column(Float, default=0.0)
    materiality_band: Mapped[str] = mapped_column(String(32), default="Low")
    novelty_score: Mapped[float] = mapped_column(Float, default=0.0)
    corroboration_count: Mapped[int] = mapped_column(Integer, default=0)
    summary: Mapped[str] = mapped_column(Text, default="")
    why_it_matters: Mapped[str] = mapped_column(Text, default="")
    operational_impact: Mapped[str] = mapped_column(Text, default="")
    market_impact: Mapped[str] = mapped_column(Text, default="")
    uncertainty_notes: Mapped[str] = mapped_column(Text, default="")
    supporting_sources: Mapped[list] = mapped_column(JSON, default=list)
    created_at_utc: Mapped[datetime] = mapped_column(DateTime(timezone=False), default=datetime.utcnow)
    updated_at_utc: Mapped[datetime] = mapped_column(DateTime(timezone=False), default=datetime.utcnow, onupdate=datetime.utcnow)


class SourceHealthRecord(Base):
    __tablename__ = "source_health"
    __table_args__ = (UniqueConstraint("source_name", name="uq_source_health_name"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    source_name: Mapped[str] = mapped_column(String(120), index=True)
    source_type: Mapped[str] = mapped_column(String(50))
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    last_success_utc: Mapped[datetime | None] = mapped_column(DateTime(timezone=False), nullable=True)
    last_attempt_utc: Mapped[datetime | None] = mapped_column(DateTime(timezone=False), nullable=True)
    last_error: Mapped[str] = mapped_column(Text, default="")
    last_response_time_ms: Mapped[int] = mapped_column(Integer, default=0)
    fetch_failures: Mapped[int] = mapped_column(Integer, default=0)
    items_ingested_last_run: Mapped[int] = mapped_column(Integer, default=0)
    cache_age_seconds: Mapped[int] = mapped_column(Integer, default=0)
    degraded: Mapped[bool] = mapped_column(Boolean, default=False)