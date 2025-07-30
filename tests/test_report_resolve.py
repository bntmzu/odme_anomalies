import pytest
from typing import cast
from datetime import datetime
from fastapi import HTTPException
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

import odme_anomalies.models as models
from odme_anomalies.api.v1.endpoints.report import create_agent_report
from odme_anomalies.api.v1.endpoints.resolve import resolve_anomaly, ResponseMessage
from odme_anomalies.schemas.agent_report_schema import AgentReportIn, AgentReportOut


class DummyReportSession:
    """
    Fake AsyncSession for create_agent_report:
      - get(models.Anomaly, id) → stub anomaly or None
      - get(models.AgentReport, id) → returns the “refreshed” report
      - add(obj), commit(), refresh(obj), rollback() record calls
      - begin()/__aenter__/__aexit__ support transactional context
    """

    def __init__(self, anomaly_exists: bool = True):
        self.anomaly_exists = anomaly_exists
        self.added = []  # records objects passed to add()
        self.committed = False
        self.rolled_back = False
        self.refreshed = None  # will hold the AgentReport after “refresh”

    async def get(self, model, id_):
        # First call is to fetch the Anomaly
        if model is models.Anomaly:
            if not self.anomaly_exists:
                return None
            return type("AnomalyStub", (), {"id": id_})()
        # Second call is to fetch the newly created AgentReport
        if model is models.AgentReport:
            return self.refreshed
        return None

    def add(self, obj):
        self.added.append(obj)

    async def commit(self):
        self.committed = True  # type: ignore[attr-defined]

    async def refresh(self, obj):
        obj.id = "1df"
        self.refreshed = obj  # type: ignore[attr-defined]

    async def rollback(self):
        self.rolled_back = True  # type: ignore[attr-defined]

    def begin(self):
        return self

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        # On exception inside the block: rollback
        if exc_type:
            await self.rollback()
        else:
            # On success: “refresh” then commit
            try:
                for obj in self.added:
                    if isinstance(obj, models.AgentReport):
                        await self.refresh(obj)
                await self.commit()
            except Exception:
                await self.rollback()
                raise


class DummyResolveSession:
    """
    Fake AsyncSession for resolve_anomaly:
      - get(models.Anomaly, id) → returns the anomaly stub or None
      - add(obj), commit(), begin()/__aenter__/__aexit__ simulate transaction
    """

    def __init__(self, anomaly):
        self._anomaly = anomaly
        self.added = []
        self.committed = False

    async def get(self, model, id_):
        return self._anomaly

    def add(self, obj):
        self.added.append(obj)

    def begin(self):
        return self

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        # no rollback path here; just commit on success
        if exc_type is None:
            await self.commit()

    async def commit(self):
        self.committed = True  # type: ignore[attr-defined]


# ------------------ Tests for create_agent_report ------------------


@pytest.mark.asyncio
async def test_create_agent_report_success():
    """
    GIVEN an existing anomaly
      AND a valid AgentReportIn payload
    WHEN create_agent_report is called
    THEN it commits, refreshes, and returns AgentReportOut with integer id.
    """
    session = cast(AsyncSession, DummyReportSession(anomaly_exists=True))

    payload = AgentReportIn.model_validate(
        {
            "jmeno_strazce": "Agent Spectra",
            "shrnuti_hlaseni": "Observed strange electromagnetic patterns",
        }
    )

    result = await create_agent_report(
        anomaly_id="00000000-0000-0000-0000-000000000123",
        payload=payload,
        session=session,
    )

    assert isinstance(result, AgentReportOut)
    assert result.agent_name == payload.agent_name
    assert result.summary == payload.summary

    assert session.committed, "commit() should have been called"  # type: ignore[attr-defined]
    assert session.refreshed is not None  # type: ignore[attr-defined]
    assert isinstance(result.id, str)
    assert isinstance(result.anomaly_id, str)
    assert isinstance(result.report_time, datetime)


@pytest.mark.asyncio
async def test_create_agent_report_not_found():
    """
    GIVEN no anomaly in DB
    WHEN create_agent_report is called
    THEN HTTPException 404 is raised.
    """
    session = cast(AsyncSession, DummyReportSession(anomaly_exists=False))

    payload = AgentReportIn.model_validate(
        {"jmeno_strazce": "Agent X", "shrnuti_hlaseni": None}
    )

    with pytest.raises(HTTPException) as exc:
        await create_agent_report(anomaly_id="", payload=payload, session=session)
    assert exc.value.status_code == 404
    assert "Anomaly not found" in exc.value.detail


@pytest.mark.asyncio
async def test_create_agent_report_db_error():
    """
    GIVEN a database error on commit()
    WHEN create_agent_report is called
    THEN HTTPException 500 is raised and rollback() is called.
    """
    session_obj = DummyReportSession(anomaly_exists=True)
    session = cast(AsyncSession, session_obj)

    async def bad_commit():
        raise SQLAlchemyError("commit failed")

    session_obj.commit = bad_commit  # type: ignore[assignment]

    payload = AgentReportIn.model_validate(
        {"jmeno_strazce": "Agent Y", "shrnuti_hlaseni": "Sample report"}
    )

    with pytest.raises(HTTPException) as exc:
        await create_agent_report(
            anomaly_id="00000000-0000-0000-0000-000000000123",
            payload=payload,
            session=session,
        )

    assert exc.value.status_code == 500
    assert "Database error" in exc.value.detail
    assert session_obj.rolled_back, "rollback() should have been called"  # type: ignore[attr-defined]


# ------------------ Tests for resolve_anomaly ------------------


@pytest.mark.asyncio
async def test_resolve_anomaly_success():
    """
    GIVEN an unresolved anomaly
    WHEN resolve_anomaly is called
    THEN it marks resolved, commits, and returns a ResponseMessage.
    """
    fake = type("Anomaly", (), {"is_resolved": False})()
    session = cast(AsyncSession, DummyResolveSession(fake))

    response = await resolve_anomaly(anomaly_id=789, session=session)

    assert isinstance(response, ResponseMessage)
    assert response.message == "Anomaly marked as resolved"
    assert session.committed, "commit() should have been called"  # type: ignore[attr-defined]


@pytest.mark.asyncio
async def test_resolve_anomaly_already_resolved():
    """
    GIVEN an already resolved anomaly
    WHEN resolve_anomaly is called
    THEN it returns a ResponseMessage without committing.
    """
    fake = type("Anomaly", (), {"is_resolved": True})()
    session = cast(AsyncSession, DummyResolveSession(fake))

    response = await resolve_anomaly(anomaly_id=789, session=session)

    assert isinstance(response, ResponseMessage)
    assert response.message == "Anomaly already resolved"
    assert not session.committed  # type: ignore[attr-defined]


@pytest.mark.asyncio
async def test_resolve_anomaly_not_found():
    """
    GIVEN no anomaly in DB
    WHEN resolve_anomaly is called
    THEN HTTPException 404 is raised.
    """
    session = cast(AsyncSession, DummyResolveSession(None))

    with pytest.raises(HTTPException) as exc:
        await resolve_anomaly(anomaly_id=999, session=session)
    assert exc.value.status_code == 404
    assert "not found" in exc.value.detail
