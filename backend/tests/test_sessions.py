from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient

from app.core.config import settings
from app.core.exceptions import AppError
from app.services import session_service

API_PREFIX = "/api/v1/sessions"


def test_create_session_from_valid_pdf(client: TestClient, pdf_content: bytes) -> None:
    response = client.post(
        f"{API_PREFIX}/file",
        files={"file": ("clase.pdf", pdf_content, "application/pdf")},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["source_type"] == "pdf"
    assert body["filename"] == "clase.pdf"
    assert body["size_bytes"] == len(pdf_content)
    assert body["status"] == "uploaded"
    assert body["session_id"]
    assert body["created_at"].endswith(("Z", "+00:00"))


@pytest.mark.parametrize("filename", ["apunte.txt", "trabajo.docx"])
def test_reject_non_pdf_extension(
    client: TestClient, pdf_content: bytes, filename: str
) -> None:
    response = client.post(
        f"{API_PREFIX}/file",
        files={"file": (filename, pdf_content, "application/octet-stream")},
    )

    assert response.status_code == 415
    assert response.json() == {
        "code": "unsupported_format",
        "message": "Por ahora solo se aceptan archivos PDF.",
    }


def test_reject_fake_pdf(client: TestClient) -> None:
    response = client.post(
        f"{API_PREFIX}/file",
        files={
            "file": (
                "renombrado.pdf",
                b"esto es un txt renombrado, no un PDF",
                "application/pdf",
            )
        },
    )

    assert response.status_code == 400
    assert response.json()["code"] == "invalid_pdf"


def test_reject_empty_file(client: TestClient) -> None:
    response = client.post(
        f"{API_PREFIX}/file",
        files={"file": ("vacio.pdf", b"", "application/pdf")},
    )

    assert response.status_code == 400
    assert response.json()["code"] == "empty_content"


def test_reject_file_over_size_limit(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(settings, "max_upload_mb", 1)
    oversized = b"%PDF-1.4" + b"0" * (1024 * 1024)

    response = client.post(
        f"{API_PREFIX}/file",
        files={"file": ("grande.pdf", oversized, "application/pdf")},
    )

    assert response.status_code == 413
    body = response.json()
    assert body["code"] == "file_too_large"
    assert "1 MB" in body["message"]


def test_create_session_from_text(client: TestClient) -> None:
    text = "La célula es la unidad básica de la vida."

    response = client.post(
        f"{API_PREFIX}/text",
        json={"title": "  Biología  ", "text": text},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["source_type"] == "text"
    assert body["filename"] == "Biología"
    assert body["size_bytes"] == len(text.encode("utf-8"))
    assert body["status"] == "uploaded"
    assert body["created_at"].endswith(("Z", "+00:00"))


def test_create_session_from_text_without_title(client: TestClient) -> None:
    response = client.post(f"{API_PREFIX}/text", json={"text": "Texto sin título"})

    assert response.status_code == 201
    assert response.json()["filename"] is None


@pytest.mark.parametrize("text", ["", "   ", "\n\t  \n"])
def test_reject_blank_text(client: TestClient, text: str) -> None:
    response = client.post(f"{API_PREFIX}/text", json={"text": text})

    assert response.status_code == 400
    assert response.json() == {
        "code": "empty_content",
        "message": "El texto no puede estar vacío.",
    }


def test_get_created_session(client: TestClient, pdf_content: bytes) -> None:
    created = client.post(
        f"{API_PREFIX}/file",
        files={"file": ("clase.pdf", pdf_content, "application/pdf")},
    ).json()

    response = client.get(f"{API_PREFIX}/{created['session_id']}")

    assert response.status_code == 200
    assert response.json() == created


def test_get_unknown_session(client: TestClient) -> None:
    response = client.get(f"{API_PREFIX}/{uuid4()}")

    assert response.status_code == 404
    assert response.json() == {
        "code": "session_not_found",
        "message": "La sesión solicitada no existe.",
    }


def test_get_raw_content_from_pdf(
    client: TestClient, pdf_content: bytes
) -> None:
    created = client.post(
        f"{API_PREFIX}/file",
        files={"file": ("clase.pdf", pdf_content, "application/pdf")},
    ).json()

    raw = session_service.get_raw_content(UUID(created["session_id"]))

    assert raw == pdf_content


def test_get_raw_content_from_text(client: TestClient) -> None:
    created = client.post(
        f"{API_PREFIX}/text", json={"text": "Contenido original"}
    ).json()

    raw = session_service.get_raw_content(UUID(created["session_id"]))

    assert raw == "Contenido original"


def test_get_raw_content_of_unknown_session() -> None:
    with pytest.raises(AppError) as error:
        session_service.get_raw_content(uuid4())

    assert error.value.code == "session_not_found"
    assert error.value.status_code == 404
