from datetime import datetime, timedelta, UTC

from backend.app.schemas import EventItem
from backend.app.services.scoring import confidence_score, materiality_score


def test_confidence_scores_official_higher():
    recent = datetime.now(UTC).replace(tzinfo=None) - timedelta(hours=1)
    official = EventItem(
        event_uid="1",
        title="Treasury sanctions facilitators linked to regional network",
        source="U.S. Treasury",
        source_type="official",
        url="https://example.com",
        published_at_utc=recent,
        countries_involved=["Iran", "United States"],
        actors_involved=["U.S. Treasury"],
        locations=["Tehran"],
        event_type="sanctions_or_designation",
        asset_exposure_tags=["oil"],
        raw_text="Treasury sanctions facilitators linked to regional network",
    )
    aggregator = official.model_copy(update={"source_type": "aggregator", "source": "Google News"})
    off_score, _ = confidence_score(official)
    agg_score, _ = confidence_score(aggregator)
    assert off_score > agg_score


def test_materiality_shipping_high():
    recent = datetime.now(UTC).replace(tzinfo=None) - timedelta(hours=2)
    item = EventItem(
        event_uid="2",
        title="UKMTO advisory reports vessel attack in Strait of Hormuz",
        source="UKMTO",
        source_type="maritime",
        url="https://example.com",
        published_at_utc=recent,
        countries_involved=["Oman"],
        actors_involved=["UKMTO"],
        locations=["Strait of Hormuz"],
        event_type="shipping_disruption",
        asset_exposure_tags=["shipping", "oil"],
        raw_text="vessel attack strait of hormuz shipping advisory",
    )
    score, band = materiality_score(item)
    assert score >= 0.82
    assert band in {"Critical", "High"}