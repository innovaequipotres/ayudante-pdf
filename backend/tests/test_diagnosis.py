"""Tests de los endpoints y del servicio de diagnóstico."""

from __future__ import annotations

import logging
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.schemas.ai import AiAnalysisResult, AiStatus
from app.schemas.observation import (
    Category,
    Observation,
    ObservationSource,
    Severity,
)
from app.schemas.session import SessionStatus
from app.services import analysis_service, content_service, session_service

API_PREFIX = "/api/v1/sessions"

_TEXT = (
    "# Tema\n"
    "\n"
    "La célula es la unidad básica de la vida.\n"
    "\n"
    "- Membrana\n"
    "- Citoplasma"
)

_LONG_TEXT = "# Tema\n\n" + ("Uno dos tres. " * 60)

_AI_NOTICE = "Aviso de prueba sobre el envío del texto a un proveedor de IA."


def _create_text_session(
    client: TestClient,
    text: str = _TEXT,
    title: str = "Biología",
) -> dict:
    response = client.post(
        f"{API_PREFIX}/text",
        json={"title": title, "text": text},
    )
    assert response.status_code == 201
    return response.json()


def _create_pdf_session(client: TestClient, pdf_content: bytes) -> dict:
    response = client.post(
        f"{API_PREFIX}/file",
        files={"file": ("clase.pdf", pdf_content, "application/pdf")},
    )
    assert response.status_code == 201
    return response.json()


def _ai_observation(block_id: str = "b1") -> Observation:
    return Observation(
        id=f"ai:undefined_term:{block_id}",
        rule_id="undefined_term",
        category=Category.REPRESENTATION,
        severity=Severity.MEDIUM,
        source=ObservationSource.AI,
        title="Término técnico sin explicar",
        detail="El término no está definido.",
        why_it_matters="Quien no lo conoce pierde el hilo.",
        recommendation="Definirlo la primera vez que aparece.",
        block_id=block_id,
        excerpt="Contenido del bloque.",
    )


def _ai_result(
    status: AiStatus = AiStatus.OK,
    observations: list[Observation] | None = None,
    *,
    truncated: bool = False,
) -> AiAnalysisResult:
    return AiAnalysisResult(
        status=status,
        notice=_AI_NOTICE,
        truncated=truncated,
        observations=observations or [],
    )


def _fake_ai(monkeypatch: pytest.MonkeyPatch, results: list[AiAnalysisResult]) -> list:
    """Parchea analyze_with_ai y registra las llamadas."""
    calls: list = []

    def fake(blocks: list) -> AiAnalysisResult:
        calls.append(blocks)
        return results[min(len(calls) - 1, len(results) - 1)]

    monkeypatch.setattr(analysis_service, "analyze_with_ai", fake)
    return calls


def _analyze_url(session_id: str, use_ai: bool | None = None) -> str:
    url = f"{API_PREFIX}/{session_id}/analyze"
    if use_ai is None:
        return url
    return f"{url}?use_ai={'true' if use_ai else 'false'}"


def test_analyze_extracts_content_when_missing(client: TestClient) -> None:
    session = _create_text_session(client)

    response = client.post(_analyze_url(session["session_id"], use_ai=False))

    assert response.status_code == 200
    assert session_service.get_extracted(UUID(session["session_id"])) is not None
    content = client.get(f"{API_PREFIX}/{session['session_id']}/content")
    assert content.status_code == 200
    assert content.json()["blocks"]


def test_analyze_does_not_reextract_stored_content(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = _create_text_session(client)
    client.post(_analyze_url(session["session_id"], use_ai=False))

    def fail_if_called(text: str) -> list:
        raise AssertionError("El contenido ya extraído no debe reprocesarse")

    monkeypatch.setattr(content_service, "extract_from_text", fail_if_called)

    response = client.post(_analyze_url(session["session_id"], use_ai=False))

    assert response.status_code == 200


def test_use_ai_false_returns_only_rules(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = _fake_ai(monkeypatch, [_ai_result(observations=[_ai_observation()])])
    session = _create_text_session(client, text=_LONG_TEXT)

    response = client.post(_analyze_url(session["session_id"], use_ai=False))

    assert response.status_code == 200
    body = response.json()
    assert calls == []
    assert body["ai_status"] == "skipped"
    assert body["ai_notice"] is None
    assert body["ai_truncated"] is False
    assert body["observations"]
    assert all(item["source"] == "rule" for item in body["observations"])
    assert body["score"] == 96


def test_ai_ok_merges_observations_in_document_order(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = _fake_ai(
        monkeypatch,
        [
            _ai_result(
                observations=[_ai_observation("b1")],
                truncated=True,
            )
        ],
    )
    session = _create_text_session(client, text=_LONG_TEXT)

    response = client.post(_analyze_url(session["session_id"]))

    assert response.status_code == 200
    body = response.json()
    assert len(calls) == 1
    assert body["ai_status"] == "ok"
    assert body["ai_notice"] == _AI_NOTICE
    assert body["ai_truncated"] is True
    assert [item["source"] for item in body["observations"]] == ["ai", "rule"]
    assert [item["block_id"] for item in body["observations"]] == ["b1", "b2"]
    ai_observation = body["observations"][0]
    assert ai_observation["severity"] == "medium"
    assert ai_observation["source"] == "ai"
    # 4 puntos por long_paragraph y 4 por undefined_term.
    assert body["score"] == 92


def test_ai_unavailable_returns_200_with_rules(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _fake_ai(monkeypatch, [_ai_result(status=AiStatus.UNAVAILABLE)])
    session = _create_text_session(client, text=_LONG_TEXT)

    response = client.post(_analyze_url(session["session_id"]))

    assert response.status_code == 200
    body = response.json()
    assert body["ai_status"] == "unavailable"
    assert body["ai_notice"] == _AI_NOTICE
    assert body["observations"]
    assert all(item["source"] == "rule" for item in body["observations"])
    assert body["score"] == 96
    stored = client.get(f"{API_PREFIX}/{session['session_id']}/diagnosis")
    assert stored.status_code == 200
    assert stored.json() == body


def test_retry_after_unavailable_calls_ai_again(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = _fake_ai(
        monkeypatch,
        [
            _ai_result(status=AiStatus.UNAVAILABLE),
            _ai_result(observations=[_ai_observation("b1")]),
        ],
    )
    session = _create_text_session(client, text=_LONG_TEXT)

    first = client.post(_analyze_url(session["session_id"]))
    second = client.post(_analyze_url(session["session_id"]))

    assert first.json()["ai_status"] == "unavailable"
    assert second.json()["ai_status"] == "ok"
    assert len(calls) == 2


def test_complete_diagnosis_is_not_reanalyzed(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = _fake_ai(
        monkeypatch,
        [_ai_result(observations=[_ai_observation("b1")])],
    )
    session = _create_text_session(client, text=_LONG_TEXT)

    first = client.post(_analyze_url(session["session_id"]))
    second = client.post(_analyze_url(session["session_id"]))

    assert first.status_code == 200
    assert second.status_code == 200
    assert second.json() == first.json()
    assert len(calls) == 1


def test_skipped_then_use_ai_true_calls_ai(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = _fake_ai(monkeypatch, [_ai_result()])
    session = _create_text_session(client, text=_LONG_TEXT)

    skipped = client.post(_analyze_url(session["session_id"], use_ai=False))
    analyzed = client.post(_analyze_url(session["session_id"]))

    assert skipped.json()["ai_status"] == "skipped"
    assert analyzed.json()["ai_status"] == "ok"
    assert len(calls) == 1


def test_use_ai_false_after_ok_does_not_overwrite_stored_diagnosis(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = _fake_ai(
        monkeypatch,
        [_ai_result(observations=[_ai_observation("b1")])],
    )
    session = _create_text_session(client, text=_LONG_TEXT)

    complete = client.post(_analyze_url(session["session_id"])).json()
    stored_before = client.get(f"{API_PREFIX}/{session['session_id']}/diagnosis").json()

    rules_only = client.post(_analyze_url(session["session_id"], use_ai=False))
    stored_after = client.get(f"{API_PREFIX}/{session['session_id']}/diagnosis")

    assert rules_only.status_code == 200
    body = rules_only.json()
    assert body["ai_status"] == "skipped"
    assert all(item["source"] == "rule" for item in body["observations"])
    assert len(calls) == 1
    assert stored_before == complete
    assert stored_after.status_code == 200
    assert stored_after.json() == complete


def test_get_before_analyze_returns_conflict(client: TestClient) -> None:
    session = _create_text_session(client)

    response = client.get(f"{API_PREFIX}/{session['session_id']}/diagnosis")

    assert response.status_code == 409
    assert response.json() == {
        "code": "session_not_analyzed",
        "message": "La sesión todavía no fue analizada.",
    }


def test_get_after_analyze_returns_same_body(client: TestClient) -> None:
    session = _create_text_session(client)
    analyzed = client.post(_analyze_url(session["session_id"], use_ai=False))

    response = client.get(f"{API_PREFIX}/{session['session_id']}/diagnosis")

    assert response.status_code == 200
    assert response.json() == analyzed.json()


def test_unknown_session_returns_not_found(client: TestClient) -> None:
    session_id = uuid4()

    analyze_response = client.post(f"{API_PREFIX}/{session_id}/analyze")
    diagnosis_response = client.get(f"{API_PREFIX}/{session_id}/diagnosis")

    for response in (analyze_response, diagnosis_response):
        assert response.status_code == 404
        assert response.json() == {
            "code": "session_not_found",
            "message": "La sesión solicitada no existe.",
        }


def test_pdf_without_text_returns_unprocessable_and_keeps_status(
    client: TestClient,
    pdf_content: bytes,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = _create_pdf_session(client, pdf_content)
    monkeypatch.setattr(
        content_service,
        "extract_from_pdf",
        lambda content: ([], 1),
    )

    response = client.post(_analyze_url(session["session_id"], use_ai=False))

    assert response.status_code == 422
    assert response.json()["code"] == "no_extractable_text"
    stored = client.get(f"{API_PREFIX}/{session['session_id']}").json()
    assert stored["status"] == "uploaded"


def test_uploaded_session_becomes_analyzed(client: TestClient) -> None:
    session = _create_text_session(client)
    assert session["status"] == "uploaded"

    client.post(_analyze_url(session["session_id"], use_ai=False))

    stored = client.get(f"{API_PREFIX}/{session['session_id']}").json()
    assert stored["status"] == "analyzed"


def test_completed_session_does_not_regress(client: TestClient) -> None:
    session = _create_text_session(client)
    session_id = UUID(session["session_id"])
    client.post(_analyze_url(session_id, use_ai=False))
    stored = session_service.get_session(session_id)
    session_service._sessions[session_id] = stored.model_copy(
        update={"status": SessionStatus.COMPLETED}
    )

    client.post(_analyze_url(session_id, use_ai=False))

    assert (
        session_service.get_session(session_id).status
        is SessionStatus.COMPLETED
    )


def test_material_without_observations_scores_100(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _fake_ai(monkeypatch, [_ai_result()])
    session = _create_text_session(client, text="# Tema\n\nTexto breve.")

    body = client.post(_analyze_url(session["session_id"])).json()

    assert body["score"] == 100
    assert body["level"] == "ok"
    assert body["observations"] == []


def test_parallel_analyze_calls_ai_once(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list = []
    barrier = threading.Barrier(2)

    def slow_fake(blocks: list) -> AiAnalysisResult:
        calls.append(blocks)
        time.sleep(0.2)
        return _ai_result()

    monkeypatch.setattr(analysis_service, "analyze_with_ai", slow_fake)
    session = _create_text_session(client)
    url = _analyze_url(session["session_id"])

    def call() -> object:
        with TestClient(app) as thread_client:
            barrier.wait(timeout=5)
            return thread_client.post(url)

    with ThreadPoolExecutor(max_workers=2) as pool:
        responses = list(pool.map(lambda _: call(), range(2)))

    assert all(response.status_code == 200 for response in responses)
    assert len(calls) == 1
    assert responses[0].json() == responses[1].json()


def test_analysis_logs_when_ai_is_called(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    _fake_ai(monkeypatch, [_ai_result()])
    session = _create_text_session(client, text=_LONG_TEXT)

    with caplog.at_level(
        logging.INFO,
        logger="app.services.analysis_service",
    ):
        client.post(_analyze_url(session["session_id"]))
        client.post(_analyze_url(session["session_id"]))

    messages = [record.getMessage() for record in caplog.records]
    assert sum("analisis IA solicitado" in message for message in messages) == 1


def test_response_contract(client: TestClient) -> None:
    session = _create_text_session(client, text=_LONG_TEXT)

    body = client.post(_analyze_url(session["session_id"], use_ai=False)).json()

    assert set(body) >= {
        "session_id",
        "score",
        "level",
        "disclaimer",
        "categories",
        "observations",
        "created_at",
        "ai_status",
        "ai_notice",
        "ai_truncated",
    }
    assert "orientativo" in body["disclaimer"]
    assert "certificación" in body["disclaimer"]
    assert len(body["categories"]) == 6
    assert [item["category"] for item in body["categories"]] == [
        "comprehension",
        "structure",
        "visual",
        "representation",
        "multimedia",
        "navigation",
    ]


def test_openapi_documents_error_responses() -> None:
    schema = app.openapi()
    analyze = schema["paths"][
        "/api/v1/sessions/{session_id}/analyze"
    ]["post"]
    diagnosis = schema["paths"][
        "/api/v1/sessions/{session_id}/diagnosis"
    ]["get"]

    assert {"200", "404", "422"} <= set(analyze["responses"])
    assert {"200", "404", "409"} <= set(diagnosis["responses"])
