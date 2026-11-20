"""Casos de error de los endpoints: 415, 413, 404, 409 y 422."""

from __future__ import annotations

from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.core.config import settings

API_PREFIX = "/api/v1/sessions"


def _create_text_session(client: TestClient, text: str = "Material breve.") -> dict:
    response = client.post(f"{API_PREFIX}/text", json={"text": text})
    assert response.status_code == 201
    return response.json()


def _create_pdf_session(client: TestClient, content: bytes) -> dict:
    response = client.post(
        f"{API_PREFIX}/file",
        files={"file": ("material.pdf", content, "application/pdf")},
    )
    assert response.status_code == 201
    return response.json()


@pytest.mark.parametrize("filename", ["apunte.txt", "trabajo.docx", "material"])
def test_unsupported_file_extension_returns_415(
    client: TestClient,
    filename: str,
) -> None:
    response = client.post(
        f"{API_PREFIX}/file",
        files={"file": (filename, b"contenido", "application/octet-stream")},
    )

    assert response.status_code == 415
    assert response.json() == {
        "code": "unsupported_format",
        "message": "Por ahora solo se aceptan archivos PDF.",
    }


def test_file_over_configured_limit_returns_413(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(settings, "max_upload_mb", 1)
    oversized = b"%PDF-1.4" + b"0" * settings.max_upload_bytes

    response = client.post(
        f"{API_PREFIX}/file",
        files={"file": ("grande.pdf", oversized, "application/pdf")},
    )

    assert len(oversized) > settings.max_upload_bytes
    assert response.status_code == 413
    body = response.json()
    assert body["code"] == "file_too_large"
    assert f"{settings.max_upload_mb} MB" in body["message"]


@pytest.mark.parametrize(
    ("method", "suffix"),
    [
        ("GET", ""),
        ("POST", "/extract"),
        ("GET", "/content"),
        ("POST", "/analyze?use_ai=false"),
        ("GET", "/diagnosis"),
    ],
)
def test_unknown_session_returns_404(
    client: TestClient,
    method: str,
    suffix: str,
) -> None:
    response = client.request(method, f"{API_PREFIX}/{uuid4()}{suffix}")

    assert response.status_code == 404
    assert response.json() == {
        "code": "session_not_found",
        "message": "La sesión solicitada no existe.",
    }


def test_content_before_extract_returns_409(client: TestClient) -> None:
    session = _create_text_session(client)

    response = client.get(f"{API_PREFIX}/{session['session_id']}/content")

    assert response.status_code == 409
    assert response.json() == {
        "code": "content_not_extracted",
        "message": "El contenido todavía no fue extraído.",
    }


def test_diagnosis_before_analyze_returns_409(client: TestClient) -> None:
    session = _create_text_session(client)

    response = client.get(f"{API_PREFIX}/{session['session_id']}/diagnosis")

    assert response.status_code == 409
    assert response.json() == {
        "code": "session_not_analyzed",
        "message": "La sesión todavía no fue analizada.",
    }


@pytest.mark.parametrize(
    ("method", "path", "kwargs"),
    [
        ("POST", f"{API_PREFIX}/file", {}),
        ("POST", f"{API_PREFIX}/text", {"json": {}}),
        (
            "POST",
            f"{API_PREFIX}/text",
            {"json": {"title": "x" * 201, "text": "Contenido"}},
        ),
        ("POST", f"{API_PREFIX}/text", {"json": {"text": 123}}),
        ("GET", f"{API_PREFIX}/no-es-un-uuid", {}),
        (
            "POST",
            f"{API_PREFIX}/00000000-0000-0000-0000-000000000000/analyze",
            {"params": {"use_ai": "tal vez"}},
        ),
    ],
)
def test_invalid_request_data_returns_422(
    client: TestClient,
    method: str,
    path: str,
    kwargs: dict,
) -> None:
    response = client.request(method, path, **kwargs)

    assert response.status_code == 422
    body = response.json()
    assert body["code"] == "VALIDATION_ERROR"
    assert body["message"]


def test_malformed_pdf_returns_422_on_extract(
    client: TestClient,
    malformed_pdf: bytes,
) -> None:
    session = _create_pdf_session(client, malformed_pdf)

    response = client.post(f"{API_PREFIX}/{session['session_id']}/extract")

    assert response.status_code == 422
    assert response.json() == {
        "code": "invalid_pdf",
        "message": "No se pudo leer el PDF. Puede estar dañado o protegido.",
    }


def test_pdf_without_text_returns_422_on_extract(
    client: TestClient,
    blank_pdf: bytes,
) -> None:
    session = _create_pdf_session(client, blank_pdf)

    response = client.post(f"{API_PREFIX}/{session['session_id']}/extract")

    assert response.status_code == 422
    body = response.json()
    assert body["code"] == "no_extractable_text"
    assert "no se puede leer" in body["message"]


def test_pdf_without_text_returns_422_on_analyze_and_keeps_status(
    client: TestClient,
    blank_pdf: bytes,
) -> None:
    session = _create_pdf_session(client, blank_pdf)

    response = client.post(
        f"{API_PREFIX}/{session['session_id']}/analyze?use_ai=false"
    )

    assert response.status_code == 422
    assert response.json()["code"] == "no_extractable_text"
    stored = client.get(f"{API_PREFIX}/{session['session_id']}").json()
    assert stored["status"] == "uploaded"
