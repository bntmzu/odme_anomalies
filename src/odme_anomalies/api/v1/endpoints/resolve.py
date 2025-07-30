from fastapi import APIRouter, HTTPException, Path, status, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
from pydantic import BaseModel, Field, ConfigDict

from odme_anomalies.db.session import get_session
from odme_anomalies.models.anomaly import Anomaly


class ResponseMessage(BaseModel):
    """
    Standard response with a message.
    """

    message: str = Field(..., description="Result message")

    model_config = ConfigDict(populate_by_name=True)


router = APIRouter(
    prefix="/anomalies",
    tags=["Anomalies"],
)


@router.post(
    "/{anomaly_id}/resolve",
    status_code=status.HTTP_200_OK,
    summary="Resolve an anomaly",
    description="Mark the specified anomaly as resolved if it isn't already",
)
async def resolve_anomaly(
    anomaly_id: int = Path(..., description="ID of the anomaly to mark as resolved"),
    session: AsyncSession = Depends(get_session),
) -> ResponseMessage:
    # Check existence
    anomaly = await session.get(Anomaly, anomaly_id)
    if not anomaly:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Anomaly not found"
        )
    if anomaly.is_resolved:
        return ResponseMessage(message="Anomaly already resolved")

    # 3) Mark as resolved in one transaction
    try:
        async with session.begin():
            anomaly.is_resolved = True
            session.add(anomaly)
    except SQLAlchemyError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error occurred",
        )

    return ResponseMessage(message="Anomaly marked as resolved")
