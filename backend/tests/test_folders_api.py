"""Tests de los endpoints de carpetas."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

API_PREFIX = "/api/v1/folders"


def _create_folder(
    client: TestClient,
    name: str,
    parent_id: str | None = None,
) -> dict:
    """Helper: crea una carpeta y devuelve su JSON."""
    payload: dict = {"name": name}
    if parent_id is not None:
        payload["parent_id"] = parent_id
    response = client.post(API_PREFIX, json=payload)
    assert response.status_code == 201
    return response.json()


# ---------- POST /folders ----------


def test_create_root_folder(client: TestClient) -> None:
    body = _create_folder(client, "Matemática")

    assert body["name"] == "Matemática"
    assert body["parent_id"] is None
    assert body["id"]


def test_create_folder_inside_parent(client: TestClient) -> None:
    parent = _create_folder(client, "Ciencias")
    child = _create_folder(client, "Unidad 1", parent_id=parent["id"])

    assert child["parent_id"] == parent["id"]
    assert child["name"] == "Unidad 1"


def test_create_folder_duplicate_name_returns_conflict(
    client: TestClient,
) -> None:
    _create_folder(client, "Matemática")

    response = client.post(API_PREFIX, json={"name": "matemática"})

    assert response.status_code == 409
    assert response.json()["code"] == "folder_name_conflict"


def test_create_folder_with_unknown_parent_returns_not_found(
    client: TestClient,
) -> None:
    response = client.post(
        API_PREFIX,
        json={"name": "Huérfana", "parent_id": "00000000-0000-0000-0000-000000000000"},
    )

    assert response.status_code == 404
    assert response.json()["code"] == "folder_not_found"


def test_create_folder_blank_name_returns_validation_error(
    client: TestClient,
) -> None:
    response = client.post(API_PREFIX, json={"name": "   "})

    assert response.status_code == 422
    assert response.json()["code"] == "VALIDATION_ERROR"


# ---------- GET /folders ----------


def test_list_folders_returns_all_created(client: TestClient) -> None:
    _create_folder(client, "Matemática")
    _create_folder(client, "Ciencias")

    response = client.get(API_PREFIX)

    assert response.status_code == 200
    names = [item["name"] for item in response.json()]
    assert "Matemática" in names
    assert "Ciencias" in names


def test_get_folder_by_id(client: TestClient) -> None:
    created = _create_folder(client, "Historia")

    response = client.get(f"{API_PREFIX}/{created['id']}")

    assert response.status_code == 200
    assert response.json() == created


def test_get_unknown_folder_returns_not_found(client: TestClient) -> None:
    response = client.get(f"{API_PREFIX}/00000000-0000-0000-0000-000000000000")

    assert response.status_code == 404
    assert response.json()["code"] == "folder_not_found"


# ---------- PATCH /folders/{id} ----------


def test_rename_folder(client: TestClient) -> None:
    folder = _create_folder(client, "Matemática")

    response = client.patch(f"{API_PREFIX}/{folder['id']}", json={"name": "Álgebra"})

    assert response.status_code == 200
    assert response.json()["name"] == "Álgebra"


def test_rename_folder_to_existing_name_returns_conflict(
    client: TestClient,
) -> None:
    _create_folder(client, "Matemática")
    other = _create_folder(client, "Álgebra")

    response = client.patch(
        f"{API_PREFIX}/{other['id']}", json={"name": "matemática"}
    )

    assert response.status_code == 409
    assert response.json()["code"] == "folder_name_conflict"


def test_move_folder_into_itself_is_rejected(client: TestClient) -> None:
    folder = _create_folder(client, "Matemática")

    response = client.patch(
        f"{API_PREFIX}/{folder['id']}", json={"parent_id": folder["id"]}
    )

    assert response.status_code == 422
    assert response.json()["code"] == "folder_cannot_be_own_parent"


def test_move_folder_into_descendant_is_rejected(client: TestClient) -> None:
    parent = _create_folder(client, "Ciencias")
    child = _create_folder(client, "Unidad 1", parent_id=parent["id"])

    # Intentar mover el padre dentro del hijo (crea ciclo).
    response = client.patch(
        f"{API_PREFIX}/{parent['id']}", json={"parent_id": child["id"]}
    )

    assert response.status_code == 422
    assert response.json()["code"] == "folder_cannot_be_descendant"


# ---------- DELETE /folders/{id} ----------


def test_delete_empty_folder_succeeds(client: TestClient) -> None:
    folder = _create_folder(client, "Temporal")

    response = client.delete(f"{API_PREFIX}/{folder['id']}")

    assert response.status_code == 204
    assert client.get(f"{API_PREFIX}/{folder['id']}").status_code == 404


def test_delete_folder_with_documents_returns_conflict(
    client: TestClient,
) -> None:
    folder = _create_folder(client, "Con documentos")
    # Crear un documento (sesión) y moverlo a la carpeta.
    session = client.post(
        "/api/v1/sessions/text",
        json={"title": "Material", "text": "# Tema\n\nContenido."},
    ).json()
    client.patch(
        f"/api/v1/documents/{session['session_id']}",
        json={"folder_id": folder["id"]},
    )

    response = client.delete(f"{API_PREFIX}/{folder['id']}")

    assert response.status_code == 409
    assert response.json()["code"] == "folder_has_documents"


def test_delete_unknown_folder_returns_not_found(client: TestClient) -> None:
    response = client.delete(
        f"{API_PREFIX}/00000000-0000-0000-0000-000000000000"
    )

    assert response.status_code == 404
    assert response.json()["code"] == "folder_not_found"