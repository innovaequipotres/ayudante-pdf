"""Modelos de los bloques de contenido extraídos de un material educativo."""

from enum import Enum
from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.session import SourceType


class BlockType(str, Enum):
    """Tipo de bloque de contenido detectado en un documento."""

    HEADING = "heading"
    PARAGRAPH = "paragraph"
    LIST = "list"
    IMAGE = "image"


class ContentBlock(BaseModel):
    """Unidad de contenido extraída de un documento.

    El procesador deja ``id`` vacío y ``word_count`` en 0: ``content_service``
    los completa al construir el contenido extraído. Los campos que no
    corresponden al tipo de bloque quedan en ``None``.
    """

    id: str = Field(
        default="",
        description=(
            "Identificador del bloque. El procesador lo deja vacío; "
            "``content_service`` lo asigna."
        ),
    )
    type: BlockType = Field(description="Tipo de bloque de contenido.")
    page: int | None = Field(
        default=None,
        ge=1,
        description="Página donde empieza el bloque (empieza en 1).",
    )
    text: str | None = Field(
        default=None,
        description="Texto del bloque; se usa en títulos y párrafos.",
    )
    level: int | None = Field(
        default=None,
        ge=1,
        le=6,
        description="Nivel del título (1 a 6); solo se usa en títulos.",
    )
    items: list[str] | None = Field(
        default=None,
        description="Ítems de la lista, sin la viñeta ni la numeración.",
    )
    word_count: int = Field(
        default=0,
        ge=0,
        description=(
            "Cantidad de palabras del bloque. El procesador la deja en 0; "
            "``content_service`` la calcula."
        ),
    )
    alt_text: str | None = Field(
        default=None,
        description="Texto alternativo de una imagen; solo se usa en imágenes.",
    )
    width: float | None = Field(
        default=None,
        ge=0,
        description="Ancho en puntos; solo se usa en imágenes.",
    )
    height: float | None = Field(
        default=None,
        ge=0,
        description="Alto en puntos; solo se usa en imágenes.",
    )


class ContentSummary(BaseModel):
    """Resumen cuantitativo del contenido extraído de un material."""

    word_count: int = Field(
        ge=0,
        description="Total de palabras del material; las imágenes no suman.",
    )
    heading_count: int = Field(ge=0, description="Cantidad de títulos.")
    paragraph_count: int = Field(ge=0, description="Cantidad de párrafos.")
    list_count: int = Field(ge=0, description="Cantidad de listas.")
    image_count: int = Field(ge=0, description="Cantidad de imágenes.")
    images_without_alt: int = Field(
        ge=0,
        description="Cantidad de imágenes sin texto alternativo.",
    )


class ExtractedContent(BaseModel):
    """Contenido estructurado extraído de una sesión."""

    session_id: UUID = Field(description="Identificador de la sesión de origen.")
    source_type: SourceType = Field(description="Origen del material: PDF o texto.")
    title: str | None = Field(
        default=None,
        description=(
            "Título del material. En texto es el título de la sesión; en PDF es "
            "el título de menor nivel. Puede ser nulo si no se detectó."
        ),
    )
    page_count: int | None = Field(
        default=None,
        ge=1,
        description="Cantidad de páginas del PDF; nulo para texto pegado.",
    )
    summary: ContentSummary = Field(description="Resumen cuantitativo del contenido.")
    blocks: list[ContentBlock] = Field(
        description="Bloques de contenido en orden de lectura.",
    )
