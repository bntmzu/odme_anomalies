import uuid
from datetime import datetime, timezone
from sqlalchemy import String, DateTime, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from odme_anomalies.db.base import Base
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from odme_anomalies.models.anomaly import Anomaly


class AgentReport(Base):
    __tablename__ = "agent_reports"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    anomaly_id: Mapped[str] = mapped_column(
        ForeignKey("anomalies.id"),
        nullable=False,
    )
    agent_name: Mapped[str] = mapped_column(
        String,
        nullable=False,
    )
    report_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    summary: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    anomaly: Mapped["Anomaly"] = relationship(
        "Anomaly",
        back_populates="reports",
    )
