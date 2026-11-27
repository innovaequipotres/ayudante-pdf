"""Schemas de documentos para la biblioteca."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.session import SessionStatus, SourceType


class DocumentResponse(BaseModel):
    """Datos públicos de un documento (sin bytes ni contenido extraído)."""

    id: UUID = Field(description="Identificador único del documento.")
    owner_id: UUID = Field(description="Usuario dueño del documento.")
    folder_id: UUID | None = Field(description="Carpeta donde está guardado.")
    source_type: SourceType = Field(description="Origen del material: PDF o texto.")
    filename: str | None = Field(description="Nombre del archivo o título.")
    size_bytes: int = Field(description="Tamaño en bytes.")
    status: SessionStatus = Field(description="Estado actual del documento.")
    created_at: datetime = Field(description="Fecha de creación en UTC.")
    updated_at: datetime = Field(description="Fecha de última modificación en UTC.")


class DocumentUpdate(BaseModel):
    """Datos para actualizar un documento (renombrar o mover)."""

    filename: str | None = Field(
        default=None,
        description="Nuevo nombre del archivo o título.",
        max_length=200,
    )
    folder_id: UUID | None = Field(
        default=None,
        description="Nueva carpeta. Null para mover a raíz.",
    )


class DocumentListFilters(BaseModel):
    """Filtros opcionales para el listado de documentos."""

    folder_id: UUID | None = Field(
        default=None,
        description="Filtrar por carpeta. Null para documentos sin carpeta.",
    )
    status: SessionStatus | None = Field(
        default=None,
        description="Filtrar por estado.",
    )
    q: str | None = Field(
        default=None,
        description="Búsqueda por nombre de documento (case-insensitive).",
        max_length=200,
    )