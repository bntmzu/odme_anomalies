import uuid
import pytest
from typing import cast
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException
from sqlalchemy.exc import SQLAlchemyError

from odme_anomalies.api.v1.endpoints.ingest import ingest_anomaly
from odme_anomalies.schemas.anomaly_schema import AnomalyIn, AnomalyOut


class DummySession:
    """
    Dummy AsyncSession that records add/flush/commit/rollback calls,
    and assigns a UUID string to .id on flush().
    """

    def __init__(self):
        self.added = []
        self.flushed = False
        self.committed = False
        self.rolled_back = False

    def add(self, obj):
        self.added.append(obj)

    async def flush(self):
        self.flushed = True
        # Assign a realistic UUID string as the new anomaly's id
        for obj in self.added:
            if hasattr(obj, "id"):
                obj.id = str(uuid.uuid4())

    async def commit(self):
        self.committed = True

    async def rollback(self):
        self.rolled_back = True

    def begin(self):
        # Support `async with session.begin():`
        return self

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            await self.rollback()
        else:
            await self.commit()


@pytest.fixture
def dummy_session() -> AsyncSession:
    """
    Provides a DummySession cast to AsyncSession for endpoint calls.
    """
    return cast(AsyncSession, DummySession())


@pytest.mark.asyncio
async def test_ingest_success(monkeypatch, dummy_session: AsyncSession):
    """
    GIVEN a valid AnomalyIn payload
      AND calculate_threat_level is stubbed
      AND get_anomaly_with_attributes returns a matching dict
    WHEN ingest_anomaly is called
    THEN it should flush(), commit(), and return a valid AnomalyOut with a UUID id.
    """
    # Stub the threat calculation to always return 42
    monkeypatch.setattr(
        "odme_anomalies.api.v1.endpoints.ingest.calculate_threat_level",
        lambda category, attributes: 42,
    )

    # Build a valid payload
    payload = AnomalyIn.model_validate(
        {
            "kategorie": "Elementál",
            "lokace": "Šumava",
            "cas_detekce": "2025-07-30T12:00:00Z",
            "atributy": [
                {"klic": "agresivita", "hodnota": "3"},
                {"klic": "puvod", "hodnota": "slovanský"},
            ],
        }
    )

    # Stub get_anomaly_with_attributes to mirror the DB record
    async def fake_get(anomaly_id, session):
        # anomaly_id is the UUID string assigned on flush()
        return {
            "id": anomaly_id,
            "kategorie": payload.category,
            "lokace": payload.location,
            "cas_detekce": payload.detected_at.isoformat(),
            "uroven_hrozby": 42,
            "je_vyresen": False,
            "atributy": [
                {"id": 1, "klic": "agresivita", "hodnota": "3"},
                {"id": 2, "klic": "puvod", "hodnota": "slovanský"},
            ],
        }

    monkeypatch.setattr(
        "odme_anomalies.api.v1.endpoints.ingest.get_anomaly_with_attributes", fake_get
    )

    # Call the endpoint
    result = await ingest_anomaly(payload, session=dummy_session)

    # Assertions for transactional behavior
    assert dummy_session.flushed, "flush() should have been called"  # type: ignore[attr-defined]
    assert dummy_session.committed, "commit() should have been called"  # type: ignore[attr-defined]
    assert not dummy_session.rolled_back, "rollback() should NOT have been called"  # type: ignore[attr-defined]

    # Assert return type and fields
    assert isinstance(result, AnomalyOut)
    # id must be a 36‑char UUID string
    assert isinstance(result.id, str)
    assert len(result.id) == 36
    assert result.category == payload.category
    assert result.threat_level == 42
    assert result.location == payload.location
    assert result.is_resolved is False


@pytest.mark.asyncio
async def test_ingest_database_error(monkeypatch, dummy_session: AsyncSession):
    """
    GIVEN an AnomalyIn payload
      AND flush() raises SQLAlchemyError
    WHEN ingest_anomaly is called
    THEN it should raise HTTPException(500)
      AND rollback() should have been called.
    """
    # Stub threat calculation
    monkeypatch.setattr(
        "odme_anomalies.api.v1.endpoints.ingest.calculate_threat_level",
        lambda category, attributes: 0,
    )

    # Make flush() raise a database error
    async def bad_flush():
        raise SQLAlchemyError("flush failed")

    dummy_session.flush = bad_flush  # type: ignore[assignment]

    payload = AnomalyIn.model_validate(
        {
            "kategorie": "Chyba",
            "lokace": "Hvozd",
            "cas_detekce": "2025-07-30T13:00:00Z",
            "atributy": [],
        }
    )

    # Expect HTTP 500 and rollback
    with pytest.raises(HTTPException) as excinfo:
        await ingest_anomaly(payload, session=dummy_session)

    assert excinfo.value.status_code == 500
    assert "Database error" in excinfo.value.detail
    assert dummy_session.rolled_back, "rollback() should have been called on DB error"  # type: ignore[attr-defined]
