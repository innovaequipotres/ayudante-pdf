"""Tests de la extracción de contenido y de sus endpoints."""

from __future__ import annotations

from uuid import uuid4

from fastapi.testclient import TestClient

from app.schemas.content import BlockType, ContentBlock
from app.services import content_service

API_PREFIX = "/api/v1/sessions"

_TEXT = (
    "# Tema\n"
    "\n"
    "La célula es la unidad básica de la vida.\n"
    "\n"
    "- Membrana\n"
    "- Citoplasma\n"
    "\n"
    "Texto suelto."
)


def _create_text_session(client: TestClient, title: str | None = "Biología") -> dict:
    payload: dict[str, str] = {"text": _TEXT}
    if title is not None:
        payload["title"] = title
    response = client.post(f"{API_PREFIX}/text", json=payload)
    assert response.status_code == 201
    return response.json()


def _create_pdf_session(client: TestClient, pdf_content: bytes) -> dict:
    response = client.post(
        f"{API_PREFIX}/file",
        files={"file": ("clase.pdf", pdf_content, "application/pdf")},
    )
    assert response.status_code == 201
    return response.json()


def test_extract_text_returns_blocks_and_summary(client: TestClient) -> None:
    session = _create_text_session(client)

    response = client.post(f"{API_PREFIX}/{session['session_id']}/extract")

    assert response.status_code == 200
    body = response.json()
    assert body["session_id"] == session["session_id"]
    assert body["source_type"] == "text"
    assert body["title"] == "Biología"
    assert body["page_count"] is None
    assert [block["id"] for block in body["blocks"]] == ["b1", "b2", "b3", "b4"]
    assert [block["type"] for block in body["blocks"]] == [
        "heading",
        "paragraph",
        "list",
        "paragraph",
    ]
    assert [block["word_count"] for block in body["blocks"]] == [1, 9, 2, 2]
    assert body["blocks"][0]["level"] == 1
    assert body["blocks"][2]["items"] == ["Membrana", "Citoplasma"]
    assert all(block["page"] is None for block in body["blocks"])
    assert body["summary"] == {
        "word_count": 14,
        "heading_count": 1,
        "paragraph_count": 2,
        "list_count": 1,
        "image_count": 0,
        "images_without_alt": 0,
    }

    stored = client.get(f"{API_PREFIX}/{session['session_id']}").json()
    assert stored["status"] == "extracted"


def test_get_content_returns_same_result(client: TestClient) -> None:
    session = _create_text_session(client)

    extracted = client.post(f"{API_PREFIX}/{session['session_id']}/extract").json()
    response = client.get(f"{API_PREFIX}/{session['session_id']}/content")

    assert response.status_code == 200
    assert response.json() == extracted


def test_get_content_before_extract_returns_conflict(client: TestClient) -> None:
    session = _create_text_session(client)

    response = client.get(f"{API_PREFIX}/{session['session_id']}/content")

    assert response.status_code == 409
    assert response.json() == {
        "code": "content_not_extracted",
        "message": "El contenido todavía no fue extraído.",
    }


def test_unknown_session_returns_not_found(client: TestClient) -> None:
    session_id = uuid4()

    extract_response = client.post(f"{API_PREFIX}/{session_id}/extract")
    content_response = client.get(f"{API_PREFIX}/{session_id}/content")

    for response in (extract_response, content_response):
        assert response.status_code == 404
        assert response.json() == {
            "code": "session_not_found",
            "message": "La sesión solicitada no existe.",
        }


def test_second_extract_does_not_reprocess(
    client: TestClient,
    monkeypatch,
) -> None:
    session = _create_text_session(client)
    first = client.post(f"{API_PREFIX}/{session['session_id']}/extract").json()

    def fail_if_called(text: str) -> list[ContentBlock]:
        raise AssertionError("El texto no debería volver a procesarse")

    monkeypatch.setattr(content_service, "extract_from_text", fail_if_called)

    second = client.post(f"{API_PREFIX}/{session['session_id']}/extract")

    assert second.status_code == 200
    assert second.json() == first


def test_text_without_title_has_no_content_title(client: TestClient) -> None:
    session = _create_text_session(client, title=None)

    body = client.post(f"{API_PREFIX}/{session['session_id']}/extract").json()

    assert body["title"] is None


def test_pdf_without_text_returns_unprocessable(
    client: TestClient,
    pdf_content: bytes,
    monkeypatch,
) -> None:
    session = _create_pdf_session(client, pdf_content)
    monkeypatch.setattr(
        content_service,
        "extract_from_pdf",
        lambda content: ([], 1),
    )

    response = client.post(f"{API_PREFIX}/{session['session_id']}/extract")

    assert response.status_code == 422
    assert response.json() == {
        "code": "no_extractable_text",
        "message": (
            "No se encontró texto en el material. "
            "Si es un PDF escaneado, no se puede leer por ahora."
        ),
    }

    stored = client.get(f"{API_PREFIX}/{session['session_id']}").json()
    assert stored["status"] == "uploaded"


def test_pdf_content_counts_images_without_alt(
    client: TestClient,
    pdf_content: bytes,
    monkeypatch,
) -> None:
    session = _create_pdf_session(client, pdf_content)
    blocks = [
        ContentBlock(type=BlockType.HEADING, text="Sección", level=2, page=1),
        ContentBlock(
            type=BlockType.HEADING,
            text="Título principal",
            level=1,
            page=1,
        ),
        ContentBlock(type=BlockType.IMAGE, page=2, width=100, height=50),
    ]
    monkeypatch.setattr(
        content_service,
        "extract_from_pdf",
        lambda content: (blocks, 3),
    )

    response = client.post(f"{API_PREFIX}/{session['session_id']}/extract")

    assert response.status_code == 200
    body = response.json()
    assert body["title"] == "Título principal"
    assert body["page_count"] == 3
    assert [block["id"] for block in body["blocks"]] == ["b1", "b2", "b3"]
    assert body["blocks"][2]["word_count"] == 0
    assert body["summary"] == {
        "word_count": 3,
        "heading_count": 2,
        "paragraph_count": 0,
        "list_count": 0,
        "image_count": 1,
        "images_without_alt": 1,
    }

    stored = client.get(f"{API_PREFIX}/{session['session_id']}").json()
    assert stored["status"] == "extracted"
