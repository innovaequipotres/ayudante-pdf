import uuid

from sqlalchemy import CheckConstraint, ForeignKey, Index, LargeBinary, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class DocumentFile(Base):
    """Contenido original de un documento.

    Un PDF guarda sus bytes en ``content``; un texto pegado se guarda en
    ``content_text``. La restricción exige exactamente uno de los dos.
    """

    __tablename__ = "document_files"

    __table_args__ = (
        CheckConstraint(
            "(content IS NOT NULL) <> (content_text IS NOT NULL)",
            name="ck_document_files_one_content",
        ),
        Index("ix_document_files_owner", "owner_id"),
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
    # Los bytes se cargan solo al leerlos con ``read_pdf``: un listado de
    # documentos no debe traer esta columna.
    content: Mapped[bytes | None] = mapped_column(
        LargeBinary, nullable=True, deferred=True
    )
    content_text: Mapped[str | None] = mapped_column(Text, nullable=True)
