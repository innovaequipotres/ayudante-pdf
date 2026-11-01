"""Lógica de negocio de la extracción de contenido.

El servicio elige el procesador según el origen de la sesión, completa los
bloques con identificadores y conteos, arma el resumen y guarda el resultado.
Todo el acceso al almacenamiento pasa por ``session_service``.
"""

from __future__ import annotations

from typing import cast
from uuid import UUID

from app.core.exceptions import AppError
from app.processors.pdf_processor import extract_from_pdf
from app.processors.text_processor import extract_from_text
from app.schemas.content import (
    BlockType,
    ContentBlock,
    ContentSummary,
    ExtractedContent,
)
from app.schemas.session import SessionResponse, SourceType
from app.services import session_service

_NO_TEXT_MESSAGE = (
    "No se encontró texto en el material. "
    "Si es un PDF escaneado, no se puede leer por ahora."
)


def _word_count(text: str | None) -> int:
    """Cuenta palabras separadas por espacios."""
    return len((text or "").split())


def _block_word_count(block: ContentBlock) -> int:
    """Calcula las palabras de un bloque; las imágenes no suman."""
    if block.type is BlockType.IMAGE:
        return 0
    if block.type is BlockType.LIST:
        return sum(_word_count(item) for item in (block.items or []))
    return _word_count(block.text)


def _content_title(
    session: SessionResponse,
    blocks: list[ContentBlock],
) -> str | None:
    """Determina el título del contenido según el origen de la sesión."""
    if session.source_type is SourceType.TEXT:
        return session.filename

    headings = [
        block
        for block in blocks
        if block.type is BlockType.HEADING
        and block.level is not None
        and block.text
    ]
    if not headings:
        return None

    min_level = min(block.level for block in headings if block.level is not None)
    return next(block.text for block in headings if block.level == min_level)


def build_content(
    session: SessionResponse,
    blocks: list[ContentBlock],
    page_count: int | None,
) -> ExtractedContent:
    """Completa los bloques y construye el contenido extraído de una sesión.

    Args:
        session: Sesión de origen.
        blocks: Bloques crudos devueltos por el procesador.
        page_count: Cantidad de páginas del PDF, o ``None`` para texto.

    Returns:
        El contenido con identificadores, conteos y resumen.

    Raises:
        AppError: Si el material no tiene palabras extraíbles.
    """
    enriched_blocks = [
        block.model_copy(
            update={
                "id": f"b{index}",
                "word_count": _block_word_count(block),
            }
        )
        for index, block in enumerate(blocks, start=1)
    ]

    summary = ContentSummary(
        word_count=sum(block.word_count for block in enriched_blocks),
        heading_count=sum(
            1 for block in enriched_blocks if block.type is BlockType.HEADING
        ),
        paragraph_count=sum(
            1 for block in enriched_blocks if block.type is BlockType.PARAGRAPH
        ),
        list_count=sum(
            1 for block in enriched_blocks if block.type is BlockType.LIST
        ),
        image_count=sum(
            1 for block in enriched_blocks if block.type is BlockType.IMAGE
        ),
        images_without_alt=sum(
            1
            for block in enriched_blocks
            if block.type is BlockType.IMAGE
            and not (block.alt_text or "").strip()
        ),
    )

    if summary.word_count == 0:
        raise AppError(
            code="no_extractable_text",
            message=_NO_TEXT_MESSAGE,
            status_code=422,
        )

    return ExtractedContent(
        session_id=session.session_id,
        source_type=session.source_type,
        title=_content_title(session, enriched_blocks),
        page_count=page_count,
        summary=summary,
        blocks=enriched_blocks,
    )


def extract(session_id: UUID) -> ExtractedContent:
    """Extrae el contenido de una sesión o devuelve el ya guardado.

    Raises:
        AppError: Si la sesión no existe (404), si el PDF no se puede leer
            (422) o si el material no tiene texto extraíble (422).
    """
    session = session_service.get_session(session_id)

    stored = session_service.get_extracted(session_id)
    if stored is not None:
        return stored

    raw_content = session_service.get_raw_content(session_id)

    if session.source_type is SourceType.PDF:
        blocks, page_count = extract_from_pdf(cast(bytes, raw_content))
    else:
        blocks = extract_from_text(cast(str, raw_content))
        page_count = None

    content = build_content(session, blocks, page_count)
    session_service.save_extracted(content)
    return content


def get_content(session_id: UUID) -> ExtractedContent:
    """Devuelve el contenido extraído de una sesión.

    Raises:
        AppError: Si la sesión no existe (404) o si el contenido todavía no fue
            extraído (409).
    """
    session_service.get_session(session_id)

    content = session_service.get_extracted(session_id)
    if content is None:
        raise AppError(
            code="content_not_extracted",
            message="El contenido todavía no fue extraído.",
            status_code=409,
        )
    return content
