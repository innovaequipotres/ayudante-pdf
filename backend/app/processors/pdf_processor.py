"""Extracción heurística de contenido estructurado desde archivos PDF.

El procesador recorre el PDF página por página, clasifica las líneas de texto
como títulos, ítems de lista o párrafos y ordena las imágenes según su posición
vertical.

Limitaciones conocidas
----------------------
- **Columnas múltiples:** el orden de lectura puede mezclar el contenido de las
  columnas, porque se usa el orden que devuelve ``pdfplumber``.
- **Tablas:** las celdas se tratan como líneas de texto; pueden aparecer como
  párrafos, títulos o listas.
- **Encabezados y pies repetidos:** no se detectan ni se eliminan, salvo los
  números de página con los formatos contemplados. Pueden terminar como
  párrafos o títulos en cada página.
- **Párrafos que cruzan de página:** como cada página se procesa por separado,
  el párrafo queda dividido en dos bloques.
- **PDFs escaneados:** si no hay capa de texto se devuelve una lista vacía y la
  cantidad de páginas; no se aplica OCR.
- **Imágenes:** ``pdfplumber`` no expone el texto alternativo, por lo que
  ``alt_text`` siempre queda en ``None``. Los logos y adornos que superan los
  20 puntos también se incluyen.
- **Listas anidadas:** se aplanan en un solo bloque de ítems.
- **Continuaciones de lista:** una línea que se corta al mismo ``x0`` que el
  marcador no se reconoce como continuación del ítem.
- **Numeración de páginas:** solo se reconocen los formatos ``3``,
  ``Página 3``, ``3/10`` y variantes equivalentes; la numeración romana o los
  números desplazados respecto de la página real no se detectan.
- **Niveles de título:** una portada con muchos tamaños distintos puede asignar
  niveles profundos a los títulos de sección.
- **Negrita:** se detecta por la presencia de ``bold`` en el nombre de la
  fuente. Fuentes como ``Black`` o ``Heavy`` no se consideran negrita.
"""

from __future__ import annotations

import io
import re
from collections import Counter
from dataclasses import dataclass, field
from statistics import median
from typing import Any

import pdfplumber
from pdfplumber.utils.exceptions import MalformedPDFException, PdfminerException

from app.core.exceptions import AppError
from app.schemas.content import BlockType, ContentBlock

__all__ = ["BULLET_RE", "extract_from_pdf"]

# Coincide con el inicio de una línea que empieza con una viñeta, numeración,
# letra minúscula o una viñeta codificada como (cid:NNN). ``match.end()`` marca
# dónde empieza el texto del ítem, sin el marcador.
BULLET_RE = re.compile(
    r"^\s*(?:"
    r"(?P<bullet>[•●▪◦·*\-–—])"
    r"|(?P<number>\d{1,3}[.)])(?=\s|$)"
    r"|(?P<letter>[a-z][.)])(?=\s|$)"
    r"|(?P<cid>\(cid:\d+\))"
    r")\s*"
)

_PAGE_NUMBER_RE = re.compile(
    r"^(?:(?P<label>(?:p[áa]g(?:ina)?|page)\.?)\s*:?\s*)?"
    r"(?P<current>\d{1,4})"
    r"(?:\s*(?:/|de)\s*(?P<total>\d{1,4}))?$",
    re.IGNORECASE,
)

_BODY_HEADING_FACTOR = 1.15
_MAX_HEADING_WORDS = 25
_MAX_BOLD_HEADING_CHARS = 80
_BOLD_CHAR_RATIO = 0.8
_BOLD_LINE_RATIO = 0.5
_MAX_HEADING_LEVEL = 6
_PARAGRAPH_GAP_FACTOR = 0.6
_HEADING_GAP_FACTOR = 0.6
_INDENT_TOLERANCE = 2.0
_MIN_IMAGE_SIDE = 20.0

_INVALID_PDF_MESSAGE = "No se pudo leer el PDF. Puede estar dañado o protegido."


@dataclass
class _Line:
    """Línea de texto con los datos necesarios para clasificarla."""

    text: str
    x0: float
    top: float
    bottom: float
    size: int
    bold: bool
    char_count: int
    heading_level: int | None = None
    list_item: str | None = None


@dataclass
class _Image:
    """Imagen relevante de una página, en coordenadas de la página."""

    top: float
    x0: float
    width: float
    height: float


@dataclass
class _PageContent:
    """Líneas e imágenes leídas de una página."""

    page_number: int
    lines: list[_Line]
    images: list[_Image]


@dataclass
class _OpenBlock:
    """Bloque en construcción mientras se agrupan líneas consecutivas."""

    kind: str
    page: int
    last_bottom: float
    last_size: int = 0
    level: int | None = None
    text: str = ""
    items: list[str] = field(default_factory=list)
    item_x0: float = 0.0

    def to_content_block(self) -> ContentBlock:
        """Convierte el bloque abierto en el modelo público."""
        if self.kind == "heading":
            return ContentBlock(
                type=BlockType.HEADING,
                page=self.page,
                text=self.text,
                level=self.level,
            )
        if self.kind == "list":
            return ContentBlock(
                type=BlockType.LIST,
                page=self.page,
                items=list(self.items),
            )
        return ContentBlock(
            type=BlockType.PARAGRAPH,
            page=self.page,
            text=self.text,
        )


def _normalize_text(text: str) -> str:
    """Colapsa espacios y saltos de línea en un único espacio."""
    return " ".join(text.split())


def _word_count(text: str) -> int:
    """Cuenta palabras separadas por espacios."""
    return len(text.split())


def _is_bold(chars: list[dict[str, Any]]) -> bool:
    """Indica si más del 80 % de los caracteres usan una fuente negrita."""
    if not chars:
        return False
    bold_chars = sum("bold" in str(char.get("fontname", "")).lower() for char in chars)
    return bold_chars / len(chars) > _BOLD_CHAR_RATIO


def _is_page_number(text: str, page_number: int, page_count: int) -> bool:
    """Detecta líneas que son únicamente un número de página."""
    match = _PAGE_NUMBER_RE.fullmatch(text)
    if match is None:
        return False

    # "Página 3" es un número de página aunque el índice no coincida (por
    # ejemplo, si la numeración visible empieza en la portada).
    if match.group("label"):
        return True

    current = int(match.group("current"))
    total = match.group("total")
    if total is not None:
        return current == page_number or int(total) == page_count

    # Un número suelto solo se descarta si coincide con la página actual, para
    # no borrar números que forman parte del contenido.
    return current == page_number


def _read_images(page: Any) -> list[_Image]:
    """Lee las imágenes con ancho y alto mayores o iguales a 20 puntos."""
    images: list[_Image] = []
    for raw_image in page.images:
        width = float(raw_image.get("width") or 0.0)
        height = float(raw_image.get("height") or 0.0)
        if width < _MIN_IMAGE_SIDE or height < _MIN_IMAGE_SIDE:
            continue
        images.append(
            _Image(
                top=float(raw_image.get("top") or 0.0),
                x0=float(raw_image.get("x0") or 0.0),
                width=width,
                height=height,
            )
        )
    return sorted(images, key=lambda image: (image.top, image.x0))


def _read_page(
    page: Any,
    page_number: int,
    page_count: int,
) -> _PageContent:
    """Extrae las líneas y las imágenes relevantes de una página."""
    lines: list[_Line] = []

    for raw_line in page.extract_text_lines():
        text = _normalize_text(str(raw_line.get("text") or ""))
        chars = raw_line.get("chars") or []
        if not text or not chars:
            continue
        if _is_page_number(text, page_number, page_count):
            continue

        sizes = [float(char["size"]) for char in chars if char.get("size") is not None]
        if not sizes:
            continue

        lines.append(
            _Line(
                text=text,
                x0=float(raw_line["x0"]),
                top=float(raw_line["top"]),
                bottom=float(raw_line["bottom"]),
                size=int(median(sizes) + 0.5),
                bold=_is_bold(chars),
                char_count=len(sizes),
            )
        )

    return _PageContent(
        page_number=page_number,
        lines=lines,
        images=_read_images(page),
    )


def _body_font_size(lines: list[_Line]) -> int:
    """Calcula el tamaño de letra más frecuente, ponderado por caracteres."""
    weights: Counter[int] = Counter()
    for line in lines:
        weights[line.size] += line.char_count
    if not weights:
        return 0
    return weights.most_common(1)[0][0]


def _heading_levels(lines: list[_Line], body_size: int) -> dict[int, int]:
    """Asigna niveles a los tamaños grandes, de mayor a menor."""
    heading_sizes = {
        line.size
        for line in lines
        if line.size >= body_size * _BODY_HEADING_FACTOR
        and _word_count(line.text) <= _MAX_HEADING_WORDS
    }
    return {
        size: min(index + 1, _MAX_HEADING_LEVEL)
        for index, size in enumerate(sorted(heading_sizes, reverse=True))
    }


def _classify_line(
    line: _Line,
    body_size: int,
    size_levels: dict[int, int],
    allow_bold_headings: bool,
) -> None:
    """Clasifica una línea como título, ítem de lista o párrafo."""
    is_large = line.size >= body_size * _BODY_HEADING_FACTOR

    if is_large and _word_count(line.text) <= _MAX_HEADING_WORDS:
        line.heading_level = size_levels.get(line.size, _MAX_HEADING_LEVEL)
        return

    match = BULLET_RE.match(line.text)
    if match is not None:
        item = _normalize_text(line.text[match.end() :])
        if item:
            line.list_item = item
        else:
            # Una línea que solo contiene el marcador no aporta contenido.
            line.text = ""
        return

    if (
        allow_bold_headings
        and line.bold
        and len(line.text) <= _MAX_BOLD_HEADING_CHARS
        and not line.text.endswith((".", ",", ";"))
    ):
        line.heading_level = min(
            len(size_levels) + 1,
            _MAX_HEADING_LEVEL,
        )


def _image_block(page_number: int, image: _Image) -> ContentBlock:
    """Crea el bloque público de una imagen."""
    return ContentBlock(
        type=BlockType.IMAGE,
        page=page_number,
        width=round(image.width, 1),
        height=round(image.height, 1),
    )


def _group_page(page: _PageContent, body_size: int) -> list[ContentBlock]:
    """Agrupa las líneas de una página y ordena las imágenes entre ellas."""
    blocks: list[ContentBlock] = []
    current: _OpenBlock | None = None
    image_index = 0
    images = page.images

    def flush() -> None:
        nonlocal current
        if current is not None:
            blocks.append(current.to_content_block())
            current = None

    for line in page.lines:
        if not line.text:
            continue

        # Una imagen corta el bloque actual y se emite en el orden de lectura.
        while image_index < len(images) and images[image_index].top <= line.top:
            flush()
            blocks.append(_image_block(page.page_number, images[image_index]))
            image_index += 1

        if line.heading_level is not None:
            if (
                current is not None
                and current.kind == "heading"
                and current.level == line.heading_level
                and line.top - current.last_bottom
                <= _HEADING_GAP_FACTOR * max(current.last_size, line.size)
            ):
                current.text = f"{current.text} {line.text}"
                current.last_bottom = line.bottom
                current.last_size = line.size
            else:
                flush()
                current = _OpenBlock(
                    kind="heading",
                    page=page.page_number,
                    last_bottom=line.bottom,
                    last_size=line.size,
                    level=line.heading_level,
                    text=line.text,
                )
        elif line.list_item is not None:
            if current is not None and current.kind == "list":
                current.items.append(line.list_item)
                current.item_x0 = line.x0
                current.last_bottom = line.bottom
                current.last_size = line.size
            else:
                flush()
                current = _OpenBlock(
                    kind="list",
                    page=page.page_number,
                    last_bottom=line.bottom,
                    last_size=line.size,
                    items=[line.list_item],
                    item_x0=line.x0,
                )
        else:
            is_list_continuation = (
                current is not None
                and current.kind == "list"
                and line.top - current.last_bottom <= _PARAGRAPH_GAP_FACTOR * body_size
                and line.x0 > current.item_x0 + _INDENT_TOLERANCE
            )
            is_paragraph_continuation = (
                current is not None
                and current.kind == "paragraph"
                and line.top - current.last_bottom <= _PARAGRAPH_GAP_FACTOR * body_size
            )

            if is_list_continuation:
                current.items[-1] = f"{current.items[-1]} {line.text}"
                current.last_bottom = line.bottom
                current.last_size = line.size
            elif is_paragraph_continuation:
                current.text = f"{current.text} {line.text}"
                current.last_bottom = line.bottom
                current.last_size = line.size
            else:
                flush()
                current = _OpenBlock(
                    kind="paragraph",
                    page=page.page_number,
                    last_bottom=line.bottom,
                    last_size=line.size,
                    text=line.text,
                )

    flush()

    while image_index < len(images):
        blocks.append(_image_block(page.page_number, images[image_index]))
        image_index += 1

    return blocks


def extract_from_pdf(content: bytes) -> tuple[list[ContentBlock], int]:
    """Extrae los bloques de contenido y la cantidad de páginas de un PDF.

    Args:
        content: Contenido binario del archivo PDF.

    Returns:
        Una tupla ``(blocks, page_count)``. Los bloques están en orden de
        lectura y la cantidad de páginas es la del documento. Si no hay texto,
        se devuelve ``([], page_count)``.

    Raises:
        AppError: Si el PDF no se puede abrir porque está dañado o protegido.
    """
    try:
        with pdfplumber.open(io.BytesIO(content)) as pdf:
            page_count = len(pdf.pages)
            pages = [
                _read_page(page, page_number, page_count)
                for page_number, page in enumerate(pdf.pages, start=1)
            ]
    except (
        PdfminerException,
        MalformedPDFException,
        OSError,
        ValueError,
        UnicodeError,
    ) as exc:
        raise AppError(
            code="invalid_pdf",
            message=_INVALID_PDF_MESSAGE,
            status_code=422,
        ) from exc

    all_lines = [line for page in pages for line in page.lines]
    if not all_lines:
        return [], page_count

    body_size = _body_font_size(all_lines)
    bold_ratio = sum(line.bold for line in all_lines) / len(all_lines)
    size_levels = _heading_levels(all_lines, body_size)
    allow_bold_headings = bold_ratio < _BOLD_LINE_RATIO

    for line in all_lines:
        _classify_line(
            line,
            body_size,
            size_levels,
            allow_bold_headings,
        )

    blocks: list[ContentBlock] = []
    for page in pages:
        blocks.extend(_group_page(page, body_size))

    return blocks, page_count
