"""Schemas de carpetas para la biblioteca de documentos."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class FolderCreate(BaseModel):
    """Datos para crear una carpeta."""

    name: str = Field(
        description="Nombre de la carpeta. Se recorta automáticamente.",
        min_length=1,
        max_length=200,
    )
    parent_id: UUID | None = Field(
        default=None,
        description="ID de la carpeta padre. Null para carpetas raíz.",
    )


class FolderResponse(BaseModel):
    """Datos públicos de una carpeta."""

    id: UUID = Field(description="Identificador único de la carpeta.")
    owner_id: UUID = Field(description="Usuario dueño de la carpeta.")
    parent_id: UUID | None = Field(description="Carpeta padre (null si es raíz).")
    name: str = Field(description="Nombre de la carpeta.")
    created_at: datetime = Field(description="Fecha de creación en UTC.")
    updated_at: datetime = Field(description="Fecha de última modificación en UTC.")


class FolderUpdate(BaseModel):
    """Datos para actualizar una carpeta."""

    name: str | None = Field(
        default=None,
        description="Nuevo nombre de la carpeta.",
        min_length=1,
        max_length=200,
    )
    parent_id: UUID | None = Field(
        default=None,
        description="Nueva carpeta padre. Null para mover a raíz.",
    )