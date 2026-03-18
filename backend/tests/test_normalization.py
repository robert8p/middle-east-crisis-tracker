from datetime import datetime

from backend.app.services.normalization import is_relevant_item, normalize_raw_item


def test_normalize_raw_item_makes_payload_json_safe():
    raw = {
        "title": "Iran says shipping risk in Strait of Hormuz is rising",
        "summary": "Officials warn of maritime disruption.",
        "url": "https://example.com/item",
        "source": "Example",
        "source_type": "aggregator",
        "published_at_utc": datetime(2026, 3, 18, 2, 0, 0),
    }
    item = normalize_raw_item(raw)
    assert item.raw_payload["published_at_utc"] == "2026-03-18T02:00:00"


def test_is_relevant_item_filters_noise_navigation_and_generic_guidance():
    assert not is_relevant_item({"title": "About us", "summary": "", "url": "https://example.com/about"})
    assert not is_relevant_item({"title": "UK financial sanctions general guidance", "summary": "", "url": "https://gov.uk/foo"})
    assert is_relevant_item({
        "title": "Iran warns shipping risk in Strait of Hormuz is rising",
        "summary": "Maritime security concerns are increasing.",
        "url": "https://example.com/hormuz",
    })
