from datetime import datetime, timedelta, UTC

from backend.app.schemas import EventItem
from backend.app.services.clustering import cluster_events


def test_near_duplicate_events_cluster_together():
    recent = datetime.now(UTC).replace(tzinfo=None) - timedelta(hours=1)
    a = EventItem(
        event_uid="a",
        title="Vessel struck in Strait of Hormuz, UKMTO says",
        source="UKMTO",
        source_type="maritime",
        url="https://example.com/a",
        published_at_utc=recent,
        countries_involved=["Oman"],
        actors_involved=["UKMTO"],
        locations=["Strait of Hormuz"],
        event_type="shipping_disruption",
        asset_exposure_tags=["shipping", "oil"],
        confidence_score=0.8,
        confidence_band="High confidence",
        materiality_score=0.9,
        materiality_band="Critical",
        novelty_score=0.8,
        summary="A",
        why_it_matters="A",
        operational_impact="A",
        market_impact="A",
        uncertainty_notes="A",
        raw_text="vessel struck in strait of hormuz ukmto says",
        fingerprint="fp1",
    )
    b = a.model_copy(update={
        "event_uid": "b",
        "title": "UKMTO reports tanker incident near the Strait of Hormuz",
        "url": "https://example.com/b",
        "raw_text": "ukmto reports tanker incident near the strait of hormuz",
    })
    clusters = cluster_events([a, b])
    assert len(clusters) == 1
    assert len(clusters[0].event_uids) == 2

def test_mixed_datetime_and_inserted_order_sorting_does_not_crash():
    recent = datetime.now(UTC).replace(tzinfo=None) - timedelta(hours=2)
    timed = EventItem(
        event_uid="timed",
        title="Shipping incident near Hormuz",
        source="Google News",
        source_type="aggregator",
        url="https://example.com/timed",
        published_at_utc=recent,
        countries_involved=["Oman"],
        actors_involved=[],
        locations=["Strait of Hormuz"],
        event_type="shipping_disruption",
        asset_exposure_tags=["shipping"],
        confidence_score=0.7,
        confidence_band="Moderate confidence",
        materiality_score=0.7,
        materiality_band="High",
        novelty_score=0.6,
        summary="Timed event",
        why_it_matters="Timed matters",
        operational_impact="Operational",
        market_impact="Market",
        uncertainty_notes="None",
        raw_text="shipping incident near hormuz",
        raw_payload={},
        fingerprint="fp-timed",
    )
    untimed = timed.model_copy(update={
        "event_uid": "untimed",
        "title": "Sanctions update affecting regional shipping",
        "url": "https://example.com/untimed",
        "published_at_utc": None,
        "detected_event_time_utc": None,
        "raw_payload": {"inserted_order": 3},
        "fingerprint": "fp-untimed",
    })
    clusters = cluster_events([untimed, timed])
    assert clusters
    event_uids = sorted(uid for cluster in clusters for uid in cluster.event_uids)
    assert event_uids == ["timed", "untimed"]
