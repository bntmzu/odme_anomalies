from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from odme_anomalies.db.session import get_session
from odme_anomalies import models
from odme_anomalies.schemas.anomaly_schema import (
    AnomalyQueryParams,
    AnomalyOut,
    AnomalySummary,
)
from sqlalchemy.orm import selectinload

router = APIRouter(
    prefix="/anomalies",
    tags=["Anomalies"],
)


@router.get(
    "/",
    response_model=list[AnomalyOut],
    summary="List anomalies",
    description="Retrieve all anomalies, optionally filtered by category and/or minimum threat level",
)
async def list_anomalies(
    filters: AnomalyQueryParams = Depends(),
    session: AsyncSession = Depends(get_session),
) -> List[AnomalyOut]:
    stmt = select(models.Anomaly).options(selectinload(models.Anomaly.attributes))
    if filters.category:
        stmt = stmt.where(models.Anomaly.category == filters.category)
    if filters.min_threat is not None:
        stmt = stmt.where(models.Anomaly.threat_level >= filters.min_threat)

    result = await session.execute(stmt)
    orm_list = result.scalars().all()  # List[models.Anomaly]

    return [AnomalyOut.model_validate(item) for item in orm_list]


@router.get(
    "/summary",
    response_model=AnomalySummary,
    summary="Anomaly summary",
    description="Get total count, unresolved count, most common category, and average threat level of unresolved anomalies",
)
async def anomaly_summary(
    session: AsyncSession = Depends(get_session),
) -> AnomalySummary:
    # 1) Total count
    total = await session.scalar(select(func.count()).select_from(models.Anomaly))

    # 2) Unresolved count
    unresolved = await session.scalar(
        select(func.count())
        .select_from(models.Anomaly)
        .where(models.Anomaly.is_resolved == False)
    )

    # 3) Most common category (or None)
    most_common = await session.scalar(
        select(models.Anomaly.category)
        .group_by(models.Anomaly.category)
        .order_by(func.count(models.Anomaly.category).desc())
        .limit(1)
    )

    # 4) Average threat level for unresolved (or None)
    avg_threat = await session.scalar(
        select(func.avg(models.Anomaly.threat_level)).where(
            models.Anomaly.is_resolved == False
        )
    )

    return AnomalySummary(
        total_anomalies=total or 0,
        unresolved_anomalies=unresolved or 0,
        most_common_category=most_common,
        avg_threat_level=float(avg_threat) if avg_threat is not None else None,
    )
