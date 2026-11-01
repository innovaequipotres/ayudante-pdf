"""Lógica de negocio de las sesiones.

El almacenamiento es temporal y en memoria: más adelante se reemplazará por una
base de datos. Todo el acceso a los datos pasa por las funciones de este módulo,
de modo que los endpoints nunca manipulan los diccionarios directamente.
"""

from datetime import UTC, datetime
from uuid import UUID, uuid4

from app.core.config import settings
from app.core.exceptions import AppError
from app.schemas.content import ExtractedContent
from app.schemas.session import SessionResponse, SessionStatus, SourceType, TextInput

_sessions: dict[UUID, SessionResponse] = {}
_raw_contents: dict[UUID, bytes | str] = {}
_extracted_contents: dict[UUID, ExtractedContent] = {}


def _create_session(
    source_type: SourceType,
    filename: str | None,
    size_bytes: int,
    raw_content: bytes | str,
) -> SessionResponse:
    """Crea, almacena y devuelve una sesión nueva en estado ``uploaded``."""
    session = SessionResponse(
        session_id=uuid4(),
        source_type=source_type,
        filename=filename,
        size_bytes=size_bytes,
        status=SessionStatus.UPLOADED,
        created_at=datetime.now(UTC),
    )
    _sessions[session.session_id] = session
    _raw_contents[session.session_id] = raw_content
    return session


def create_from_file(filename: str, content: bytes) -> SessionResponse:
    """Valida un archivo PDF y crea una sesión a partir de él."""
    if not filename.lower().endswith(".pdf"):
        raise AppError(
            code="unsupported_format",
            message="Por ahora solo se aceptan archivos PDF.",
            status_code=415,
        )

    if not content:
        raise AppError(
            code="empty_content",
            message="El archivo está vacío.",
            status_code=400,
        )

    if len(content) > settings.max_upload_bytes:
        raise AppError(
            code="file_too_large",
            message=(
                f"El archivo supera el límite de {settings.max_upload_mb} MB permitido."
            ),
            status_code=413,
        )

    if not content.startswith(b"%PDF"):
        raise AppError(
            code="invalid_pdf",
            message="El archivo no es un PDF válido.",
            status_code=400,
        )

    return _create_session(
        source_type=SourceType.PDF,
        filename=filename,
        size_bytes=len(content),
        raw_content=content,
    )


def create_from_text(payload: TextInput) -> SessionResponse:
    """Valida un texto pegado y crea una sesión a partir de él."""
    if not payload.text.strip():
        raise AppError(
            code="empty_content",
            message="El texto no puede estar vacío.",
            status_code=400,
        )

    title = payload.title.strip() if payload.title else None

    return _create_session(
        source_type=SourceType.TEXT,
        filename=title or None,
        size_bytes=len(payload.text.encode("utf-8")),
        raw_content=payload.text,
    )


def get_session(session_id: UUID) -> SessionResponse:
    """Devuelve la sesión indicada o lanza ``session_not_found``."""
    session = _sessions.get(session_id)
    if session is None:
        raise AppError(
            code="session_not_found",
            message="La sesión solicitada no existe.",
            status_code=404,
        )
    return session


def get_raw_content(session_id: UUID) -> bytes | str:
    """Devuelve el contenido original (bytes del PDF o texto pegado)."""
    get_session(session_id)
    return _raw_contents[session_id]


def get_extracted(session_id: UUID) -> ExtractedContent | None:
    """Devuelve el contenido extraído o ``None`` si todavía no se extrajo."""
    return _extracted_contents.get(session_id)


def save_extracted(content: ExtractedContent) -> None:
    """Guarda el contenido extraído y marca la sesión como ``extracted``."""
    session = get_session(content.session_id)
    _sessions[content.session_id] = session.model_copy(
        update={"status": SessionStatus.EXTRACTED}
    )
    _extracted_contents[content.session_id] = content
