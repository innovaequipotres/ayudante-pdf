"""Tests de los endpoints de documentos."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

API_PREFIX = "/api/v1/documents"
SESSIONS_PREFIX = "/api/v1/sessions"
FOLDERS_PREFIX = "/api/v1/folders"


def _create_text_session(client: TestClient, title: str = "Material") -> dict:
    """Helper: crea una sesión de texto y devuelve su JSON."""
    response = client.post(
        f"{SESSIONS_PREFIX}/text",
        json={"title": title, "text": "# Tema\n\nContenido de prueba."},
    )
    assert response.status_code == 201
    return response.json()


def _create_folder(client: TestClient, name: str) -> dict:
    """Helper: crea una carpeta y devuelve su JSON."""
    response = client.post(FOLDERS_PREFIX, json={"name": name})
    assert response.status_code == 201
    return response.json()


# ---------- GET /documents ----------


def test_list_documents_empty(client: TestClient) -> None:
    response = client.get(API_PREFIX)

    assert response.status_code == 200
    assert response.json() == []


def test_list_documents_returns_created_sessions(client: TestClient) -> None:
    _create_text_session(client, "Biología")
    _create_text_session(client, "Historia")

    response = client.get(API_PREFIX)

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 2
    titles = [doc["filename"] for doc in body]
    assert "Biología" in titles
    assert "Historia" in titles


def test_list_documents_filter_by_folder(client: TestClient) -> None:
    folder = _create_folder(client, "Ciencias")
    doc1 = _create_text_session(client, "Biología")
    _create_text_session(client, "Historia")  # Sin carpeta

    # Mover Biología a la carpeta
    client.patch(f"{API_PREFIX}/{doc1['session_id']}", json={"folder_id": folder["id"]})

    response = client.get(f"{API_PREFIX}?folder_id={folder['id']}")

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["filename"] == "Biología"


def test_list_documents_filter_by_status(client: TestClient) -> None:
    _create_text_session(client, "Material")

    response = client.get(f"{API_PREFIX}?status=uploaded")

    assert response.status_code == 200
    assert len(response.json()) == 1

    response = client.get(f"{API_PREFIX}?status=analyzed")
    assert response.status_code == 200
    assert len(response.json()) == 0


def test_list_documents_search_by_name(client: TestClient) -> None:
    _create_text_session(client, "Biología Celular")
    _create_text_session(client, "Historia Antigua")

    response = client.get(f"{API_PREFIX}?q=biología")

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["filename"] == "Biología Celular"


# ---------- GET /documents/{id} ----------


def test_get_document_by_id(client: TestClient) -> None:
    session = _create_text_session(client, "Material")

    response = client.get(f"{API_PREFIX}/{session['session_id']}")

    assert response.status_code == 200
    assert response.json()["filename"] == "Material"
    assert response.json()["source_type"] == "text"


def test_get_unknown_document_returns_not_found(client: TestClient) -> None:
    response = client.get(f"{API_PREFIX}/00000000-0000-0000-0000-000000000000")

    assert response.status_code == 404
    assert response.json()["code"] == "document_not_found"


# ---------- PATCH /documents/{id} ----------


def test_rename_document(client: TestClient) -> None:
    session = _create_text_session(client, "Material")

    response = client.patch(
        f"{API_PREFIX}/{session['session_id']}", json={"filename": "Nuevo Nombre"}
    )

    assert response.status_code == 200
    assert response.json()["filename"] == "Nuevo Nombre"


def test_move_document_to_folder(client: TestClient) -> None:
    session = _create_text_session(client, "Material")
    folder = _create_folder(client, "Ciencias")

    response = client.patch(
        f"{API_PREFIX}/{session['session_id']}", json={"folder_id": folder["id"]}
    )

    assert response.status_code == 200
    assert response.json()["folder_id"] == folder["id"]


def test_move_document_to_unknown_folder_returns_not_found(
    client: TestClient,
) -> None:
    session = _create_text_session(client, "Material")

    response = client.patch(
        f"{API_PREFIX}/{session['session_id']}",
        json={"folder_id": "00000000-0000-0000-0000-000000000000"},
    )

    assert response.status_code == 404
    assert response.json()["code"] == "folder_not_found"


def test_update_unknown_document_returns_not_found(client: TestClient) -> None:
    response = client.patch(
        f"{API_PREFIX}/00000000-0000-0000-0000-000000000000",
        json={"filename": "Nuevo"},
    )

    assert response.status_code == 404
    assert response.json()["code"] == "document_not_found"