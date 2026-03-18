from uuid import uuid4

from backend.app.db import Base, SessionLocal, engine
from backend.app.models import EventRecord


def test_objects_remain_readable_after_commit_when_session_closes():
    Base.metadata.create_all(bind=engine)
    event_uid = f"session-test-{uuid4()}"
    with SessionLocal() as db:
        rec = EventRecord(
            event_uid=event_uid,
            title="Test event",
            source="Test",
            source_type="official",
            url="https://example.com/test",
            event_type="diplomatic_statement",
            fingerprint=f"fp-{event_uid}",
        )
        db.add(rec)
        db.commit()

    with SessionLocal() as db:
        row = db.query(EventRecord).filter_by(event_uid=event_uid).one()
        db.commit()

    assert row.event_uid == event_uid
    assert row.title == "Test event"
