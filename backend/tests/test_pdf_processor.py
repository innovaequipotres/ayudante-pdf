"""Tests del procesador de PDFs."""

from __future__ import annotations

from typing import Any

import pytest
from pdfplumber.utils.exceptions import PdfminerException
from pydantic import ValidationError

from app.core.exceptions import AppError
from app.processors import pdf_processor
from app.processors.pdf_processor import BULLET_RE, extract_from_pdf
from app.schemas.content import BlockType, ContentBlock


class _FakePage:
    """Página mínima compatible con lo que usa el procesador."""

    def __init__(
        self,
        lines: list[dict[str, Any]],
        images: list[dict[str, Any]] | None = None,
    ) -> None:
        self._lines = lines
        self.images = images or []

    def extract_text_lines(self) -> list[dict[str, Any]]:
        return self._lines


class _FakePdf:
    """PDF mínimo que se usa como context manager."""

    def __init__(self, pages: list[_FakePage]) -> None:
        self.pages = pages

    def __enter__(self) -> _FakePdf:
        return self

    def __exit__(self, *args: object) -> bool:
        return False


def _line(
    text: str,
    *,
    top: float,
    size: float = 12,
    bold: bool = False,
    x0: float = 72.0,
) -> dict[str, Any]:
    """Construye una línea con los campos que devuelve pdfplumber."""
    fontname = "Helvetica-Bold" if bold else "Helvetica"
    chars = [{"fontname": fontname, "size": size} for _ in text]
    return {
        "text": text,
        "x0": x0,
        "top": top,
        "bottom": top + size,
        "chars": chars,
    }


@pytest.fixture
def install_fake_pdf(monkeypatch: pytest.MonkeyPatch):
    """Reemplaza pdfplumber.open por un PDF construido en el test."""

    def install(pages: list[_FakePage]) -> None:
        monkeypatch.setattr(
            pdf_processor.pdfplumber,
            "open",
            lambda *args, **kwargs: _FakePdf(pages),
        )

    return install


def test_extract_from_pdf_detects_all_block_types(
    install_fake_pdf,
) -> None:
    page_one = _FakePage(
        lines=[
            _line("1", top=20, size=9),
            _line("Guía de accesibilidad", top=60, size=24, bold=True),
            _line(
                "Este es un párrafo de prueba que continúa",
                top=100,
            ),
            _line("en la segunda línea.", top=114),
            _line("Sección", top=140, size=18, bold=True),
            _line("• Uno", top=170),
            _line("• Dos", top=184),
            _line("continuación", top=198, x0=90),
            _line("Texto final.", top=260),
        ],
        images=[
            {"top": 220, "x0": 72, "width": 100.04, "height": 50.06},
            # Un ícono pequeño no debe generar bloque.
            {"top": 230, "x0": 72, "width": 10, "height": 10},
        ],
    )
    page_two = _FakePage(
        lines=[
            _line("2", top=20, size=9),
            _line("Otra sección", top=60, size=18, bold=True),
            _line("Actividad", top=100, bold=True),
            _line("Página dos.", top=120),
            _line("Texto de cierre", top=134),
        ],
    )
    install_fake_pdf([page_one, page_two])

    blocks, page_count = extract_from_pdf(b"ignored")

    assert page_count == 2
    assert [block.type for block in blocks] == [
        BlockType.HEADING,
        BlockType.PARAGRAPH,
        BlockType.HEADING,
        BlockType.LIST,
        BlockType.IMAGE,
        BlockType.PARAGRAPH,
        BlockType.HEADING,
        BlockType.HEADING,
        BlockType.PARAGRAPH,
    ]

    (
        heading_one,
        paragraph_one,
        heading_two,
        list_block,
        image_block,
        paragraph_two,
        heading_three,
        heading_four,
        paragraph_three,
    ) = blocks

    assert heading_one.text == "Guía de accesibilidad"
    assert heading_one.level == 1
    assert heading_one.page == 1
    assert heading_one.id == ""
    assert heading_one.word_count == 0
    assert heading_one.items is None

    assert paragraph_one.text == (
        "Este es un párrafo de prueba que continúa en la segunda línea."
    )
    assert paragraph_one.page == 1

    assert heading_two.text == "Sección"
    assert heading_two.level == 2

    assert list_block.items == ["Uno", "Dos continuación"]
    assert list_block.page == 1

    assert image_block.page == 1
    assert image_block.width == 100.0
    assert image_block.height == 50.1
    assert image_block.text is None
    assert image_block.alt_text is None

    assert paragraph_two.text == "Texto final."
    assert paragraph_two.page == 1

    assert heading_three.text == "Otra sección"
    assert heading_three.level == 2
    assert heading_three.page == 2

    assert heading_four.text == "Actividad"
    assert heading_four.level == 3
    assert heading_four.page == 2

    assert paragraph_three.text == "Página dos. Texto de cierre"
    assert paragraph_three.page == 2

    assert all(
        block.text not in {"1", "2"} for block in blocks if block.text is not None
    )


def test_merges_consecutive_headings_of_same_level(
    install_fake_pdf,
) -> None:
    install_fake_pdf(
        [
            _FakePage(
                lines=[
                    _line("Título", top=60, size=24, bold=True),
                    _line("partido", top=90, size=24, bold=True),
                    _line(
                        "Cuerpo del documento con varias palabras",
                        top=130,
                    ),
                    _line("otra línea de cuerpo", top=144),
                    _line(
                        "más texto para que domine el tamaño doce",
                        top=158,
                    ),
                ]
            )
        ]
    )

    blocks, _ = extract_from_pdf(b"ignored")

    headings = [block for block in blocks if block.type == BlockType.HEADING]
    assert len(headings) == 1
    assert headings[0].text == "Título partido"
    assert headings[0].level == 1


def test_paragraphs_do_not_merge_across_pages(install_fake_pdf) -> None:
    install_fake_pdf(
        [
            _FakePage([_line("Primera parte", top=700)]),
            _FakePage([_line("Segunda parte", top=20)]),
        ]
    )

    blocks, _ = extract_from_pdf(b"ignored")

    paragraphs = [block for block in blocks if block.type == BlockType.PARAGRAPH]
    assert [paragraph.text for paragraph in paragraphs] == [
        "Primera parte",
        "Segunda parte",
    ]


@pytest.mark.parametrize(
    "text",
    [
        "• Uno",
        "● Dos",
        "▪ Tres",
        "◦ Cuatro",
        "· Cinco",
        "* Seis",
        "- Siete",
        "– Ocho",
        "— Nueve",
        "1. Diez",
        "2) Once",
        "a. Doce",
        "b) Trece",
        "(cid:127) Catorce",
        "  • Quince",
    ],
)
def test_bullet_re_matches_list_markers(text: str) -> None:
    assert BULLET_RE.match(text) is not None


@pytest.mark.parametrize(
    "text",
    [
        "Texto normal",
        "3.14 es pi",
        "A. Mayúscula",
        "1.Introducción",
        "2024.",
        "a.b",
    ],
)
def test_bullet_re_does_not_match_regular_text(text: str) -> None:
    assert BULLET_RE.match(text) is None


@pytest.mark.parametrize(
    "text",
    ["1", "Página 1", "Pág. 1", "1/1", "1 de 1"],
)
def test_page_number_lines_are_removed(
    install_fake_pdf,
    text: str,
) -> None:
    install_fake_pdf([_FakePage([_line(text, top=20, size=9)])])

    blocks, page_count = extract_from_pdf(b"ignored")

    assert blocks == []
    assert page_count == 1


def test_standalone_number_from_another_page_is_kept(
    install_fake_pdf,
) -> None:
    install_fake_pdf(
        [
            _FakePage(
                [
                    _line("2", top=20, size=9),
                    _line("Texto", top=40),
                ]
            )
        ]
    )

    blocks, _ = extract_from_pdf(b"ignored")

    assert any(
        block.type == BlockType.PARAGRAPH and block.text == "2" for block in blocks
    )


def test_pdf_without_text_returns_empty_list(install_fake_pdf) -> None:
    install_fake_pdf(
        [
            _FakePage(
                lines=[],
                images=[{"top": 100, "x0": 72, "width": 200, "height": 200}],
            )
        ]
    )

    blocks, page_count = extract_from_pdf(b"ignored")

    assert blocks == []
    assert page_count == 1


@pytest.mark.parametrize(
    "content",
    [
        b"",
        b"not a pdf",
        b"%PDF-1.4\ncontenido truncado",
    ],
)
def test_invalid_pdf_raises_app_error(content: bytes) -> None:
    with pytest.raises(AppError) as error:
        extract_from_pdf(content)

    assert error.value.code == "invalid_pdf"
    assert error.value.status_code == 422
    assert error.value.message == (
        "No se pudo leer el PDF. Puede estar dañado o protegido."
    )


def test_pdf_open_failure_is_mapped_to_invalid_pdf(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail_open(*args: Any, **kwargs: Any) -> None:
        raise PdfminerException("se requiere contraseña")

    monkeypatch.setattr(pdf_processor.pdfplumber, "open", fail_open)

    with pytest.raises(AppError) as error:
        extract_from_pdf(b"ignored")

    assert error.value.code == "invalid_pdf"
    assert error.value.status_code == 422


def test_content_block_defaults() -> None:
    block = ContentBlock(
        type=BlockType.HEADING,
        text="Título",
        level=1,
    )

    assert block.id == ""
    assert block.page is None
    assert block.word_count == 0
    assert block.items is None
    assert block.alt_text is None
    assert block.width is None
    assert block.height is None


@pytest.mark.parametrize("level", [0, 7])
def test_content_block_rejects_invalid_level(level: int) -> None:
    with pytest.raises(ValidationError):
        ContentBlock(type=BlockType.HEADING, level=level)


def test_content_block_rejects_invalid_page() -> None:
    with pytest.raises(ValidationError):
        ContentBlock(type=BlockType.PARAGRAPH, page=0)
