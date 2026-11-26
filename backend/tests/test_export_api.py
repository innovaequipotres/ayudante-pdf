"""Tests del endpoint de exportación de PDFs adaptados."""

from __future__ import annotations

import io
from collections.abc import Sequence
from typing import Any
from uuid import UUID, uuid4

import pdfplumber
import pytest
from fastapi.testclient import TestClient
from pypdf import PdfReader
from reportlab.pdfgen.canvas import Canvas

from app.schemas.content import BBox, BlockType, ContentBlock, PageSize
from app.services import content_service, session_service

API_PREFIX = "/api/v1/sessions"

_WIDTH = 612.0
_HEIGHT = 792.0


def _make_pdf(pages: Sequence[list[str]]) -> bytes:
    """Genera un PDF de varias páginas con una línea de texto en cada una."""
    buffer = io.BytesIO()
    canvas = Canvas(buffer, pagesize=(_WIDTH, _HEIGHT))
    for index, lines in enumerate(pages):
        if index:
            canvas.showPage()
            canvas.setPageSize((_WIDTH, _HEIGHT))
        canvas.setFont("Helvetica", 12)
        for line_index, line in enumerate(lines):
            canvas.drawString(72, 700 - line_index * 18, line)
    canvas.showPage()
    canvas.save()
    return buffer.getvalue()


def _create_pdf_session(
    client: TestClient,
    pdf: bytes,
    filename: str = "clase.pdf",
) -> dict[str, Any]:
    response = client.post(
        f"{API_PREFIX}/file",
        files={"file": (filename, pdf, "application/pdf")},
    )
    assert response.status_code == 201
    return response.json()


def _extract(client: TestClient, session_id: str) -> dict[str, Any]:
    response = client.post(f"{API_PREFIX}/{session_id}/extract")
    assert response.status_code == 200
    return response.json()


def _block_with_bbox(content: dict[str, Any], page: int) -> dict[str, Any]:
    return next(
        block
        for block in content["blocks"]
        if block["page"] == page and block["bbox"] is not None
    )


def _save_custom_content(
    session_id: str,
    blocks: list[ContentBlock],
    pages: list[PageSize],
) -> None:
    from sqlalchemy import create_engine
    from sqlalchemy.orm import Session

    from app.core.config import settings

    engine = create_engine(settings.test_database_url, pool_pre_ping=True)
    with Session(engine) as db:
        session = session_service.get_session(db, UUID(session_id))
        content = content_service.build_content(
            session,
            blocks,
            page_count=len(pages),
            pages=pages,
        )
        session_service.save_extracted(content, db=db)
        db.commit()
    engine.dispose()


def _export(
    client: TestClient,
    session_id: str,
    edits: list[dict[str, str]],
):
    return client.post(
        f"{API_PREFIX}/{session_id}/export",
        json={"edits": edits},
    )


def test_export_returns_pdf_with_same_pages_and_sizes(
    client: TestClient,
) -> None:
    pdf = _make_pdf(
        [
            ["La celula es la unidad basica de la vida."],
            ["El nucleo contiene el material genetico."],
        ]
    )
    session = _create_pdf_session(client, pdf, filename="Biologia.pdf")
    content = _extract(client, session["session_id"])
    block = _block_with_bbox(content, page=1)
    new_text = "ZZZZ ZZZZ ZZZZ"

    response = _export(
        client,
        session["session_id"],
        [{"block_id": block["id"], "text": new_text}],
    )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/pdf")
    assert response.headers["content-disposition"] == (
        'attachment; filename="documento-adaptado.pdf"; '
        "filename*=UTF-8''Biologia_adaptado.pdf"
    )

    original = PdfReader(io.BytesIO(pdf))
    exported = PdfReader(io.BytesIO(response.content))
    assert len(exported.pages) == len(original.pages)
    for original_page, exported_page in zip(original.pages, exported.pages):
        assert float(exported_page.mediabox.width) == pytest.approx(
            float(original_page.mediabox.width)
        )
        assert float(exported_page.mediabox.height) == pytest.approx(
            float(original_page.mediabox.height)
        )

    with pdfplumber.open(io.BytesIO(response.content)) as exported_pdf:
        # El texto original sigue debajo y pdfplumber intercala ambas capas.
        # Los caracteres irrepetibles confirman que el texto nuevo se dibujó.
        assert (exported_pdf.pages[0].extract_text() or "").count("Z") == 12


def test_export_preserves_paragraphs(client: TestClient) -> None:
    pdf = _make_pdf([["Texto original"]])
    session = _create_pdf_session(client, pdf)
    _save_custom_content(
        session["session_id"],
        [
            ContentBlock(
                type=BlockType.PARAGRAPH,
                text="Texto original",
                page=1,
                bbox=BBox(x0=72.0, top=100.0, x1=400.0, bottom=190.0),
                font_size=12.0,
            )
        ],
        [PageSize(page=1, width=_WIDTH, height=_HEIGHT)],
    )

    response = _export(
        client,
        session["session_id"],
        [
            {
                "block_id": "b1",
                "text": "Primer párrafo.\n\nSegundo párrafo.",
            }
        ],
    )

    assert response.status_code == 200
    with pdfplumber.open(io.BytesIO(response.content)) as exported:
        extracted = exported.pages[0].extract_text() or ""
        assert "Primer párrafo." in extracted
        assert "Segundo párrafo." in extracted
        assert "Primer párrafo. Segundo párrafo." not in extracted


def test_export_applies_all_edits_in_one_call(client: TestClient) -> None:
    pdf = _make_pdf(
        [
            ["Primera pagina con contenido suficiente."],
            ["Segunda pagina con contenido suficiente."],
        ]
    )
    session = _create_pdf_session(client, pdf)
    _save_custom_content(
        session["session_id"],
        [
            ContentBlock(
                type=BlockType.PARAGRAPH,
                text="Contenido original de la pagina uno.",
                page=1,
                bbox=BBox(x0=72.0, top=100.0, x1=400.0, bottom=130.0),
                font_size=12.0,
            ),
            ContentBlock(
                type=BlockType.PARAGRAPH,
                text="Contenido original de la pagina dos.",
                page=2,
                bbox=BBox(x0=72.0, top=100.0, x1=400.0, bottom=130.0),
                font_size=12.0,
            ),
        ],
        [
            PageSize(page=1, width=_WIDTH, height=_HEIGHT),
            PageSize(page=2, width=_WIDTH, height=_HEIGHT),
        ],
    )

    response = _export(
        client,
        session["session_id"],
        [
            {"block_id": "b1", "text": "Texto nuevo de la pagina uno."},
            {"block_id": "b2", "text": "Texto nuevo de la pagina dos."},
        ],
    )

    assert response.status_code == 200
    with pdfplumber.open(io.BytesIO(response.content)) as exported:
        assert "Texto nuevo de la pagina uno." in (
            exported.pages[0].extract_text() or ""
        )
        assert "Texto nuevo de la pagina dos." in (
            exported.pages[1].extract_text() or ""
        )


def test_export_does_not_change_session_state_or_content(
    client: TestClient,
) -> None:
    pdf = _make_pdf([["Contenido original para exportar."]])
    session = _create_pdf_session(client, pdf)
    content = _extract(client, session["session_id"])
    block = _block_with_bbox(content, page=1)
    before_session = client.get(f"{API_PREFIX}/{session['session_id']}").json()
    before_content = client.get(
        f"{API_PREFIX}/{session['session_id']}/content"
    ).json()

    response = _export(
        client,
        session["session_id"],
        [{"block_id": block["id"], "text": "Texto adaptado."}],
    )

    assert response.status_code == 200
    after_session = client.get(f"{API_PREFIX}/{session['session_id']}").json()
    after_content = client.get(
        f"{API_PREFIX}/{session['session_id']}/content"
    ).json()
    assert after_session == before_session
    assert after_content == before_content


def test_export_encodes_utf8_filename(client: TestClient) -> None:
    pdf = _make_pdf([["Contenido para el nombre del archivo."]])
    session = _create_pdf_session(client, pdf, filename="Biología 2º.pdf")
    content = _extract(client, session["session_id"])
    block = _block_with_bbox(content, page=1)

    response = _export(
        client,
        session["session_id"],
        [{"block_id": block["id"], "text": "Texto adaptado."}],
    )

    assert response.status_code == 200
    assert response.headers["content-disposition"] == (
        'attachment; filename="documento-adaptado.pdf"; '
        "filename*=UTF-8''Biolog%C3%ADa%202%C2%BA_adaptado.pdf"
    )


@pytest.mark.parametrize(
    ("edits", "code"),
    [
        ([{"block_id": "b999", "text": "Texto"}], "unknown_block"),
        (
            [
                {"block_id": "b1", "text": "Texto uno"},
                {"block_id": "b1", "text": "Texto dos"},
            ],
            "duplicate_block_id",
        ),
        ([{"block_id": "b1", "text": "   "}], "empty_text"),
        ([{"block_id": "b1", "text": "a" * 8001}], "text_too_long"),
    ],
)
def test_export_validation_errors(
    client: TestClient,
    edits: list[dict[str, str]],
    code: str,
) -> None:
    pdf = _make_pdf([["Contenido original para validar."]])
    session = _create_pdf_session(client, pdf)
    _extract(client, session["session_id"])

    response = _export(client, session["session_id"], edits)

    assert response.status_code == 422
    assert response.json()["code"] == code


def test_export_block_without_bbox(client: TestClient) -> None:
    pdf = _make_pdf([["Contenido original."]])
    session = _create_pdf_session(client, pdf)
    _save_custom_content(
        session["session_id"],
        [
            ContentBlock(
                type=BlockType.PARAGRAPH,
                text="Texto original sin coordenadas",
                page=1,
            )
        ],
        [PageSize(page=1, width=_WIDTH, height=_HEIGHT)],
    )

    response = _export(
        client,
        session["session_id"],
        [{"block_id": "b1", "text": "Texto adaptado"}],
    )

    assert response.status_code == 422
    assert response.json()["code"] == "block_without_bbox"


def test_export_requires_extracted_content(client: TestClient) -> None:
    pdf = _make_pdf([["Contenido sin extraer."]])
    session = _create_pdf_session(client, pdf)

    response = _export(
        client,
        session["session_id"],
        [{"block_id": "b1", "text": "Texto adaptado"}],
    )

    assert response.status_code == 409
    assert response.json()["code"] == "content_not_extracted"


def test_export_unavailable_for_text_session(client: TestClient) -> None:
    response = client.post(
        f"{API_PREFIX}/text",
        json={"title": "Biología", "text": "# Tema\n\nUn texto."},
    )
    session_id = response.json()["session_id"]
    _extract(client, session_id)

    export_response = _export(
        client,
        session_id,
        [{"block_id": "b1", "text": "Texto adaptado"}],
    )

    assert export_response.status_code == 409
    assert export_response.json()["code"] == "export_unavailable"


def test_export_unknown_session(client: TestClient) -> None:
    response = _export(
        client,
        str(uuid4()),
        [{"block_id": "b1", "text": "Texto adaptado"}],
    )

    assert response.status_code == 404
    assert response.json()["code"] == "session_not_found"


def test_export_invalid_pdf(client: TestClient) -> None:
    pdf = b"%PDF-1.4\nContenido roto sin objetos validos\n%%EOF\n"
    session = _create_pdf_session(client, pdf)
    _save_custom_content(
        session["session_id"],
        [
            ContentBlock(
                type=BlockType.PARAGRAPH,
                text="Texto original",
                page=1,
                bbox=BBox(x0=72.0, top=100.0, x1=400.0, bottom=130.0),
            )
        ],
        [PageSize(page=1, width=_WIDTH, height=_HEIGHT)],
    )

    response = _export(
        client,
        session["session_id"],
        [{"block_id": "b1", "text": "Texto adaptado"}],
    )

    assert response.status_code == 422
    assert response.json()["code"] == "invalid_pdf"


def test_openapi_includes_export_contract(client: TestClient) -> None:
    schema = client.get("/openapi.json").json()

    assert f"{API_PREFIX}/{{session_id}}/export" in schema["paths"]
    components = schema["components"]["schemas"]
    assert "ExportRequest" in components
    assert "ExportEdit" in components
    assert "font_size" in components["ContentBlock"]["properties"]
