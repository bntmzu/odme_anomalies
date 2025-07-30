from fastapi import APIRouter, HTTPException, status, Depends, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
from odme_anomalies.db.session import get_session
from odme_anomalies import models
from odme_anomalies.schemas.anomaly_schema import AnomalyIn, AnomalyOut
from odme_anomalies.services.threat_level import calculate_threat_level
from odme_anomalies.crud.anomaly_reader import get_anomaly_with_attributes

router = APIRouter(
    prefix="/anomalies",
    tags=["Anomalies"],
)


@router.post(
    "/",
    response_model=AnomalyOut,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new anomaly",
    response_description="Ingest a new anomaly, compute threat level, and save in a single transaction",
    description="Ingest a new anomaly, compute its threat level, and save it (with attributes) in one transaction",
)
async def ingest_anomaly(
    payload: AnomalyIn = Body(..., description="New anomaly payload"),
    session: AsyncSession = Depends(get_session),
) -> AnomalyOut:
    """
    1. Validate input via AnomalyIn.
    2. Compute `threat_level` = calculate_threat_level(category, attributes).
    3. Save anomaly + its attributes inside one transaction.
    4. Return the full record (AnomalyOut).
    """
    # 1) Compute threat level
    threat_level = calculate_threat_level(payload.category, payload.attributes)

    try:
        # 2) Persist within a single transaction
        async with session.begin():
            new_anomaly = models.Anomaly(
                category=payload.category,
                location=payload.location,
                detected_at=payload.detected_at,
                threat_level=threat_level,
                is_resolved=False,
            )
            session.add(new_anomaly)
            await session.flush()  # for `anomaly.id`

            for attr in payload.attributes:
                session.add(
                    models.AnomalyAttribute(
                        anomaly_id=new_anomaly.id, key=attr.key, value=attr.value
                    )
                )

        # 3) Load back with attributes
        orm_anomaly = await get_anomaly_with_attributes(new_anomaly.id, session)
        return AnomalyOut.model_validate(orm_anomaly)

    except SQLAlchemyError as db_err:
        # rollback выполняется автоматически при выходе из session.begin()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error occurred",
        ) from db_err
