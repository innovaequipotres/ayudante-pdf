"""Cálculo del puntaje y los niveles del diagnóstico de accesibilidad.

El puntaje es una suma de penalizaciones por observación: cada regla resta
según la severidad de sus hallazgos y tiene un tope para que un solo problema
repetido no opaque el resto del material. La ponderación es una propuesta
inicial y debe validarse con el equipo de Accesibilidad (BE-10).
"""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from app.schemas.ai import AiStatus
from app.schemas.diagnosis import (
    DIAGNOSIS_CATEGORIES,
    SCORE_DISCLAIMER,
    CategoryResult,
    Diagnosis,
    DiagnosisLevel,
)
from app.schemas.observation import Observation, Severity

__all__ = [
    "MAX_PENALTY_PER_RULE",
    "SEVERITY_PENALTY",
    "build_diagnosis",
    "calculate_score",
    "category_results",
    "overall_level",
]

# --- Ponderación (a validar con Accesibilidad, BE-10) ---
SEVERITY_PENALTY: dict[Severity, int] = {
    Severity.HIGH: 10,  # barrera
    Severity.MEDIUM: 4,  # para revisar
    Severity.LOW: 1,  # mejora sugerida
}
MAX_PENALTY_PER_RULE = 30  # una misma regla no puede restar más que esto
MAX_SCORE = 100


def calculate_score(observations: list[Observation]) -> int:
    """Calcula el puntaje de 0 a 100 a partir de las observaciones.

    Las penalizaciones se agrupan por regla y cada regla se limita a
    ``MAX_PENALTY_PER_RULE``. Un material sin observaciones obtiene 100.
    """
    per_rule: dict[str, int] = {}
    for observation in observations:
        penalty = SEVERITY_PENALTY[observation.severity]
        per_rule[observation.rule_id] = (
            per_rule.get(observation.rule_id, 0) + penalty
        )

    total = sum(
        min(penalty, MAX_PENALTY_PER_RULE) for penalty in per_rule.values()
    )
    return max(0, MAX_SCORE - total)


def overall_level(observations: list[Observation]) -> DiagnosisLevel:
    """Devuelve el peor nivel presente en un conjunto de observaciones."""
    if any(
        observation.severity is Severity.HIGH for observation in observations
    ):
        return DiagnosisLevel.BARRIER
    if observations:
        return DiagnosisLevel.REVIEW
    return DiagnosisLevel.OK


def category_results(observations: list[Observation]) -> list[CategoryResult]:
    """Agrupa las observaciones por categoría.

    Siempre devuelve las seis categorías, en el orden de ``Category``, para que
    el cliente pueda mostrar también las que no tienen hallazgos.
    """
    results: list[CategoryResult] = []
    for category in DIAGNOSIS_CATEGORIES:
        found = [
            observation
            for observation in observations
            if observation.category is category
        ]
        results.append(
            CategoryResult(
                category=category,
                severity=overall_level(found),
                barrier_count=sum(
                    1
                    for observation in found
                    if observation.severity is Severity.HIGH
                ),
                review_count=sum(
                    1
                    for observation in found
                    if observation.severity is Severity.MEDIUM
                ),
                suggestion_count=sum(
                    1
                    for observation in found
                    if observation.severity is Severity.LOW
                ),
            )
        )
    return results


def build_diagnosis(
    session_id: UUID,
    observations: list[Observation],
    *,
    ai_status: AiStatus = AiStatus.SKIPPED,
    ai_notice: str | None = None,
    ai_truncated: bool = False,
) -> Diagnosis:
    """Arma el diagnóstico completo de una sesión a partir de sus hallazgos.

    Los parámetros de IA son opcionales para que el puntaje se pueda usar sin
    análisis semántico. Por defecto el diagnóstico queda como ``skipped``.
    """
    return Diagnosis(
        session_id=session_id,
        score=calculate_score(observations),
        level=overall_level(observations),
        disclaimer=SCORE_DISCLAIMER,
        categories=category_results(observations),
        observations=observations,
        created_at=datetime.now(UTC),
        ai_status=ai_status,
        ai_notice=ai_notice,
        ai_truncated=ai_truncated,
    )
