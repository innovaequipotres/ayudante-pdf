import uuid
from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class DocumentEdit(Base):
    """Texto final de un bloque editado por el docente.

    La clave primaria es compuesta ``(document_id, block_id)``: cada bloque
    admite una única versión final por documento. El contenido original nunca
    se toca: vive en ``document_files`` y ``extracted_contents``.
    """

    __tablename__ = "document_edits"

    __table_args__ = (
        CheckConstraint(
            "length(btrim(text)) > 0",
            name="ck_document_edits_text_not_blank",
        ),
        Index("ix_document_edits_owner", "owner_id"),
    )

    document_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("documents.id", ondelete="CASCADE"),
        primary_key=True,
    )
    block_id: Mapped[str] = mapped_column(String, primary_key=True)
    owner_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    text: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )