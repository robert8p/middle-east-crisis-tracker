from backend.app.sources.base import SourceResult
from backend.app.schemas import SourceHealthItem


def test_source_failure_health_flag():
    result = SourceResult(source_name="demo", source_type="official", error="timeout")
    health = SourceHealthItem(
        source_name=result.source_name,
        source_type=result.source_type,
        enabled=True,
        last_error=result.error,
        degraded=bool(result.error),
    )
    assert health.degraded is True
    assert health.last_error == "timeout"