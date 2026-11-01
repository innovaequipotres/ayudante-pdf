"""Modelos de los bloques de contenido extraídos de un material educativo."""

from enum import Enum

from pydantic import BaseModel, Field


class BlockType(str, Enum):
    """Tipo de bloque de contenido detectado en un documento."""

    HEADING = "heading"
    PARAGRAPH = "paragraph"
    LIST = "list"
    IMAGE = "image"


class ContentBlock(BaseModel):
    """Unidad de contenido extraída de un documento.

    El procesador deja ``id`` vacío y ``word_count`` en 0: ambos se completan en
    etapas posteriores. Los campos que no corresponden al tipo de bloque quedan
    en ``None``.
    """

    id: str = Field(
        default="",
        description=(
            "Identificador del bloque. El procesador lo deja vacío; se asigna "
            "en una etapa posterior."
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
            "Cantidad de palabras del bloque. El procesador la deja en 0; se "
            "calcula en una etapa posterior."
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
