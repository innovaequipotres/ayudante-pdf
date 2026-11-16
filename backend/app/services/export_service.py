"""Exportación del PDF con los textos finales de una adaptación.

La operación es stateless: lee el PDF original de la sesión, dibuja una capa
visual de reemplazo sobre los bloques indicados y devuelve el PDF resultante.
No persiste los textos ni modifica el estado de la sesión.

Limitación conocida
-------------------
El reemplazo es visual: se tapa el bloque con un rectángulo blanco y se dibuja
el texto nuevo encima, pero el texto original sigue en la capa de texto del
PDF. Copiar/pegar o un lector de pantalla pueden ver ambos textos. La redacción
real requiere borrar los operadores de texto del original y queda para otra
issue.
"""

from __future__ import annotations

import io
import re
from collections import defaultdict
from dataclasses import dataclass
from typing import cast
from urllib.parse import quote
from uuid import UUID

from pypdf import PdfReader, PdfWriter
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfgen.canvas import Canvas

from app.core.exceptions import AppError
from app.schemas.content import BlockType, ContentBlock, ExtractedContent
from app.schemas.export import ExportRequest
from app.schemas.session import SourceType
from app.services import content_service, session_service

__all__ = ["ExportResult", "export_pdf"]

_MAX_TEXT_CHARS = 8000
_DEFAULT_FONT_SIZE = 10.0
_MIN_FONT_SIZE = 6.0
_FONT_STEP = 0.5
_LEADING_FACTOR = 1.25
_RECT_PADDING = 0.5
_IMAGE_CAPTION_RATIO = 0.30
_MAX_FILENAME_STEM = 120
_ELLIPSIS = "…"

_INVALID_PDF_MESSAGE = (
    "No se pudo leer el PDF. Puede estar dañado o protegido."
)

_EXPORT_UNAVAILABLE = (
    "La exportación solo está disponible para sesiones creadas desde un PDF."
)
_UNKNOWN_BLOCK = "El bloque indicado no existe en el contenido extraído."
_BLOCK_WITHOUT_BBOX = (
    "El bloque indicado no tiene coordenadas válidas en el PDF."
)
_DUPLICATE_BLOCK = "El bloque indicado está repetido en la solicitud."
_EMPTY_TEXT = "El texto de un bloque no puede estar vacío."
_TEXT_TOO_LONG = (
    "El texto de un bloque supera el límite de 8.000 caracteres."
)


@dataclass(frozen=True)
class ExportResult:
    """PDF exportado y header listo para la respuesta HTTP."""

    content: bytes
    content_disposition: str


@dataclass(frozen=True)
class _PreparedEdit:
    """Edit validado, listo para dibujarse sobre el PDF."""

    block: ContentBlock
    text: str


def _validate_edits(
    content: ExtractedContent,
    payload: ExportRequest,
) -> list[_PreparedEdit]:
    """Valida los edits contra los bloques del contenido extraído.

    Raises:
        AppError: Con ``duplicate_block_id``, ``unknown_block``,
            ``block_without_bbox``, ``empty_text`` o ``text_too_long``.
    """
    blocks_by_id = {block.id: block for block in content.blocks}
    seen: set[str] = set()
    prepared: list[_PreparedEdit] = []

    for edit in payload.edits:
        if edit.block_id in seen:
            raise AppError("duplicate_block_id", _DUPLICATE_BLOCK, 422)

        block = blocks_by_id.get(edit.block_id)
        if block is None:
            raise AppError("unknown_block", _UNKNOWN_BLOCK, 422)

        bbox = block.bbox
        if (
            block.page is None
            or bbox is None
            or bbox.x1 <= bbox.x0
            or bbox.bottom <= bbox.top
        ):
            raise AppError("block_without_bbox", _BLOCK_WITHOUT_BBOX, 422)

        text = (
            edit.text.replace("\r\n", "\n").replace("\r", "\n").strip()
        )
        if not text:
            raise AppError("empty_text", _EMPTY_TEXT, 422)
        if len(text) > _MAX_TEXT_CHARS:
            raise AppError("text_too_long", _TEXT_TOO_LONG, 422)

        seen.add(edit.block_id)
        prepared.append(_PreparedEdit(block=block, text=text))

    return prepared


def _read_pdf(raw: bytes) -> tuple[PdfReader, list[tuple[float, float]]]:
    """Abre el PDF original y devuelve el lector y el MediaBox de sus páginas.

    Raises:
        AppError: Con ``invalid_pdf`` si el archivo no se puede abrir.
    """
    try:
        reader = PdfReader(io.BytesIO(raw))
        page_sizes = [
            (float(page.mediabox.width), float(page.mediabox.height))
            for page in reader.pages
        ]
    except Exception as exc:
        raise AppError("invalid_pdf", _INVALID_PDF_MESSAGE, 422) from exc

    if not page_sizes:
        raise AppError("invalid_pdf", _INVALID_PDF_MESSAGE, 422)

    return reader, page_sizes


def _split_long_word(
    word: str,
    font_name: str,
    size: float,
    max_width: float,
) -> list[str]:
    """Parte una palabra más ancha que el bloque en fragmentos."""
    chunks: list[str] = []
    current = ""
    for char in word:
        candidate = f"{current}{char}"
        if (
            current
            and pdfmetrics.stringWidth(candidate, font_name, size) > max_width
        ):
            chunks.append(current)
            current = char
        else:
            current = candidate
    if current:
        chunks.append(current)
    return chunks or [word]


def _wrap_line(
    text: str,
    font_name: str,
    size: float,
    max_width: float,
) -> list[str]:
    """Envuelve una línea de texto al ancho disponible."""
    lines: list[str] = []
    current = ""

    for word in text.split():
        candidate = f"{current} {word}".strip()
        if pdfmetrics.stringWidth(candidate, font_name, size) <= max_width:
            current = candidate
            continue

        if current:
            lines.append(current)

        if pdfmetrics.stringWidth(word, font_name, size) <= max_width:
            current = word
        else:
            chunks = _split_long_word(word, font_name, size, max_width)
            lines.extend(chunks[:-1])
            current = chunks[-1]

    if current:
        lines.append(current)

    return lines


def _wrap_text(
    text: str,
    font_name: str,
    size: float,
    max_width: float,
) -> list[str]:
    """Envuelve el texto conservando párrafos y saltos de línea.

    Los párrafos (separados por una o más líneas en blanco) quedan separados
    por una línea vacía; los saltos simples ``\\n`` cortan la línea sin dejar
    espacio adicional.
    """
    lines: list[str] = []
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")

    for paragraph in re.split(r"\n[ \t]*\n+", normalized):
        paragraph_lines: list[str] = []
        for source_line in paragraph.split("\n"):
            paragraph_lines.extend(
                _wrap_line(source_line, font_name, size, max_width)
            )

        if not paragraph_lines:
            continue
        if lines:
            lines.append("")
        lines.extend(paragraph_lines)

    return lines or [""]


def _with_ellipsis(
    line: str,
    font_name: str,
    size: float,
    max_width: float,
) -> str:
    """Recorta una línea y agrega ``…`` sin superar el ancho disponible."""
    text = f"{line}{_ELLIPSIS}"
    if pdfmetrics.stringWidth(text, font_name, size) <= max_width:
        return text

    trimmed = line
    while trimmed and (
        pdfmetrics.stringWidth(
            f"{trimmed}{_ELLIPSIS}", font_name, size
        ) > max_width
    ):
        trimmed = trimmed[:-1]

    return f"{trimmed.rstrip()}{_ELLIPSIS}" if trimmed else _ELLIPSIS


def _fit_text(
    text: str,
    font_name: str,
    initial_size: float,
    max_width: float,
    max_height: float,
) -> tuple[float, list[str]]:
    """Elige el tamaño de fuente y las líneas que entran en el bloque."""
    width = max(max_width, 1.0)
    height = max(max_height, 0.0)
    size = max(initial_size, 0.1)

    while size > _MIN_FONT_SIZE:
        leading = size * _LEADING_FACTOR
        lines = _wrap_text(text, font_name, size, width)
        if len(lines) * leading <= height:
            return size, lines

        next_size = max(_MIN_FONT_SIZE, size - _FONT_STEP)
        if next_size >= size:
            break
        size = next_size

    leading = size * _LEADING_FACTOR
    lines = _wrap_text(text, font_name, size, width)
    max_lines = max(1, int(height // leading)) if leading > 0 else 1

    if len(lines) > max_lines:
        lines = lines[:max_lines]
        while lines and not lines[-1]:
            lines.pop()
        if lines:
            lines[-1] = _with_ellipsis(
                lines[-1], font_name, size, width
            )
        else:
            lines = [_ELLIPSIS]

    return size, lines


def _draw_edit(
    canvas: Canvas,
    page_height: float,
    edit: _PreparedEdit,
) -> None:
    """Dibuja el rectángulo blanco y el texto de un bloque."""
    block = edit.block
    bbox = block.bbox

    # _validate_edits ya garantizó que page y bbox existen.
    assert bbox is not None

    block_height = bbox.bottom - bbox.top
    if block.type is BlockType.IMAGE:
        text_top = bbox.bottom - block_height * _IMAGE_CAPTION_RATIO
        text_height = block_height * _IMAGE_CAPTION_RATIO
        rect_top = text_top
        rect_bottom = bbox.bottom
    else:
        text_top = bbox.top
        text_height = block_height
        rect_top = bbox.top
        rect_bottom = bbox.bottom

    rect_x = bbox.x0 - _RECT_PADDING
    rect_y = page_height - rect_bottom - _RECT_PADDING
    rect_width = (bbox.x1 - bbox.x0) + 2 * _RECT_PADDING
    rect_height = (rect_bottom - rect_top) + 2 * _RECT_PADDING

    font_name = (
        "Helvetica-Bold"
        if block.type is BlockType.HEADING
        else "Helvetica"
    )
    initial_size = (
        block.font_size
        if block.font_size is not None and block.font_size > 0
        else _DEFAULT_FONT_SIZE
    )
    size, lines = _fit_text(
        edit.text,
        font_name,
        initial_size,
        bbox.x1 - bbox.x0,
        text_height,
    )
    leading = size * _LEADING_FACTOR

    canvas.saveState()
    canvas.setFillColorRGB(1, 1, 1)
    canvas.rect(rect_x, rect_y, rect_width, rect_height, stroke=0, fill=1)

    canvas.setFillColorRGB(0, 0, 0)
    canvas.setFont(font_name, size)
    text_y = page_height - text_top - size
    for line in lines:
        if line:
            canvas.drawString(bbox.x0, text_y, line)
        text_y -= leading
    canvas.restoreState()


def _build_overlay(
    page_sizes: list[tuple[float, float]],
    edits: list[_PreparedEdit],
) -> bytes:
    """Genera un PDF transparente con la capa de reemplazo."""
    edits_by_page: dict[int, list[_PreparedEdit]] = defaultdict(list)
    for edit in edits:
        page = edit.block.page
        if page is not None:
            edits_by_page[page].append(edit)

    buffer = io.BytesIO()
    canvas = Canvas(buffer, pagesize=page_sizes[0])

    for index, (width, height) in enumerate(page_sizes):
        if index:
            canvas.showPage()
            canvas.setPageSize((width, height))

        for edit in edits_by_page.get(index + 1, []):
            _draw_edit(canvas, height, edit)

    canvas.showPage()
    canvas.save()
    return buffer.getvalue()


def _merge_overlay(
    reader: PdfReader,
    overlay: bytes,
    edited_pages: set[int],
) -> bytes:
    """Fusiona el overlay con las páginas editadas del PDF original."""
    overlay_reader = PdfReader(io.BytesIO(overlay))
    writer = PdfWriter()
    writer.append(reader)

    for index in edited_pages:
        writer.pages[index - 1].merge_page(
            overlay_reader.pages[index - 1],
            over=True,
        )

    buffer = io.BytesIO()
    writer.write(buffer)
    return buffer.getvalue()


def _sanitize_filename_stem(filename: str | None) -> str:
    """Obtiene un nombre de archivo seguro a partir del nombre de la sesión."""
    name = re.sub(r"[\x00-\x1f\x7f]", "", filename or "")
    name = name.replace("\\", "/").rsplit("/", 1)[-1]
    name = name.replace('"', "")
    if name.lower().endswith(".pdf"):
        name = name[:-4]
    name = re.sub(r"\s+", " ", name).strip().strip(".")
    return name[:_MAX_FILENAME_STEM] or "documento"


def _content_disposition(stem: str) -> str:
    """Arma el header con fallback ASCII y nombre UTF-8 percent-encoded."""
    encoded_name = quote(f"{stem}_adaptado.pdf", safe="")
    return (
        'attachment; filename="documento-adaptado.pdf"; '
        f"filename*=UTF-8''{encoded_name}"
    )


def export_pdf(session_id: UUID, payload: ExportRequest) -> ExportResult:
    """Aplica los textos finales y devuelve el PDF con la capa de reemplazo.

    Raises:
        AppError: Con los errores de sesión, contenido, validación o PDF
            documentados para el endpoint de exportación.
    """
    session = session_service.get_session(session_id)

    if session.source_type is not SourceType.PDF:
        raise AppError("export_unavailable", _EXPORT_UNAVAILABLE, 409)

    content = content_service.get_content(session_id)
    edits = _validate_edits(content, payload)

    raw = cast(bytes, session_service.get_raw_content(session_id))
    reader, page_sizes = _read_pdf(raw)

    for edit in edits:
        page = edit.block.page
        if page is None or page < 1 or page > len(page_sizes):
            raise AppError("block_without_bbox", _BLOCK_WITHOUT_BBOX, 422)

    overlay = _build_overlay(page_sizes, edits)
    edited_pages = {
        edit.block.page
        for edit in edits
        if edit.block.page is not None
    }
    exported = _merge_overlay(reader, overlay, edited_pages)

    return ExportResult(
        content=exported,
        content_disposition=_content_disposition(
            _sanitize_filename_stem(session.filename)
        ),
    )
