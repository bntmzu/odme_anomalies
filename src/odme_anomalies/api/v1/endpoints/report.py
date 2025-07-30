from fastapi import APIRouter, HTTPException, status, Depends, Path, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime, timezone

from odme_anomalies.db.session import get_session
from odme_anomalies import models
from odme_anomalies.schemas.agent_report_schema import AgentReportIn, AgentReportOut

router = APIRouter(
    prefix="/anomalies",
    tags=["Reports"],
)


@router.post(
    "/{anomaly_id}/report",
    response_model=AgentReportOut,
    status_code=status.HTTP_201_CREATED,
    summary="Add an agent report to an anomaly",
    description=(
        "Attach a new report from an agent to an existing anomaly.  \n"
        "- Validates that anomaly exists.  \n"
        "- Records `agent_name`, optional `summary`, and current UTC timestamp.  \n"
        "- Saves in a single transaction."
    ),
)
async def create_agent_report(
    anomaly_id: str = Path(..., description="ID of the anomaly to report on"),
    payload: AgentReportIn = Body(..., description="Agent report payload"),
    session: AsyncSession = Depends(get_session),
) -> AgentReportOut:
    """
    Create and return a new AgentReport linked to the given anomaly
    """
    # 1) Ensure anomaly exists
    anomaly = await session.get(models.Anomaly, str(anomaly_id))
    if not anomaly:
        raise HTTPException(status_code=404, detail="Anomaly not found")

    try:
        # 2) Persist report in one transaction
        async with session.begin():
            report = models.AgentReport(
                anomaly_id=str(anomaly_id),
                agent_name=payload.agent_name,
                summary=payload.summary,
                report_time=datetime.now(timezone.utc),
            )
            session.add(report)

        # 3) Reload to pick up any defaults (e.g. report.id) and return as Pydantic
        created = await session.get(models.AgentReport, report.id)
        return AgentReportOut.model_validate(created)

    except SQLAlchemyError as db_err:
        # automatic rollback from session.begin()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error occurred",
        ) from db_err
