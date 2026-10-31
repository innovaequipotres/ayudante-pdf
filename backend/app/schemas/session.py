from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, Field


class SourceType(str, Enum):
    """Origen del material educativo cargado en una sesión."""

    PDF = "pdf"
    TEXT = "text"


class SessionStatus(str, Enum):
    """Estados por los que pasa una sesión de análisis."""

    UPLOADED = "uploaded"
    EXTRACTED = "extracted"
    ANALYZED = "analyzed"
    COMPLETED = "completed"


class TextInput(BaseModel):
    """Texto pegado directamente por el docente."""

    title: str | None = Field(
        default=None,
        max_length=200,
        description="Título opcional del texto (máximo 200 caracteres).",
    )
    text: str = Field(
        description=(
            "Contenido del texto. No puede estar vacío ni contener solo "
            "espacios; se valida en el servicio."
        ),
    )


class SessionResponse(BaseModel):
    """Datos públicos de una sesión."""

    session_id: UUID = Field(description="Identificador único de la sesión.")
    source_type: SourceType = Field(description="Origen del material: PDF o texto.")
    filename: str | None = Field(
        default=None,
        description="Nombre del archivo PDF o título del texto.",
    )
    size_bytes: int | None = Field(
        default=None,
        description="Tamaño del contenido en bytes (UTF-8 para texto).",
    )
    status: SessionStatus = Field(description="Estado actual de la sesión.")
    created_at: datetime = Field(description="Fecha de creación en UTC.")
