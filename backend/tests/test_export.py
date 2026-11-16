"""Tests del servicio de exportación de PDFs adaptados."""

from __future__ import annotations

import io
from collections.abc import Sequence
from typing import Any

import pdfplumber
import pytest
from pypdf import PdfReader
from reportlab.pdfgen.canvas import Canvas

from app.core.exceptions import AppError
from app.schemas.content import BBox, BlockType, ContentBlock, PageSize
from app.schemas.export import ExportEdit, ExportRequest
from app.schemas.session import TextInput
from app.services import content_service, export_service, session_service

_PAGE_WIDTH = 612.0
_PAGE_HEIGHT = 792.0


def _make_pdf(pages: Sequence[dict[str, Any]]) -> bytes:
    """Genera un PDF con texto opcional en cada página."""
    buffer = io.BytesIO()
    first = pages[0]
    canvas = Canvas(buffer, pagesize=(first["width"], first["height"]))

    for index, page in enumerate(pages):
        if index:
            canvas.showPage()
            canvas.setPageSize((page["width"], page["height"]))

        for item in page.get("texts", []):
            font = "Helvetica-Bold" if item.get("bold") else "Helvetica"
            canvas.setFont(font, item["size"])
            canvas.drawString(item["x"], item["y"], item["text"])

    canvas.showPage()
    canvas.save()
    return buffer.getvalue()


def _page(width: float = _PAGE_WIDTH, height: float = _PAGE_HEIGHT) -> dict:
    return {"width": width, "height": height, "texts": []}


def _text(
    text: str,
    *,
    x: float = 72.0,
    y: float = 300.0,
    size: float = 12.0,
    bold: bool = False,
) -> dict:
    return {"text": text, "x": x, "y": y, "size": size, "bold": bold}


def _create_session_with_content(
    pdf: bytes,
    blocks: list[ContentBlock],
    pages: list[PageSize],
    *,
    filename: str = "clase.pdf",
) -> tuple[Any, Any]:
    """Crea una sesión PDF y guarda un contenido extraído controlado."""
    session = session_service.create_from_file(filename, pdf)
    content = content_service.build_content(
        session,
        blocks,
        page_count=len(pages),
        pages=pages,
    )
    session_service.save_extracted(content)
    return session, content


def _paragraph_block(
    text: str,
    *,
    page: int = 1,
    bbox: BBox | None = None,
    font_size: float | None = 12.0,
) -> ContentBlock:
    return ContentBlock(
        type=BlockType.PARAGRAPH,
        text=text,
        page=page,
        bbox=bbox or BBox(x0=72.0, top=100.0, x1=400.0, bottom=130.0),
        font_size=font_size,
    )


def _pages(count: int) -> list[PageSize]:
    return [
        PageSize(page=index, width=_PAGE_WIDTH, height=_PAGE_HEIGHT)
        for index in range(1, count + 1)
    ]


def _pdf_with_original_text() -> bytes:
    return _make_pdf(
        [
            {
                **_page(),
                "texts": [_text("Texto original de la primera página.")],
            },
            {
                **_page(),
                "texts": [_text("Texto original de la segunda página.")],
            },
        ]
    )


def _export(
    session_id: Any,
    edits: list[ExportEdit],
) -> export_service.ExportResult:
    return export_service.export_pdf(
        session_id,
        ExportRequest(edits=edits),
    )


def test_export_keeps_page_count_and_page_sizes() -> None:
    pdf = _pdf_with_original_text()
    session, _ = _create_session_with_content(
        pdf,
        [_paragraph_block("Texto original")],
        _pages(2),
    )

    result = _export(
        session.session_id,
        [ExportEdit(block_id="b1", text="Texto adaptado.")],
    )

    original = PdfReader(io.BytesIO(pdf))
    exported = PdfReader(io.BytesIO(result.content))
    assert len(exported.pages) == len(original.pages)
    for original_page, exported_page in zip(original.pages, exported.pages):
        assert float(exported_page.mediabox.width) == pytest.approx(
            float(original_page.mediabox.width)
        )
        assert float(exported_page.mediabox.height) == pytest.approx(
            float(original_page.mediabox.height)
        )


def test_export_draws_new_text_and_white_rectangle() -> None:
    pdf = _pdf_with_original_text()
    session, _ = _create_session_with_content(
        pdf,
        [_paragraph_block("Texto original")],
        _pages(2),
    )

    result = _export(
        session.session_id,
        [ExportEdit(block_id="b1", text="Texto adaptado uno.")],
    )

    with pdfplumber.open(io.BytesIO(result.content)) as exported:
        page = exported.pages[0]
        extracted = page.extract_text() or ""
        assert "Texto adaptado uno." in extracted
        assert "Texto original de la primera página." in extracted

        assert any(
            rect["x0"] == pytest.approx(71.5, abs=0.2)
            and rect["x1"] == pytest.approx(400.5, abs=0.2)
            and rect["top"] == pytest.approx(99.5, abs=0.2)
            and rect["bottom"] == pytest.approx(130.5, abs=0.2)
            for rect in page.rects
        )


def test_export_applies_edits_on_multiple_pages() -> None:
    pdf = _pdf_with_original_text()
    blocks = [
        _paragraph_block("Primera página"),
        ContentBlock(
            type=BlockType.HEADING,
            text="Segunda página",
            level=1,
            page=2,
            bbox=BBox(x0=72.0, top=150.0, x1=400.0, bottom=180.0),
            font_size=18.0,
        ),
    ]
    session, _ = _create_session_with_content(pdf, blocks, _pages(2))

    result = _export(
        session.session_id,
        [
            ExportEdit(block_id="b1", text="Nuevo texto de la página uno."),
            ExportEdit(block_id="b2", text="Nuevo título de la página dos."),
        ],
    )

    with pdfplumber.open(io.BytesIO(result.content)) as exported:
        assert "Nuevo texto de la página uno." in (
            exported.pages[0].extract_text() or ""
        )
        assert "Nuevo título de la página dos." in (
            exported.pages[1].extract_text() or ""
        )


def test_export_uses_block_font_size_and_bold_for_heading() -> None:
    pdf = _make_pdf([_page()])
    blocks = [
        ContentBlock(
            type=BlockType.HEADING,
            text="Título original",
            level=1,
            page=1,
            bbox=BBox(x0=72.0, top=100.0, x1=400.0, bottom=140.0),
            font_size=18.0,
        )
    ]
    session, _ = _create_session_with_content(pdf, blocks, _pages(1))

    result = _export(
        session.session_id,
        [ExportEdit(block_id="b1", text="Título adaptado")],
    )

    with pdfplumber.open(io.BytesIO(result.content)) as exported:
        page = exported.pages[0]
        chars = page.crop((66.0, 95.0, 406.0, 145.0)).chars
        assert chars
        assert all(char["size"] == pytest.approx(18.0) for char in chars)
        assert all("Bold" in char["fontname"] for char in chars)


def test_export_image_caption_uses_bottom_strip() -> None:
    pdf = _make_pdf([_page()])
    blocks = [
        _paragraph_block("Texto original"),
        ContentBlock(
            type=BlockType.IMAGE,
            page=1,
            bbox=BBox(x0=72.0, top=200.0, x1=272.0, bottom=300.0),
            width=200.0,
            height=100.0,
        ),
    ]
    session, _ = _create_session_with_content(pdf, blocks, _pages(1))

    result = _export(
        session.session_id,
        [ExportEdit(block_id="b2", text="Leyenda de la imagen")],
    )

    with pdfplumber.open(io.BytesIO(result.content)) as exported:
        page = exported.pages[0]
        assert "Leyenda de la imagen" in (page.extract_text() or "")
        assert any(
            rect["top"] == pytest.approx(269.5, abs=0.2)
            and rect["bottom"] == pytest.approx(300.5, abs=0.2)
            and rect["bottom"] - rect["top"] == pytest.approx(31.0, abs=0.2)
            for rect in page.rects
        )


def test_export_shrinks_and_truncates_long_text() -> None:
    size, lines = export_service._fit_text(
        "palabra " * 100,
        "Helvetica",
        10.0,
        80.0,
        12.0,
    )

    assert size == 6.0
    assert len(lines) == 1
    assert lines[0].endswith("…")


@pytest.mark.parametrize(
    ("edits", "code"),
    [
        (
            [ExportEdit(block_id="b999", text="Texto")],
            "unknown_block",
        ),
        (
            [
                ExportEdit(block_id="b1", text="Texto uno"),
                ExportEdit(block_id="b1", text="Texto dos"),
            ],
            "duplicate_block_id",
        ),
        (
            [ExportEdit(block_id="b1", text="   ")],
            "empty_text",
        ),
        (
            [ExportEdit(block_id="b1", text="a" * 8001)],
            "text_too_long",
        ),
    ],
)
def test_export_edit_validation_errors(
    edits: list[ExportEdit],
    code: str,
) -> None:
    pdf = _pdf_with_original_text()
    session, _ = _create_session_with_content(
        pdf,
        [_paragraph_block("Texto original")],
        _pages(2),
    )

    with pytest.raises(AppError) as error:
        _export(session.session_id, edits)

    assert error.value.code == code
    assert error.value.status_code == 422


def test_export_block_without_bbox() -> None:
    pdf = _pdf_with_original_text()
    session, _ = _create_session_with_content(
        pdf,
        [
            ContentBlock(
                type=BlockType.PARAGRAPH,
                text="Texto original",
                page=1,
                font_size=12.0,
            )
        ],
        _pages(2),
    )

    with pytest.raises(AppError) as error:
        _export(
            session.session_id,
            [ExportEdit(block_id="b1", text="Texto adaptado")],
        )

    assert error.value.code == "block_without_bbox"


def test_export_with_invalid_pdf() -> None:
    session = session_service.create_from_file(
        "roto.pdf",
        b"%PDF-1.4\nContenido roto sin objetos validos\n%%EOF\n",
    )
    content = content_service.build_content(
        session,
        [_paragraph_block("Texto original")],
        page_count=1,
        pages=_pages(1),
    )
    session_service.save_extracted(content)

    with pytest.raises(AppError) as error:
        _export(
            session.session_id,
            [ExportEdit(block_id="b1", text="Texto adaptado")],
        )

    assert error.value.code == "invalid_pdf"
    assert error.value.status_code == 422


def test_export_unavailable_for_text_session() -> None:
    session = session_service.create_from_text(
        TextInput(title="Biología", text="# Tema\n\nUn texto.")
    )
    content_service.extract(session.session_id)

    with pytest.raises(AppError) as error:
        _export(
            session.session_id,
            [ExportEdit(block_id="b1", text="Texto adaptado")],
        )

    assert error.value.code == "export_unavailable"
    assert error.value.status_code == 409


def test_export_requires_extracted_content() -> None:
    session = session_service.create_from_file(
        "clase.pdf",
        _pdf_with_original_text(),
    )

    with pytest.raises(AppError) as error:
        _export(
            session.session_id,
            [ExportEdit(block_id="b1", text="Texto adaptado")],
        )

    assert error.value.code == "content_not_extracted"
    assert error.value.status_code == 409


def test_content_disposition_sanitizes_and_encodes_filename() -> None:
    stem = export_service._sanitize_filename_stem("../Biología 2º.pdf")

    header = export_service._content_disposition(stem)

    assert 'filename="documento-adaptado.pdf"' in header
    assert "filename*=UTF-8''Biolog%C3%ADa%202%C2%BA_adaptado.pdf" in header
    assert header.startswith("attachment;")
