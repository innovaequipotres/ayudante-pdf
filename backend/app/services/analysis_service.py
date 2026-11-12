"""Lógica de negocio del diagnóstico de accesibilidad de una sesión.

El servicio extrae el contenido si hace falta, ejecuta las reglas automáticas
y, cuando se solicita, complementa el resultado con el análisis semántico de
la IA. El diagnóstico se guarda en memoria y la sesión pasa a ``analyzed``.

La IA se consulta una sola vez por sesión: si el diagnóstico guardado ya está
completo (``ai_status="ok"``) se reutiliza, mientras que un resultado
``unavailable`` se reintenta en la próxima llamada. Todo el acceso al
almacenamiento pasa por ``session_service``.
"""

from __future__ import annotations

import logging
import threading
from uuid import UUID

from app.core.exceptions import AppError
from app.scanner.ai_analysis import analyze_with_ai
from app.scanner.rules import run_rules, sort_observations
from app.scanner.scoring import build_diagnosis
from app.schemas.ai import AiAnalysisResult, AiStatus, build_ai_notice
from app.schemas.content import ContentBlock, ExtractedContent
from app.schemas.diagnosis import Diagnosis
from app.schemas.observation import Observation
from app.services import content_service, session_service
from app.services.ai_provider import get_provider_label

logger = logging.getLogger(__name__)

_UNEXPECTED_AI_NOTICE = (
    "No se pudo completar el análisis con IA; el diagnóstico por reglas "
    "sigue disponible."
)

# Un lock por sesión evita que dos llamadas simultáneas consulten a la IA dos
# veces. El lock global solo protege la creación de los locks.
_session_locks: dict[UUID, threading.Lock] = {}
_locks_guard = threading.Lock()


def _lock_for(session_id: UUID) -> threading.Lock:
    """Devuelve el lock de una sesión, creándolo si todavía no existe."""
    with _locks_guard:
        lock = _session_locks.get(session_id)
        if lock is None:
            lock = threading.Lock()
            _session_locks[session_id] = lock
        return lock


def _merge_observations(
    rule_observations: list[Observation],
    ai_observations: list[Observation],
    content: ExtractedContent,
) -> list[Observation]:
    """Une reglas e IA, descarta ids repetidos y ordena por el documento."""
    merged: list[Observation] = []
    seen: set[str] = set()
    for observation in [*rule_observations, *ai_observations]:
        if observation.id in seen:
            continue
        seen.add(observation.id)
        merged.append(observation)
    return sort_observations(merged, content)


def _rules_only_diagnosis(
    session_id: UUID,
    observations: list[Observation],
) -> Diagnosis:
    """Arma un diagnóstico solo con reglas y sin aviso de IA."""
    return build_diagnosis(
        session_id,
        observations,
        ai_status=AiStatus.SKIPPED,
        ai_notice=None,
        ai_truncated=False,
    )


def _analyze_with_ai(blocks: list[ContentBlock]) -> AiAnalysisResult:
    """Llama a la IA y garantiza que un fallo inesperado no corte la request."""
    try:
        return analyze_with_ai(blocks)
    except Exception:  # Defensa extra: la IA nunca debe producir un 5xx.
        logger.warning("El análisis con IA falló de forma inesperada.")
        notice = (
            f"{build_ai_notice(False, get_provider_label())} "
            f"{_UNEXPECTED_AI_NOTICE}"
        )
        return AiAnalysisResult(
            status=AiStatus.UNAVAILABLE,
            notice=notice,
            truncated=False,
            observations=[],
        )


def analyze(session_id: UUID, use_ai: bool = True) -> Diagnosis:
    """Analiza una sesión y devuelve su diagnóstico.

    Extrae el contenido si todavía no fue extraído y ejecuta siempre las
    reglas automáticas. Si ``use_ai`` es ``False`` no consulta a la IA. Si el
    diagnóstico guardado ya está completo, lo reutiliza; si quedó
    ``unavailable``, reintenta la IA.

    Raises:
        AppError: Si la sesión no existe (404) o si el contenido no se puede
            extraer (422).
    """
    session_service.get_session(session_id)

    with _lock_for(session_id):
        content = content_service.extract(session_id)
        stored = session_service.get_diagnosis(session_id)

        if use_ai and stored is not None and stored.ai_status is AiStatus.OK:
            return stored

        rule_observations = run_rules(content)

        if not use_ai:
            if stored is not None and stored.ai_status is AiStatus.OK:
                # No se pisa un diagnóstico completo: el GET sigue
                # devolviendo las observaciones de IA ya calculadas.
                return _rules_only_diagnosis(session_id, rule_observations)

            diagnosis = _rules_only_diagnosis(session_id, rule_observations)
            session_service.save_diagnosis(diagnosis)
            session_service.mark_analyzed(session_id)
            return diagnosis

        logger.info("analisis IA solicitado session_id=%s", session_id)
        ai_result = _analyze_with_ai(content.blocks)

        observations = _merge_observations(
            rule_observations,
            ai_result.observations,
            content,
        )
        diagnosis = build_diagnosis(
            session_id,
            observations,
            ai_status=ai_result.status,
            ai_notice=ai_result.notice,
            ai_truncated=ai_result.truncated,
        )
        session_service.save_diagnosis(diagnosis)
        session_service.mark_analyzed(session_id)
        return diagnosis


def get_diagnosis(session_id: UUID) -> Diagnosis:
    """Devuelve el diagnóstico guardado de una sesión.

    Raises:
        AppError: Si la sesión no existe (404) o si todavía no fue analizada
            (409).
    """
    session_service.get_session(session_id)

    diagnosis = session_service.get_diagnosis(session_id)
    if diagnosis is None:
        raise AppError(
            code="session_not_analyzed",
            message="La sesión todavía no fue analizada.",
            status_code=409,
        )
    return diagnosis
