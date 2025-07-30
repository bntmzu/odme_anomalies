from uuid import uuid4
from sqlalchemy import String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from odme_anomalies.db.base import Base
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from odme_anomalies.models.anomaly import Anomaly


class AnomalyAttribute(Base):
    __tablename__ = "anomaly_attributes"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid4()),
    )
    anomaly_id: Mapped[str] = mapped_column(
        ForeignKey("anomalies.id"),
        nullable=False,
    )
    key: Mapped[str] = mapped_column(
        String,
        nullable=False,
    )
    value: Mapped[str] = mapped_column(
        String,
        nullable=False,
    )

    anomaly: Mapped["Anomaly"] = relationship(
        "Anomaly",
        back_populates="attributes",
    )
