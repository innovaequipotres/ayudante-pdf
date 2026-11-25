import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, Index, String, func, text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, validates

from app.core.database import Base


class User(Base):
    """Usuario de la aplicación (docente por defecto)."""

    __tablename__ = "users"

    __table_args__ = (
        CheckConstraint("email = lower(email)", name="ck_users_email_lowercase"),
        Index("uq_users_email_lower", func.lower(text("email")), unique=True),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    first_name: Mapped[str] = mapped_column(String, nullable=False)
    last_name: Mapped[str] = mapped_column(String, nullable=False)
    phone: Mapped[str | None] = mapped_column(String, nullable=True)
    email: Mapped[str] = mapped_column(String, nullable=False)
    password_hash: Mapped[str] = mapped_column(String, nullable=False)
    role: Mapped[str] = mapped_column(
        String, nullable=False, default="Docente", server_default=text("'Docente'")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    @validates("email")
    def normalize_email(self, _key: str, value: str | None) -> str | None:
        if value is None:
            return value
        return str(value).strip().lower()
