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
from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session

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


def _resolve_db_session_id_use_ai(args, kwargs):
    db = kwargs.get("db")
    session_id = kwargs.get("session_id")
    use_ai = kwargs.get("use_ai", True)
    for item in args:
        if isinstance(item, Session) and db is None:
            db = item
        elif isinstance(item, bool):
            use_ai = item
        elif (isinstance(item, UUID) or isinstance(item, str)) and session_id is None:
            session_id = item
    if db is None:
        from app.core.database import SessionLocal

        db = SessionLocal()
        owns = True
    else:
        owns = False
    if session_id is None:
        if owns:
            db.close()
        raise AppError(code="session_not_found", message="La sesión solicitada no existe.", status_code=404)
    return db, (session_id if isinstance(session_id, UUID) else UUID(str(session_id))), bool(use_ai), owns


def analyze(*args: Any, **kwargs: Any) -> Diagnosis:
    """Analiza una sesión y devuelve su diagnóstico."""
    db, sid, use_ai, owns = _resolve_db_session_id_use_ai(args, kwargs)
    try:
        session_service.get_session(db, sid)

        with _lock_for(sid):
            content = content_service.extract(db, sid)
            stored = session_service.get_diagnosis(sid)

            if use_ai and stored is not None and stored.ai_status is AiStatus.OK:
                return stored

            rule_observations = run_rules(content)

            if not use_ai:
                if stored is not None and stored.ai_status is AiStatus.OK:
                    return _rules_only_diagnosis(sid, rule_observations)

                diagnosis = _rules_only_diagnosis(sid, rule_observations)
                session_service.save_diagnosis(diagnosis, db=db)
                session_service.mark_analyzed(db, sid)
                return diagnosis

            logger.info("analisis IA solicitado session_id=%s", sid)
            ai_result = _analyze_with_ai(content.blocks)

            observations = _merge_observations(
                rule_observations,
                ai_result.observations,
                content,
            )
            diagnosis = build_diagnosis(
                sid,
                observations,
                ai_status=ai_result.status,
                ai_notice=ai_result.notice,
                ai_truncated=ai_result.truncated,
            )
            session_service.save_diagnosis(diagnosis, db=db)
            session_service.mark_analyzed(db, sid)
            return diagnosis
    finally:
        if owns:
            db.close()


def get_diagnosis(*args: Any, **kwargs: Any) -> Diagnosis:
    """Devuelve el diagnóstico guardado de una sesión."""
    db = kwargs.get("db")
    session_id = kwargs.get("session_id")
    for item in args:
        if isinstance(item, Session) and db is None:
            db = item
        elif (isinstance(item, UUID) or isinstance(item, str)) and session_id is None:
            session_id = item
    if db is None:
        from app.core.database import SessionLocal

        db = SessionLocal()
        owns = True
    else:
        owns = False
    if session_id is None:
        if owns:
            db.close()
        raise AppError(code="session_not_found", message="La sesión solicitada no existe.", status_code=404)
    sid = session_id if isinstance(session_id, UUID) else UUID(str(session_id))

    try:
        session_service.get_session(db, sid)

        diagnosis = session_service.get_diagnosis(sid)
        if diagnosis is None:
            raise AppError(
                code="session_not_analyzed",
                message="La sesión todavía no fue analizada.",
                status_code=409,
            )
        return diagnosis
    finally:
        if owns:
            db.close()
