from backend.app.config import Settings, get_settings
from backend.app.sources.registry import (
    UNSecurityCouncilRss,
    UKMTORecentIncidents,
    IsraelMfaPress,
    GovIlNews,
    IranMfaStatements,
    GoogleNewsMiddleEast,
)


def test_flaky_sources_disabled_by_default(monkeypatch):
    monkeypatch.setenv("APP_SOURCE_ENABLED_OVERRIDES", "")
    get_settings.cache_clear()
    assert GoogleNewsMiddleEast().enabled is True
    assert UNSecurityCouncilRss().enabled is False
    assert UKMTORecentIncidents().enabled is False
    assert IsraelMfaPress().enabled is False
    assert GovIlNews().enabled is False
    assert IranMfaStatements().enabled is False


def test_overrides_can_reenable_disabled_sources(monkeypatch):
    monkeypatch.setenv("APP_SOURCE_ENABLED_OVERRIDES", "un_security_council_rss=1,ukmto_recent_incidents=true")
    get_settings.cache_clear()
    assert UNSecurityCouncilRss().enabled is True
    assert UKMTORecentIncidents().enabled is True


def test_settings_default_timeout_and_startup_ingest():
    get_settings.cache_clear()
    settings = Settings()
    assert settings.app_source_timeout_seconds == 6
    assert settings.app_run_startup_ingestion is True


from datetime import datetime
from backend.app.schemas import ClusterItem
from backend.app.services.clustering import _cluster_time_sort_value


def test_cluster_time_sort_value_handles_missing_times():
    cluster = ClusterItem(cluster_uid="c1", canonical_title="x", canonical_event_uid="e1")
    assert _cluster_time_sort_value(cluster) == 0.0


def test_cluster_time_sort_value_uses_timestamp():
    dt = datetime(2026, 3, 18, 2, 30, 0)
    cluster = ClusterItem(cluster_uid="c2", canonical_title="x", canonical_event_uid="e2", time_max_utc=dt)
    assert _cluster_time_sort_value(cluster) == dt.timestamp()
