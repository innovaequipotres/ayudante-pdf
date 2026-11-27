"""Lógica de negocio de las sesiones.

Las sesiones se persisten en PostgreSQL a través de los modelos de BE-17 y
del almacenamiento de PDFs de BE-18. Este módulo es el único punto de acceso
a los datos de sesiones; los endpoints no manipulan las tablas directamente.
"""

from __future__ import annotations

from contextlib import contextmanager
from typing import Any, Iterator
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import SessionLocal
from app.core.exceptions import AppError
from app.models.diagnosis import DiagnosisRecord
from app.models.document import Document
from app.models.document_file import DocumentFile
from app.models.extracted_content import ExtractedContentRecord
from app.models.user import User
from app.schemas.content import ExtractedContent
from app.schemas.diagnosis import Diagnosis
from app.schemas.session import (
    SessionResponse,
    SessionStatus,
    SourceType,
    TextInput,
)
from app.services import storage

# El contenido extraído y los diagnósticos persisten en PostgreSQL.
_SYSTEM_USER_EMAIL = "sessions@ayudante-pdf.local"


@contextmanager
def _db_session(db: Session | None) -> Iterator[Session]:
    """Entrega una sesión usable, creando una propia si no se proporcionó."""
    if db is None:
        session = SessionLocal()
        owns = True
    else:
        session = db
        owns = False
    try:
        yield session
    finally:
        if owns:
            session.close()


def _resolve_uuid(value: Any) -> UUID:
    if isinstance(value, UUID):
        return value
    return UUID(str(value))


def _get_or_create_owner(db: Session) -> User:
    """Obtiene (o crea) el usuario sistema dueño de las sesiones anónimas."""
    user = db.query(User).filter(User.email == _SYSTEM_USER_EMAIL).first()
    if user is None:
        user = User(
            first_name="Sistema",
            last_name="Sesiones",
            email=_SYSTEM_USER_EMAIL,
            password_hash="!",
        )
        db.add(user)
        db.flush()
    return user


def _to_response(document: Document) -> SessionResponse:
    return SessionResponse(
        session_id=document.id,
        source_type=SourceType(document.source_type),
        filename=document.filename,
        size_bytes=document.size_bytes,
        status=SessionStatus(document.status),
        created_at=document.created_at,
    )


def _resolve_create_from_file(
    args: tuple[Any, ...], kwargs: dict[str, Any]
) -> tuple[Session, str, bytes, bool]:
    db = kwargs.get("db")
    filename = kwargs.get("filename")
    content = kwargs.get("content")
    for item in args:
        if isinstance(item, Session) and db is None:
            db = item
        elif isinstance(item, str) and filename is None:
            filename = item
        elif isinstance(item, (bytes, bytearray)) and content is None:
            content = bytes(item)
    owns = db is None
    if owns:
        db = SessionLocal()
    if filename is None:
        filename = ""
    if content is None:
        content = b""
    return db, filename, content, owns


def create_from_file(*args: Any, **kwargs: Any) -> SessionResponse:
    """Valida un archivo PDF y crea una sesión a partir de él."""
    db, filename, content, owns = _resolve_create_from_file(args, kwargs)

    # Validaciones (sin tocar la DB).
    if not filename.lower().endswith(".pdf"):
        if owns:
            db.close()
        raise AppError(
            code="unsupported_format",
            message="Por ahora solo se aceptan archivos PDF.",
            status_code=415,
        )

    if not content:
        if owns:
            db.close()
        raise AppError(
            code="empty_content",
            message="El archivo está vacío.",
            status_code=400,
        )

    if len(content) > settings.max_upload_bytes:
        if owns:
            db.close()
        raise AppError(
            code="file_too_large",
            message=(
                f"El archivo supera el límite de {settings.max_upload_mb} MB permitido."
            ),
            status_code=413,
        )

    if not content.startswith(b"%PDF"):
        if owns:
            db.close()
        raise AppError(
            code="invalid_pdf",
            message="El archivo no es un PDF válido.",
            status_code=400,
        )

    try:
        owner = _get_or_create_owner(db)
        document = Document(
            owner_id=owner.id,
            source_type=SourceType.PDF.value,
            filename=filename,
            size_bytes=len(content),
            status=SessionStatus.UPLOADED.value,
        )
        db.add(document)
        db.flush()

        storage.save_pdf(db, document.id, content)

        db.commit()
        db.refresh(document)
    except Exception:
        db.rollback()
        raise
    finally:
        if owns:
            db.close()

    return _to_response(document)


def _resolve_create_from_text(
    args: tuple[Any, ...], kwargs: dict[str, Any]
) -> tuple[Session, TextInput, bool]:
    db = kwargs.get("db")
    payload = kwargs.get("payload")
    for item in args:
        if isinstance(item, Session) and db is None:
            db = item
        elif isinstance(item, TextInput) and payload is None:
            payload = item
        elif isinstance(item, dict) and payload is None:
            payload = TextInput.model_validate(item)
    owns = db is None
    if owns:
        db = SessionLocal()
    if payload is None:
        raise AppError(code="empty_content", message="El texto no puede estar vacío.", status_code=400)
    return db, payload, owns


def create_from_text(*args: Any, **kwargs: Any) -> SessionResponse:
    """Valida un texto pegado y crea una sesión a partir de él."""
    db, payload, owns = _resolve_create_from_text(args, kwargs)

    if not payload.text.strip():
        if owns:
            db.close()
        raise AppError(
            code="empty_content",
            message="El texto no puede estar vacío.",
            status_code=400,
        )

    title = payload.title.strip() if payload.title else None

    try:
        owner = _get_or_create_owner(db)
        document = Document(
            owner_id=owner.id,
            source_type=SourceType.TEXT.value,
            filename=title or None,
            size_bytes=len(payload.text.encode("utf-8")),
            status=SessionStatus.UPLOADED.value,
        )
        db.add(document)
        db.flush()

        db.add(
            DocumentFile(
                document_id=document.id,
                owner_id=owner.id,
                content_text=payload.text,
            )
        )

        db.commit()
        db.refresh(document)
    except Exception:
        db.rollback()
        raise
    finally:
        if owns:
            db.close()

    return _to_response(document)


def _resolve_db_and_session_id(
    args: tuple[Any, ...], kwargs: dict[str, Any]
) -> tuple[Session, UUID, bool]:
    db = kwargs.get("db")
    session_id = kwargs.get("session_id")
    for item in args:
        if isinstance(item, Session) and db is None:
            db = item
        elif (isinstance(item, UUID) or isinstance(item, str)) and session_id is None:
            session_id = item
    owns = db is None
    if owns:
        db = SessionLocal()
    if session_id is None:
        if owns:
            db.close()
        raise AppError(
            code="session_not_found",
            message="La sesión solicitada no existe.",
            status_code=404,
        )
    return db, _resolve_uuid(session_id), owns


def get_session(*args: Any, **kwargs: Any) -> SessionResponse:
    """Devuelve la sesión indicada o lanza ``session_not_found``."""
    db, session_id, owns = _resolve_db_and_session_id(args, kwargs)

    try:
        document = db.get(Document, session_id)
        if document is None:
            raise AppError(
                code="session_not_found",
                message="La sesión solicitada no existe.",
                status_code=404,
            )
        return _to_response(document)
    finally:
        if owns:
            db.close()


def get_raw_content(*args: Any, **kwargs: Any) -> bytes | str:
    """Devuelve el contenido original (bytes del PDF o texto pegado)."""
    db, session_id, owns = _resolve_db_and_session_id(args, kwargs)

    try:
        document = db.get(Document, session_id)
        if document is None:
            raise AppError(
                code="session_not_found",
                message="La sesión solicitada no existe.",
                status_code=404,
            )

        if document.source_type == SourceType.PDF.value:
            return storage.read_pdf(db, session_id)

        stored = db.get(DocumentFile, session_id)
        if stored is None or stored.content_text is None:
            raise AppError(
                code="session_not_found",
                message="La sesión solicitada no existe.",
                status_code=404,
            )
        return stored.content_text
    finally:
        if owns:
            db.close()


def _resolve_db_and_session_id_extracted(
    args: tuple[Any, ...], kwargs: dict[str, Any]
) -> tuple[Session, UUID | None, bool]:
    db = kwargs.get("db")
    session_id = kwargs.get("session_id")
    content = kwargs.get("content")
    for item in args:
        if isinstance(item, Session) and db is None:
            db = item
        elif isinstance(item, ExtractedContent) and content is None:
            content = item
        elif (isinstance(item, UUID) or isinstance(item, str)) and session_id is None:
            session_id = item
    if content is not None and session_id is None:
        session_id = content.session_id
    owns = db is None
    if owns:
        db = SessionLocal()
    if session_id is None:
        if owns:
            db.close()
        raise AppError(
            code="session_not_found",
            message="La sesión solicitada no existe.",
            status_code=404,
        )
    return db, _resolve_uuid(session_id), owns


def get_extracted(*args: Any, **kwargs: Any) -> ExtractedContent | None:
    """Devuelve el contenido extraído o ``None`` si todavía no se extrajo."""
    db, session_id, owns = _resolve_db_and_session_id_extracted(args, kwargs)
    try:
        record = db.get(ExtractedContentRecord, session_id)
        if record is None:
            return None
        return ExtractedContent.model_validate(record.payload)
    finally:
        if owns:
            db.close()


def save_extracted(*args: Any, **kwargs: Any) -> None:
    """Persiste el contenido extraído y marca la sesión como extracted."""
    content = kwargs.get("content")
    db = kwargs.get("db")
    for item in args:
        if isinstance(item, ExtractedContent) and content is None:
            content = item
        elif isinstance(item, Session) and db is None:
            db = item
    if content is None:
        raise TypeError("save_extracted requiere el contenido extraído.")

    owns = db is None
    if owns:
        db = SessionLocal()

    try:
        document = db.get(Document, content.session_id)
        if document is None:
            raise AppError(
                code="session_not_found",
                message="La sesión solicitada no existe.",
                status_code=404,
            )
        document.status = SessionStatus.EXTRACTED.value

        record = db.get(ExtractedContentRecord, content.session_id)
        payload = content.model_dump(mode="json")
        if record is None:
            record = ExtractedContentRecord(
                document_id=content.session_id,
                owner_id=document.owner_id,
                payload=payload,
            )
            db.add(record)
        else:
            record.owner_id = document.owner_id
            record.payload = payload

        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        if owns:
            db.close()


def get_diagnosis(session_id: UUID, db: Session | None = None) -> Diagnosis | None:
    """Devuelve el diagnóstico guardado o ``None`` si todavía no se analizó.

    Lee el ``DiagnosisRecord`` de la base de datos y reconstruye el schema
    ``Diagnosis`` desde su ``payload`` JSONB.
    """
    sid = _resolve_uuid(session_id)

    owns = db is None
    if owns:
        db = SessionLocal()

    try:
        record = db.get(DiagnosisRecord, sid)
        if record is None:
            return None
        return Diagnosis.model_validate(record.payload)
    finally:
        if owns:
            db.close()


def save_diagnosis(*args: Any, **kwargs: Any) -> None:
    """Guarda el diagnóstico de una sesión en la base de datos."""
    diagnosis = kwargs.get("diagnosis")
    db = kwargs.get("db")
    for item in args:
        if isinstance(item, Diagnosis) and diagnosis is None:
            diagnosis = item
        elif isinstance(item, Session) and db is None:
            db = item
    if diagnosis is None:
        raise TypeError("save_diagnosis requiere el diagnóstico.")

    owns = db is None
    if owns:
        db = SessionLocal()

    try:
        document = db.get(Document, diagnosis.session_id)
        if document is None:
            raise AppError(
                code="session_not_found",
                message="La sesión solicitada no existe.",
                status_code=404,
            )

        record = db.get(DiagnosisRecord, diagnosis.session_id)
        payload = diagnosis.model_dump(mode="json")

        if record is None:
            record = DiagnosisRecord(
                document_id=diagnosis.session_id,
                owner_id=document.owner_id,
                payload=payload,
                score=diagnosis.score,
                level=diagnosis.level.value,
                ai_status=diagnosis.ai_status.value,
            )
            db.add(record)
        else:
            record.payload = payload
            record.score = diagnosis.score
            record.level = diagnosis.level.value
            record.ai_status = diagnosis.ai_status.value

        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        if owns:
            db.close()


def mark_analyzed(*args: Any, **kwargs: Any) -> SessionResponse:
    """Marca la sesión como ``analyzed`` sin retroceder una ya completada."""
    session_id = kwargs.get("session_id")
    db = kwargs.get("db")
    for item in args:
        if isinstance(item, Session) and db is None:
            db = item
        elif (isinstance(item, UUID) or isinstance(item, str)) and session_id is None:
            session_id = item

    if session_id is None:
        raise AppError(
            code="session_not_found",
            message="La sesión solicitada no existe.",
            status_code=404,
        )

    sid = _resolve_uuid(session_id)

    owns = db is None
    if owns:
        db = SessionLocal()

    try:
        session = get_session(db, sid)
        if session.status is SessionStatus.COMPLETED:
            return session

        document = db.get(Document, sid)
        if document is not None and document.status != SessionStatus.COMPLETED.value:
            document.status = SessionStatus.ANALYZED.value
        db.commit()
        return get_session(db, sid)
    except Exception:
        db.rollback()
        raise
    finally:
        if owns:
            db.close()