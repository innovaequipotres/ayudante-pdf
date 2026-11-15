"""Modelos de la adaptación de barreras con IA.

La adaptación es stateless: recibe el texto de una barrera y devuelve una
versión reescrita. No hay sesión, persistencia ni caché.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field, field_validator

from app.schemas.ai import AiStatus
from app.schemas.observation import Category

__all__ = [
    "Adaptation",
    "AdaptationRequest",
    "AdaptationSource",
    "AdaptationType",
]


class AdaptationType(str, Enum):
    """Tipo de adaptación que se pide para el texto."""

    SIMPLIFY = "simplify"
    CLARIFY = "clarify"
    DESCRIBE = "describe"
    ALT_TEXT = "alt_text"
    SEQUENCE = "sequence"


class AdaptationSource(str, Enum):
    """Origen del texto adaptado."""

    AI = "ai"
    LOCAL = "local"


class AdaptationRequest(BaseModel):
    """Barrera que se quiere adaptar.

    El ``type`` es obligatorio y manda: ``rule_id`` solo enriquece el prompt.
    El límite de 8.000 caracteres se valida en el motor para poder devolver
    ``text_too_long``; acá se documenta para que aparezca en ``/openapi.json``.
    """

    type: AdaptationType = Field(
        description="Tipo de adaptación pedida.",
    )
    original_text: str = Field(
        min_length=1,
        json_schema_extra={"maxLength": 8000},
        description="Texto de la barrera; máximo 8.000 caracteres.",
    )
    rule_id: str | None = Field(
        default=None,
        description=(
            "Código de la regla que originó la barrera. Solo se usa para "
            "enriquecer el prompt."
        ),
    )
    category: Category | None = Field(
        default=None,
        description="Dimensión de accesibilidad de la barrera.",
    )
    title: str | None = Field(
        default=None,
        max_length=200,
        description="Título de la observación.",
    )
    detail: str | None = Field(
        default=None,
        max_length=500,
        description="Detalle de la observación.",
    )
    recommendation: str | None = Field(
        default=None,
        max_length=500,
        description="Recomendación original de la observación.",
    )
    context_before: str | None = Field(
        default=None,
        max_length=1000,
        description="Texto inmediatamente anterior al bloque.",
    )
    context_after: str | None = Field(
        default=None,
        max_length=1000,
        description="Texto inmediatamente posterior al bloque.",
    )

    @field_validator("original_text")
    @classmethod
    def _not_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("original_text no puede estar vacío.")
        return value


class Adaptation(BaseModel):
    """Versión adaptada de una barrera."""

    id: str = Field(description="Identificador único de la adaptación (UUID v4).")
    type: AdaptationType = Field(description="Tipo de adaptación aplicado.")
    rule_id: str | None = Field(
        default=None,
        description="Código de la regla que originó la barrera.",
    )
    original_text: str = Field(description="Texto recibido, normalizado.")
    adapted_text: str | None = Field(
        default=None,
        description=(
            "Texto adaptado en texto plano. Es nulo si no se pudo generar."
        ),
    )
    notes: str | None = Field(
        default=None,
        max_length=500,
        description="Qué se hizo, limitaciones o recomendación manual.",
    )
    source: AdaptationSource | None = Field(
        default=None,
        description="Origen del texto adaptado: IA o fallback local.",
    )
    ai_status: AiStatus = Field(
        description="Indica si la IA pudo generar la adaptación.",
    )
    ai_notice: str | None = Field(
        default=None,
        description="Aviso de privacidad y alcance del uso de la IA.",
    )
    provider: str | None = Field(
        default=None,
        description="Nombre visible del proveedor usado o intentado.",
    )
    created_at: datetime = Field(description="Fecha de creación en UTC.")
