import uuid
from uuid import UUID
from datetime import datetime, timezone
from typing import TYPE_CHECKING
from sqlalchemy import String, Integer, Boolean, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from odme_anomalies.db.base import Base

if TYPE_CHECKING:
    from odme_anomalies.models.anomaly_attribute import AnomalyAttribute
    from odme_anomalies.models.agent_report import AgentReport


class Anomaly(Base):
    __tablename__ = "anomalies"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid4()),
    )
    category: Mapped[str] = mapped_column(
        String,
        nullable=False,
        index=True,
    )
    location: Mapped[str] = mapped_column(
        String,
        nullable=False,
    )
    detected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    threat_level: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    is_resolved: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )

    # One-to-many
    attributes: Mapped[list["AnomalyAttribute"]] = relationship(
        "AnomalyAttribute",
        back_populates="anomaly",
        cascade="all, delete-orphan",
    )
    reports: Mapped[list["AgentReport"]] = relationship(
        "AgentReport",
        back_populates="anomaly",
        cascade="all, delete-orphan",
    )
