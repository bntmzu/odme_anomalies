from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import Optional


class AgentReportIn(BaseModel):
    """
    Input schema for POST /anomalies/{id}/report — a new agent report.
    """

    agent_name: str = Field(
        ..., alias="jmeno_strazce", description="Name of the reporting guard"
    )
    summary: Optional[str] = Field(
        None, alias="shrnuti_hlaseni", description="Summary text from the guard"
    )

    model_config = ConfigDict(
        populate_by_name=True,
        from_attributes=True,
        json_schema_extra={
            "example": {
                "jmeno_strazce": "Agent Spectra",
                "shrnuti_hlaseni": "Entity flickered in and out of the visible spectrum. It responded strongly to electromagnetic pulses..",
            }
        },
    )


class AgentReportOut(AgentReportIn):
    """
    Output schema for GET or response after creating report.
    """

    id: str = Field(..., alias="id", description="Report primary key")
    anomaly_id: str = Field(
        ..., alias="projev_id", description="Foreign key to anomaly"
    )
    report_time: datetime = Field(
        ..., alias="cas_hlaseni", description="UTC timestamp when report was filed"
    )

    model_config = ConfigDict(populate_by_name=True, from_attributes=True)
