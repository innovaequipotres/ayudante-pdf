import uuid
from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    String,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class ObservationStateRecord(Base):
    """Estado de revisión de una barrera, por documento.

    La clave primaria es compuesta ``(document_id, observation_id)``: cada
    observación del diagnóstico admite un único estado por documento.
    """

    __tablename__ = "observation_states"

    __table_args__ = (
        CheckConstraint(
            "state IN ('pending', 'applied', 'ignored')",
            name="ck_observation_states_state",
        ),
        Index("ix_observation_states_owner", "owner_id"),
    )

    document_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("documents.id", ondelete="CASCADE"),
        primary_key=True,
    )
    observation_id: Mapped[str] = mapped_column(String, primary_key=True)
    owner_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    state: Mapped[str] = mapped_column(
        String,
        nullable=False,
        default="pending",
        server_default=text("'pending'"),
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )