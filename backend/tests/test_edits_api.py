"""Tests de los endpoints de ediciones y estados de barreras.

Los datos se siembran con una conexión propia que commitea de verdad
(mismo patrón que test_diagnosis.test_completed_session_does_not_regress),
porque el fixture db_session revierte su transacción y la API no vería
las filas sembradas ahí.
"""

from __future__ import annotations

from contextlib import contextmanager
from datetime import UTC, datetime
from uuid import UUID

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.diagnosis import DiagnosisRecord
from app.models.document import Document
from app.models.document_edit import DocumentEdit
from app.models.extracted_content import ExtractedContentRecord
from app.models.observation_state import ObservationStateRecord
from app.models.user import User
from app.schemas.ai import AiStatus
from app.schemas.content import ContentBlock, ContentSummary, ExtractedContent
from app.schemas.diagnosis import Diagnosis, DiagnosisLevel
from app.schemas.observation import (
    Category,
    Observation,
    ObservationSource,
    Severity,
)
from app.schemas.session import SessionStatus, SourceType

API_PREFIX = "/api/v1/documents"

_SYSTEM_EMAIL = "sessions@ayudante-pdf.local"


@contextmanager
def _fresh_db():
    """Sesión de DB independiente que commitea de verdad (simula otro proceso)."""
    engine = create_engine(settings.test_database_url, pool_pre_ping=True)
    try:
        with Session(engine) as db:
            yield db
    finally:
        engine.dispose()


def _seed_document() -> tuple[UUID, list[dict]]:
    """Crea documento + contenido extraído + diagnóstico, commiteados.

    Devuelve el id del documento y los bloques originales del payload.
    """
    blocks = [
        ContentBlock(id="b1", type="heading", text="Tema", level=1, word_count=1),
        ContentBlock(
            id="b2", type="paragraph", text="Contenido de prueba.", word_count=3
        ),
    ]
    observations = [
        Observation(
            id="long_paragraph:b2",
            rule_id="long_paragraph",
            category=Category.COMPREHENSION,
            severity=Severity.MEDIUM,
            source=ObservationSource.RULE,
            title="Párrafo extenso",
            detail="Tiene 3 palabras.",
            why_it_matters="Los bloques largos cansan.",
            recommendation="Dividir el párrafo.",
            block_id="b2",
        ),
        Observation(
            id="no_headings:b1",
            rule_id="no_headings",
            category=Category.STRUCTURE,
            severity=Severity.HIGH,
            source=ObservationSource.RULE,
            title="Falta título",
            detail="Sin título.",
            why_it_matters="Dificulta la navegación.",
            recommendation="Agregar título.",
            block_id="b1",
        ),
    ]

    with _fresh_db() as db:
        user = db.query(User).filter(User.email == _SYSTEM_EMAIL).first()
        if user is None:
            user = User(
                first_name="Sistema",
                last_name="Sesiones",
                email=_SYSTEM_EMAIL,
                password_hash="!",
            )
            db.add(user)
            db.flush()

        document = Document(
            owner_id=user.id,
            source_type=SourceType.TEXT.value,
            filename="Material de prueba",
            size_bytes=100,
            status=SessionStatus.ANALYZED.value,
        )
        db.add(document)
        db.flush()

        extracted_payload = ExtractedContent(
            session_id=document.id,
            source_type=SourceType.TEXT,
            title="Material de prueba",
            summary=ContentSummary(
                word_count=4,
                heading_count=1,
                paragraph_count=1,
                list_count=0,
                image_count=0,
                images_without_alt=0,
            ),
            blocks=blocks,
        ).model_dump(mode="json")
        db.add(
            ExtractedContentRecord(
                document_id=document.id,
                owner_id=user.id,
                payload=extracted_payload,
            )
        )
        db.add(
            DiagnosisRecord(
                document_id=document.id,
                owner_id=user.id,
                payload=Diagnosis(
                    session_id=document.id,
                    score=80,
                    level=DiagnosisLevel.REVIEW,
                    categories=[],
                    observations=observations,
                    created_at=datetime.now(UTC),
                    ai_status=AiStatus.SKIPPED,
                ).model_dump(mode="json"),
                score=80,
                level=DiagnosisLevel.REVIEW.value,
                ai_status=AiStatus.SKIPPED.value,
            )
        )
        db.commit()
        return document.id, extracted_payload["blocks"]


# ---------- Roundtrip (PUT + GET) ----------


def test_save_and_get_edits_roundtrip(client: TestClient) -> None:
    doc_id, _ = _seed_document()

    payload = {
        "edits": [
            {"block_id": "b1", "text": "Nuevo título"},
            {"block_id": "b2", "text": "Nuevo contenido editado."},
        ],
        "observation_states": [
            {"observation_id": "long_paragraph:b2", "state": "applied"},
            {"observation_id": "no_headings:b1", "state": "ignored"},
        ],
    }

    put_response = client.put(f"{API_PREFIX}/{doc_id}/edits", json=payload)
    assert put_response.status_code == 200

    get_response = client.get(f"{API_PREFIX}/{doc_id}/edits")
    assert get_response.status_code == 200
    assert get_response.json() == put_response.json()
    assert get_response.json()["document_id"] == str(doc_id)
    assert len(get_response.json()["edits"]) == 2
    assert len(get_response.json()["observation_states"]) == 2


def test_edits_persist_across_db_sessions(client: TestClient) -> None:
    doc_id, _ = _seed_document()

    payload = {
        "edits": [{"block_id": "b1", "text": "Título persistente"}],
        "observation_states": [
            {"observation_id": "long_paragraph:b2", "state": "pending"},
        ],
    }
    assert client.put(f"{API_PREFIX}/{doc_id}/edits", json=payload).status_code == 200

    # Conexión nueva: las filas existen en la DB (sobreviven un reinicio).
    with _fresh_db() as db:
        edit = (
            db.query(DocumentEdit)
            .filter(DocumentEdit.document_id == doc_id)
            .first()
        )
        assert edit is not None
        assert edit.text == "Título persistente"

        state = (
            db.query(ObservationStateRecord)
            .filter(ObservationStateRecord.document_id == doc_id)
            .first()
        )
        assert state is not None
        assert state.state == "pending"


def test_put_replaces_existing_edits(client: TestClient) -> None:
    doc_id, _ = _seed_document()

    client.put(
        f"{API_PREFIX}/{doc_id}/edits",
        json={"edits": [{"block_id": "b1", "text": "Primera versión"}],
              "observation_states": []},
    )
    client.put(
        f"{API_PREFIX}/{doc_id}/edits",
        json={"edits": [{"block_id": "b2", "text": "Segunda versión"}],
              "observation_states": []},
    )

    response = client.get(f"{API_PREFIX}/{doc_id}/edits")
    assert response.status_code == 200
    assert len(response.json()["edits"]) == 1
    assert response.json()["edits"][0]["block_id"] == "b2"
    assert response.json()["edits"][0]["text"] == "Segunda versión"


# ---------- Validación ----------


def test_invalid_block_id_returns_422(client: TestClient) -> None:
    doc_id, _ = _seed_document()

    response = client.put(
        f"{API_PREFIX}/{doc_id}/edits",
        json={"edits": [{"block_id": "b99", "text": "Bloque inexistente"}],
              "observation_states": []},
    )
    assert response.status_code == 422
    assert response.json()["code"] == "invalid_block_id"


def test_invalid_observation_id_returns_422(client: TestClient) -> None:
    doc_id, _ = _seed_document()

    response = client.put(
        f"{API_PREFIX}/{doc_id}/edits",
        json={"edits": [],
              "observation_states": [
                  {"observation_id": "fake:obs", "state": "applied"}
              ]},
    )
    assert response.status_code == 422
    assert response.json()["code"] == "invalid_observation_id"


def test_unknown_document_returns_404(client: TestClient) -> None:
    fake_id = "00000000-0000-0000-0000-000000000000"
    response = client.put(
        f"{API_PREFIX}/{fake_id}/edits",
        json={"edits": [], "observation_states": []},
    )
    assert response.status_code == 404
    assert response.json()["code"] == "document_not_found"


def test_get_edits_unknown_document_returns_404(client: TestClient) -> None:
    fake_id = "00000000-0000-0000-0000-000000000000"
    response = client.get(f"{API_PREFIX}/{fake_id}/edits")
    assert response.status_code == 404


# ---------- Estado del documento ----------


def test_document_status_changes_to_editing(client: TestClient) -> None:
    doc_id, _ = _seed_document()

    response = client.put(
        f"{API_PREFIX}/{doc_id}/edits",
        json={"edits": [{"block_id": "b1", "text": "Nuevo título"}],
              "observation_states": []},
    )
    assert response.status_code == 200

    with _fresh_db() as db:
        document = db.get(Document, doc_id)
        assert document.status == SessionStatus.EDITING.value


# ---------- Contenido original intacto ----------


def test_original_content_is_not_modified(client: TestClient) -> None:
    doc_id, original_blocks = _seed_document()

    response = client.put(
        f"{API_PREFIX}/{doc_id}/edits",
        json={"edits": [{"block_id": "b1", "text": "Título modificado"}],
              "observation_states": []},
    )
    assert response.status_code == 200

    with _fresh_db() as db:
        extracted = db.get(ExtractedContentRecord, doc_id)
        assert extracted.payload["blocks"] == original_blocks


# ---------- Estados y payload vacío ----------


def test_observation_state_must_be_valid_enum(client: TestClient) -> None:
    doc_id, _ = _seed_document()

    response = client.put(
        f"{API_PREFIX}/{doc_id}/edits",
        json={"edits": [],
              "observation_states": [
                  {"observation_id": "long_paragraph:b2", "state": "invalid_state"}
              ]},
    )
    assert response.status_code == 422
    assert response.json()["code"] == "VALIDATION_ERROR"


def test_empty_edits_payload_is_valid(client: TestClient) -> None:
    doc_id, _ = _seed_document()

    response = client.put(
        f"{API_PREFIX}/{doc_id}/edits",
        json={"edits": [], "observation_states": []},
    )
    assert response.status_code == 200
    assert response.json()["edits"] == []
    assert response.json()["observation_states"] == []