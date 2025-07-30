from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime


class AnomalyAttributeIn(BaseModel):
    """
    Input schema: single anomaly attribute key-value pair.
    """

    key: str = Field(
        ..., alias="klic", description="Attribute key (e.g., 'puvod', 'agresivita')"
    )
    value: str = Field(..., alias="hodnota", description="Attribute value")

    model_config = ConfigDict(populate_by_name=True, from_attributes=True)


class AnomalyAttributeOut(AnomalyAttributeIn):
    """
    Attribute of an anomaly in the response, including its DB id.
    """

    id: int = Field(..., description="Unique identifier of this attribute record")

    model_config = ConfigDict(populate_by_name=True, from_attributes=True)


class AnomalyIn(BaseModel):
    """
    Request schema for POST /ingest:
    Report of a newly detected anomaly (excluding ID, threat level, and resolution status).
    """

    category: str = Field(
        ..., alias="kategorie", description="Anomaly category (e.g., 'Elementál')"
    )
    location: str = Field(
        ..., alias="lokace", description="Geographic location of the anomaly"
    )
    detected_at: datetime = Field(
        ..., alias="cas_detekce", description="Time when anomaly was detected"
    )
    attributes: List[AnomalyAttributeIn] = Field(
        ..., alias="atributy", description="List of additional attributes"
    )

    model_config = ConfigDict(
        populate_by_name=True,
        from_attributes=True,
        json_schema_extra={
            "example": {
                "kategorie": "Elementál",
                "lokace": "Černé jezero, Šumava",
                "cas_detekce": "2025-07-24T22:15:00Z",
                "atributy": [
                    {"klic": "puvod", "hodnota": "Slovanský"},
                    {"klic": "entita", "hodnota": "Vodník"},
                    {"klic": "agresivita", "hodnota": "3"},
                    {"klic": "agresivita_odhad", "hodnota": "vysoká"},
                ],
            }
        },
    )


class AnomalyOut(BaseModel):
    """
    Response DTO for POST and GET /anomalies: full anomaly record.
    """

    id: str
    category: str = Field(..., alias="kategorie", description="Anomaly category")
    location: str = Field(..., alias="lokace", description="Detection location")
    detected_at: datetime = Field(
        ..., alias="cas_detekce", description="Detection timestamp"
    )
    threat_level: int = Field(
        ..., alias="uroven_hrozby", description="Calculated threat level (0–100)"
    )
    is_resolved: bool = Field(
        ..., alias="je_vyresen", description="Whether the anomaly is resolved"
    )
    attributes: List[AnomalyAttributeOut] = Field(
        ..., alias="atributy", description="Associated attributes"
    )

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        json_schema_extra={
            "example": {
                "id": 42,
                "kategorie": "Elemental",
                "lokace": "Cerne jezero, Sumava",
                "cas_detekce": "2025-07-24T22:15:00Z",
                "uroven_hrozby": 78,
                "je_vyresen": False,
                "atributy": [
                    {"id": 1, "klic": "puvod", "hodnota": "Slovansky"},
                    {"id": 2, "klic": "agresivita", "hodnota": "3"},
                    {"id": 3, "klic": "agresivita_odhad", "hodnota": "high"},
                ],
            }
        },
    )


class AnomalySummary(BaseModel):
    """
    Response DTO for GET /anomalies/summary: aggregated statistics.
    """

    total_anomalies: int = Field(
        ..., alias="celkem_projevu", description="Total number of anomalies"
    )
    unresolved_anomalies: int = Field(
        ..., alias="nevyresenych_projevu", description="Number of unresolved anomalies"
    )
    most_common_category: Optional[str] = Field(
        None, alias="nejcastejsi_kategorie", description="Most frequent category"
    )
    avg_threat_level: Optional[float] = Field(
        None,
        alias="prumerna_uroven_hrozby",
        description="Average threat level of unresolved anomalies",
    )

    model_config = ConfigDict(
        populate_by_name=True,
        from_attributes=True,
        json_schema_extra={
            "example": {
                "celkem_projevu": 100,
                "nevyresenych_projevu": 25,
                "nejcastejsi_kategorie": "Elemental",
                "prumerna_uroven_hrozby": 58.3,
            }
        },
    )


class AnomalyQueryParams(BaseModel):
    """
    Optional query parameters for filtering GET /anomalies.
    """

    category: Optional[str] = Field(
        None, alias="kategorie", description="Filter by anomaly category"
    )
    min_threat: Optional[int] = Field(
        None, alias="min_hrozba", description="Filter by minimum threat level"
    )

    model_config = ConfigDict(populate_by_name=True)
