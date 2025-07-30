from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from odme_anomalies.models.anomaly import Anomaly


async def get_anomaly_with_attributes(
    anomaly_id: str, session: AsyncSession
) -> Anomaly:
    result = await session.execute(
        select(Anomaly)
        .options(selectinload(Anomaly.attributes))
        .where(Anomaly.id == anomaly_id)
    )
    return result.scalar_one_or_none()
