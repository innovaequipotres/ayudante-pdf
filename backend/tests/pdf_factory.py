"""Generadores de PDFs de prueba con ``reportlab``.

Los archivos se construyen en memoria para no versionar binarios. Cada PDF
apunta a un escenario distinto del procesador, de las reglas o de los endpoints.
"""

from __future__ import annotations

import base64
from io import BytesIO
from typing import Literal

from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfgen import canvas

PageWidth, PageHeight = A4
_MARGIN_X = 72.0
_MARGIN_TOP = 72.0
_MARGIN_BOTTOM = 72.0
_BODY_SIZE = 12.0
_BODY_LEADING = 14.0
_HEADING_SIZES = {1: 24.0, 2: 18.0, 3: 15.0}
_MAX_WIDTH = PageWidth - 2 * _MARGIN_X

# PNG transparente de 1x1 píxel: se escala al dibujarlo. Evita depender de
# archivos binarios y alcanza para que pdfplumber lo detecte como imagen.
_TINY_PNG = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk"
    "+A8AAQUBAScY42YAAAAASUVORK5CYII="
)

Block = tuple[str, object]


class _Builder:
    """Dibuja bloques simples sobre un canvas y maneja los saltos de página."""

    def __init__(self) -> None:
        self._buffer = BytesIO()
        self._canvas = canvas.Canvas(self._buffer, pagesize=A4)
        self._y = PageHeight - _MARGIN_TOP
        self._page_open = False

    def _ensure_page(self) -> None:
        if not self._page_open:
            self._canvas.setFont("Helvetica", _BODY_SIZE)
            self._page_open = True

    def _new_page(self) -> None:
        self._ensure_page()
        self._canvas.showPage()
        self._y = PageHeight - _MARGIN_TOP
        self._page_open = False

    def _fit(self, needed: float) -> None:
        if self._y - needed < _MARGIN_BOTTOM:
            self._new_page()
        self._ensure_page()

    def heading(self, level: int, text: str) -> None:
        size = _HEADING_SIZES.get(level, _HEADING_SIZES[3])
        self._fit(size + 18)
        self._canvas.setFont("Helvetica-Bold", size)
        self._canvas.drawString(_MARGIN_X, self._y, text)
        self._y -= size + 14

    def paragraph(self, text: str) -> None:
        self._canvas.setFont("Helvetica", _BODY_SIZE)
        for line in self._wrap(text):
            self._fit(_BODY_LEADING)
            self._canvas.drawString(_MARGIN_X, self._y, line)
            self._y -= _BODY_LEADING
        self._y -= 8

    def bullet_list(self, items: list[str]) -> None:
        self._canvas.setFont("Helvetica", _BODY_SIZE)
        for item in items:
            fields = self._wrap(f"- {item}", first_indent=0.0)
            for index, line in enumerate(fields):
                x = _MARGIN_X + (12.0 if index else 0.0)
                self._fit(_BODY_LEADING)
                self._canvas.drawString(x, self._y, line)
                self._y -= _BODY_LEADING
        self._y -= 8

    def image(self, width: float = 120.0, height: float = 80.0) -> None:
        self._fit(height + 16)
        self._canvas.drawImage(
            ImageReader(BytesIO(_TINY_PNG)),
            _MARGIN_X,
            self._y - height,
            width=width,
            height=height,
            preserveAspectRatio=False,
            mask="auto",
        )
        self._y -= height + 16

    def page_break(self) -> None:
        self._new_page()

    def finish(self) -> bytes:
        self._ensure_page()
        self._canvas.save()
        return self._buffer.getvalue()

    @staticmethod
    def _wrap(text: str, first_indent: float = 0.0) -> list[str]:
        words = text.split()
        if not words:
            return []
        lines: list[str] = []
        current = ""
        available = _MAX_WIDTH - first_indent
        for word in words:
            candidate = f"{current} {word}".strip()
            if current and stringWidth(candidate, "Helvetica", _BODY_SIZE) > available:
                lines.append(current)
                current = word
                available = _MAX_WIDTH
            else:
                current = candidate
        if current:
            lines.append(current)
        return lines


def _render(blocks: list[Block]) -> bytes:
    builder = _Builder()
    for kind, value in blocks:
        if kind == "heading":
            level, text = value  # type: ignore[misc]
            builder.heading(level, text)
        elif kind == "paragraph":
            builder.paragraph(value)  # type: ignore[arg-type]
        elif kind == "list":
            builder.bullet_list(value)  # type: ignore[arg-type]
        elif kind == "image":
            builder.image()
        elif kind == "page_break":
            builder.page_break()
        else:  # pragma: no cover - error de programación en un fixture
            raise ValueError(f"Bloque de PDF desconocido: {kind}")
    return builder.finish()


def make_clean_pdf() -> bytes:
    """PDF sin problemas: títulos, párrafos breves y una lista."""
    return _render(
        [
            ("heading", (1, "Guía de estudio: la célula")),
            (
                "paragraph",
                "La célula es la unidad básica de la vida. "
                "Todas las células tienen membrana y material genético.",
            ),
            ("heading", (2, "Partes de la célula")),
            ("list", ["Membrana", "Citoplasma", "Núcleo"]),
            (
                "paragraph",
                "Cada parte cumple una función importante. "
                "Repasar la lista ayuda a recordar el vocabulario.",
            ),
        ]
    )


def make_problem_pdf() -> bytes:
    """PDF con problemas: sin títulos, párrafo y oración demasiado extensos."""
    long_sentence = " ".join(["La célula realiza funciones vitales"] * 12) + "."
    rest = " ".join(
        ["El material repite ideas sin pausas ni títulos que organicen la lectura."] * 28
    )
    return _render(
        [
            ("paragraph", f"{long_sentence} {rest}"),
        ]
    )


def make_blank_pdf() -> bytes:
    """PDF válido pero sin capa de texto extraíble."""
    return _render([])


def make_multipage_pdf() -> bytes:
    """PDF de varias páginas con un título y un párrafo por página."""
    blocks: list[Block] = []
    for number in range(1, 4):
        blocks.extend(
            [
                ("heading", (1, f"Unidad {number}")),
                (
                    "paragraph",
                    f"Esta es la página {number} del material. "
                    "El texto es breve y está organizado con un título.",
                ),
            ]
        )
        if number < 3:
            blocks.append(("page_break", None))
    return _render(blocks)


def make_image_pdf() -> bytes:
    """PDF con una imagen relevante sin texto alternativo."""
    return _render(
        [
            ("heading", (1, "Gráfico del experimento")),
            ("image", None),
            (
                "paragraph",
                "El gráfico muestra los resultados del experimento. "
                "Conviene revisar si la imagen tiene una descripción.",
            ),
        ]
    )


def make_problem_pdf_with_image() -> bytes:
    """PDF con problemas de texto y una imagen sin descripción."""
    long_sentence = " ".join(["La experiencia se repite sin una explicación clara"] * 10)
    return _render(
        [
            ("paragraph", f"{long_sentence}. " + long_sentence + "."),
            ("image", None),
            (
                "paragraph",
                "La imagen anterior no tiene texto alternativo. " * 8,
            ),
        ]
    )


def make_malformed_pdf() -> bytes:
    """Archivo con firma PDF pero contenido que pdfplumber no puede abrir."""
    return b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n"


PDFFactory = Literal[
    "clean",
    "problem",
    "blank",
    "multipage",
    "image",
    "problem_with_image",
    "malformed",
]

_FACTORIES = {
    "clean": make_clean_pdf,
    "problem": make_problem_pdf,
    "blank": make_blank_pdf,
    "multipage": make_multipage_pdf,
    "image": make_image_pdf,
    "problem_with_image": make_problem_pdf_with_image,
    "malformed": make_malformed_pdf,
}


def build_pdf(name: PDFFactory) -> bytes:
    """Devuelve el PDF de prueba pedido por nombre."""
    return _FACTORIES[name]()
