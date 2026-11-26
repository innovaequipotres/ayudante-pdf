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
from sqlalchemy.orm import Mapped, mapped_column, validates

from app.core.database import Base


class Folder(Base):
    """Carpeta de documentos. Puede estar en la raíz o dentro de otra carpeta."""

    __tablename__ = "folders"

    __table_args__ = (
        CheckConstraint(
            "length(btrim(name)) > 0",
            name="ck_folders_name_not_blank",
        ),
        CheckConstraint("name = btrim(name)", name="ck_folders_name_trimmed"),
        CheckConstraint(
            "parent_id IS NULL OR parent_id <> id",
            name="ck_folders_not_self_parent",
        ),
        # Las raíces tienen parent_id NULL: un índice único común no alcanza
        # porque NULL nunca colisiona con NULL. Por eso hay dos índices
        # parciales, uno por nivel.
        Index(
            "uq_folders_owner_root_name",
            "owner_id",
            func.lower(text("name")),
            unique=True,
            postgresql_where=text("parent_id IS NULL"),
        ),
        Index(
            "uq_folders_owner_parent_name",
            "owner_id",
            "parent_id",
            func.lower(text("name")),
            unique=True,
            postgresql_where=text("parent_id IS NOT NULL"),
        ),
        Index("ix_folders_owner_parent", "owner_id", "parent_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    owner_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    parent_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("folders.id", ondelete="CASCADE"),
        nullable=True,
    )
    name: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    @validates("name")
    def normalize_name(self, _key: str, value: str | None) -> str | None:
        if value is None:
            return value
        return str(value).strip()
