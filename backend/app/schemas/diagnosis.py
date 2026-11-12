"""Modelos del diagnóstico de accesibilidad de un material."""

from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.ai import AiStatus
from app.schemas.observation import Category, Observation

SCORE_DISCLAIMER = (
    "El puntaje es un indicador orientativo. No constituye una certificación "
    "formal de accesibilidad."
)

# Las categorías se informan siempre, aunque no tengan observaciones.
DIAGNOSIS_CATEGORIES: tuple[Category, ...] = tuple(Category)


class DiagnosisLevel(str, Enum):
    """Nivel general de accesibilidad del material.

    ``ok`` indica que no se detectaron problemas, ``review`` que hay aspectos
    para revisar y ``barrier`` que al menos una observación es una barrera.
    """

    OK = "ok"
    REVIEW = "review"
    BARRIER = "barrier"


class CategoryResult(BaseModel):
    """Resultado del diagnóstico para una categoría de accesibilidad."""

    category: Category = Field(description="Categoría evaluada.")
    severity: DiagnosisLevel = Field(
        description="Peor nivel encontrado dentro de la categoría.",
    )
    barrier_count: int = Field(
        ge=0,
        description="Cantidad de observaciones que son una barrera.",
    )
    review_count: int = Field(
        ge=0,
        description="Cantidad de observaciones para revisar.",
    )
    suggestion_count: int = Field(
        ge=0,
        description="Cantidad de mejoras sugeridas.",
    )


class Diagnosis(BaseModel):
    """Resultado completo del análisis de accesibilidad de una sesión."""

    session_id: UUID = Field(description="Identificador de la sesión analizada.")
    score: int = Field(
        ge=0,
        le=100,
        description="Puntaje orientativo de accesibilidad, de 0 a 100.",
    )
    level: DiagnosisLevel = Field(description="Nivel general del material.")
    disclaimer: str = Field(
        default=SCORE_DISCLAIMER,
        description="Aviso sobre el alcance orientativo del puntaje.",
    )
    categories: list[CategoryResult] = Field(
        description="Resultado por categoría, en el orden de ``Category``.",
    )
    observations: list[Observation] = Field(
        description="Observaciones detectadas en el material.",
    )
    created_at: datetime = Field(description="Fecha y hora del diagnóstico.")
    ai_status: AiStatus = Field(
        default=AiStatus.SKIPPED,
        description=(
            "Resultado del análisis con IA: ``ok``, ``unavailable`` o "
            "``skipped`` cuando no se solicitó."
        ),
    )
    ai_notice: str | None = Field(
        default=None,
        description=(
            "Aviso de privacidad y alcance del análisis con IA. Nulo cuando "
            "el análisis se omitió."
        ),
    )
    ai_truncated: bool = Field(
        default=False,
        description="Indica si la IA analizó solo una parte del material.",
    )
