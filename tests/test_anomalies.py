import pytest
from typing import List, Any, cast, Optional
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession

from odme_anomalies.api.v1.endpoints.anomalies import list_anomalies, anomaly_summary
from odme_anomalies.schemas.anomaly_schema import (
    AnomalyQueryParams,
    AnomalyOut,
    AnomalySummary,
    AnomalyAttributeOut,
)


class FakeAttribute:
    """Minimal fake ORM attribute."""

    def __init__(self, id_: int, key: str, value: str):
        self.id = id_
        self.key = key
        self.value = value


class FakeAnomaly:
    """Minimal fake ORM anomaly with attributes."""

    def __init__(
        self,
        id_: str,
        category: str,
        location: str,
        detected_at: datetime,
        threat_level: int,
        is_resolved: bool,
        attributes: List[FakeAttribute],
    ):
        self.id = id_
        self.category = category
        self.location = location
        self.detected_at = detected_at
        self.threat_level = threat_level
        self.is_resolved = is_resolved
        self.attributes = attributes


class DummyListSession:
    """
    Fake AsyncSession for list_anomalies:
    - execute(stmt) returns an object whose .scalars().all() gives a filtered list
    """

    def __init__(self, items: List[Any], filters: Optional[AnomalyQueryParams] = None):
        self._items = items
        self._filters = filters

    async def execute(self, _stmt):
        # Apply in‑memory filtering just like list_anomalies would in SQL
        results = self._items
        if self._filters:
            if self._filters.category is not None:
                results = [a for a in results if a.category == self._filters.category]
            if self._filters.min_threat is not None:
                results = [
                    a for a in results if a.threat_level >= self._filters.min_threat
                ]

        class Result:
            def __init__(self, data):
                self._data = data

            def scalars(self):
                return self

            def all(self):
                return self._data

        return Result(results)


class DummySummarySession:
    """
    Fake AsyncSession for anomaly_summary:
    each .scalar(stmt) yields the next value from `values`
    """

    def __init__(self, values):
        self._iter = iter(values)

    async def scalar(self, _stmt):
        return next(self._iter)


@pytest.mark.asyncio
async def test_list_anomalies_basic():
    now = datetime(2025, 7, 30, 15, 0, tzinfo=timezone.utc)
    fake1 = FakeAnomaly(
        id_="11111111-1111-1111-1111-111111111111",
        category="Elementál",
        location="Šumava",
        detected_at=now,
        threat_level=50,
        is_resolved=False,
        attributes=[FakeAttribute(1, "agresivita", "3")],
    )
    fake2 = FakeAnomaly(
        id_="22222222-2222-2222-2222-222222222222",
        category="Přízrak",
        location="Krkonoše",
        detected_at=now,
        threat_level=30,
        is_resolved=True,
        attributes=[FakeAttribute(2, "puvod", "slovanský")],
    )

    filters = AnomalyQueryParams.model_validate({})
    session = cast(AsyncSession, DummyListSession([fake1, fake2], filters))

    result = await list_anomalies(filters=filters, session=session)

    assert isinstance(result, list) and len(result) == 2

    out1, out2 = result

    assert isinstance(out1, AnomalyOut)
    assert out1.id == fake1.id
    assert out1.category == fake1.category
    assert out1.location == fake1.location
    assert out1.threat_level == fake1.threat_level
    assert out1.is_resolved == fake1.is_resolved

    assert len(out1.attributes) == 1
    attr = out1.attributes[0]
    assert isinstance(attr, AnomalyAttributeOut)
    assert attr.id == 1
    assert attr.key == "agresivita"
    assert attr.value == "3"

    assert out2.id == fake2.id
    assert out2.category == fake2.category
    assert out2.is_resolved is True


@pytest.mark.asyncio
async def test_list_anomalies_category_filter():
    now = datetime(2025, 7, 30, 15, 0, tzinfo=timezone.utc)
    e = FakeAnomaly(
        id_="1111-1111",
        category="Elementál",
        location="A",
        detected_at=now,
        threat_level=10,
        is_resolved=False,
        attributes=[FakeAttribute(1, "klic", "v")],
    )
    p = FakeAnomaly(
        id_="2222-2222",
        category="Přízrak",
        location="B",
        detected_at=now,
        threat_level=20,
        is_resolved=False,
        attributes=[FakeAttribute(2, "klic", "v")],
    )

    filters = AnomalyQueryParams.model_validate({"kategorie": "Elementál"})
    session = cast(AsyncSession, DummyListSession([e, p], filters))

    result = await list_anomalies(filters=filters, session=session)

    assert len(result) == 1
    assert result[0].category == "Elementál"


@pytest.mark.asyncio
async def test_list_anomalies_min_threat_filter():
    now = datetime(2025, 7, 30, 16, 0, tzinfo=timezone.utc)
    low = FakeAnomaly(
        id_="aaa",
        category="X",
        location="A",
        detected_at=now,
        threat_level=15,
        is_resolved=False,
        attributes=[],
    )
    high = FakeAnomaly(
        id_="bbb",
        category="Y",
        location="B",
        detected_at=now,
        threat_level=25,
        is_resolved=False,
        attributes=[],
    )

    filters = AnomalyQueryParams.model_validate({"min_hrozba": 20})
    session = cast(AsyncSession, DummyListSession([low, high], filters))

    result = await list_anomalies(filters=filters, session=session)

    assert len(result) == 1
    assert result[0].threat_level == 25


@pytest.mark.asyncio
async def test_anomaly_summary_counts_and_averages():
    values = [10, 4, "Elementál", 6.75]
    session = cast(AsyncSession, DummySummarySession(values))

    summary = await anomaly_summary(session=session)

    assert isinstance(summary, AnomalySummary)
    assert summary.total_anomalies == 10
    assert summary.unresolved_anomalies == 4
    assert summary.most_common_category == "Elementál"
    assert summary.avg_threat_level == 6.75


@pytest.mark.asyncio
async def test_anomaly_summary_empty():
    session = cast(AsyncSession, DummySummarySession([0, 0, None, None]))

    summary = await anomaly_summary(session=session)

    assert summary.total_anomalies == 0
    assert summary.unresolved_anomalies == 0
    assert summary.most_common_category is None
    assert summary.avg_threat_level is None
