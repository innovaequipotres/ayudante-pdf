import uuid
from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    SmallInteger,
    String,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class DiagnosisRecord(Base):
    """Diagnóstico de accesibilidad de un documento.

    El ``payload`` guarda el JSON de ``app.schemas.diagnosis.Diagnosis``. Las
    columnas ``score``, ``level`` y ``ai_status`` se repiten fuera del JSONB
    para poder consultarlas sin abrirlo.
    """

    __tablename__ = "diagnoses"

    __table_args__ = (
        CheckConstraint(
            "score >= 0 AND score <= 100",
            name="ck_diagnoses_score_range",
        ),
        CheckConstraint(
            "level IN ('ok', 'review', 'barrier')",
            name="ck_diagnoses_level",
        ),
        CheckConstraint(
            "ai_status IN ('ok', 'unavailable', 'skipped')",
            name="ck_diagnoses_ai_status",
        ),
        Index("ix_diagnoses_owner", "owner_id"),
    )

    document_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("documents.id", ondelete="CASCADE"),
        primary_key=True,
    )
    owner_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    payload: Mapped[dict] = mapped_column(JSONB, nullable=False)
    score: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    level: Mapped[str] = mapped_column(String, nullable=False)
    ai_status: Mapped[str] = mapped_column(
        String,
        nullable=False,
        default="skipped",
        server_default=text("'skipped'"),
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
