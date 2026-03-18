from __future__ import annotations

from datetime import datetime

from ..schemas import EventItem
from ..utils.time import utcnow_naive

SOURCE_BASE = {
    "official": 0.82,
    "institutional": 0.78,
    "maritime": 0.80,
    "wire": 0.77,
    "aggregator": 0.58,
    "unknown": 0.45,
}

EVENT_MATERIALITY = {
    "military_strike": 0.88,
    "missile_or_drone_activity": 0.82,
    "shipping_disruption": 0.86,
    "oil_or_energy_issue": 0.83,
    "sanctions_or_designation": 0.74,
    "proxy_militia_action": 0.79,
    "market_policy_response": 0.70,
    "aviation_or_airspace_disruption": 0.66,
    "diplomatic_statement": 0.48,
    "humanitarian_development": 0.50,
    "general_update": 0.35,
}

MAJOR_ACTORS = {
    "IDF", "Iran MFA", "Israel MFA", "U.S. Treasury", "White House", "UN Security Council",
    "Hamas", "Hezbollah", "Houthis"
}


def _recency_score(published_at_utc: datetime | None) -> float:
    if not published_at_utc:
        return 0.35
    age_hours = max((utcnow_naive() - published_at_utc).total_seconds() / 3600.0, 0.0)
    if age_hours <= 4:
        return 1.0
    if age_hours <= 12:
        return 0.82
    if age_hours <= 24:
        return 0.68
    if age_hours <= 48:
        return 0.52
    return 0.35


def _specificity_score(item: EventItem) -> float:
    score = 0.30
    if item.countries_involved:
        score += 0.15
    if item.actors_involved:
        score += 0.15
    if item.locations:
        score += 0.15
    if item.asset_exposure_tags:
        score += 0.10
    if item.url:
        score += 0.05
    if len(item.raw_text) > 80:
        score += 0.10
    return min(score, 1.0)


def _official_confirmation(item: EventItem) -> float:
    if item.source_type in {"official", "institutional", "maritime"}:
        return 1.0
    official_actors = {"U.S. Treasury", "White House", "UN Security Council", "Iran MFA", "Israel MFA", "UKMTO"}
    return 0.9 if any(actor in official_actors for actor in item.actors_involved) else 0.2


def _direct_reporting(item: EventItem) -> float:
    lowered = item.title.lower()
    if any(word in lowered for word in ["analysis", "opinion", "commentary", "explainer"]):
        return 0.35
    if any(word in lowered for word in ["statement", "press release", "remarks", "advisory", "update"]):
        return 0.9
    return 0.7


def confidence_score(item: EventItem) -> tuple[float, str]:
    base = SOURCE_BASE.get(item.source_type, SOURCE_BASE["unknown"])
    corroboration = min(item.corroboration_count * 0.12, 0.30)
    score = (
        base * 0.30
        + _recency_score(item.published_at_utc) * 0.20
        + _specificity_score(item) * 0.20
        + _official_confirmation(item) * 0.15
        + _direct_reporting(item) * 0.10
        + corroboration * 0.05
    )
    score = max(0.0, min(score, 1.0))
    if score >= 0.78:
        band = "High confidence"
    elif score >= 0.62:
        band = "Moderate confidence"
    elif score >= 0.45:
        band = "Low confidence"
    else:
        band = "Unverified"
    return round(score, 4), band


def materiality_score(item: EventItem) -> tuple[float, str]:
    base = EVENT_MATERIALITY.get(item.event_type, EVENT_MATERIALITY["general_update"])
    actor_boost = 0.05 if any(actor in MAJOR_ACTORS for actor in item.actors_involved) else 0.0
    exposure_boost = min(len(item.asset_exposure_tags) * 0.04, 0.16)
    location_boost = 0.05 if any(loc in {"Strait of Hormuz", "Red Sea", "Gaza"} for loc in item.locations) else 0.0
    recency = _recency_score(item.published_at_utc) * 0.08
    score = min(base + actor_boost + exposure_boost + location_boost + recency, 1.0)
    if score >= 0.82:
        band = "Critical"
    elif score >= 0.66:
        band = "High"
    elif score >= 0.48:
        band = "Medium"
    else:
        band = "Low"
    return round(score, 4), band


def novelty_score(item: EventItem, similarity_to_recent: float) -> float:
    freshness = _recency_score(item.published_at_utc)
    score = max(0.0, min((1 - similarity_to_recent) * 0.65 + freshness * 0.35, 1.0))
    return round(score, 4)