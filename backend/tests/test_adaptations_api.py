"""Tests del endpoint de adaptaciones."""

from __future__ import annotations

import json
from typing import Any

import pytest
from fastapi.testclient import TestClient

from app.scanner import adaptation as adaptation_engine
from app.services.gemini import AiUnavailableError

URL = "/api/v1/adaptations"


class FakeAI:
    """Servicio simulado que cumple ``StructuredAI``."""

    provider_name = "Google Gemini"

    def __init__(
        self,
        raw: str | None = None,
        error: BaseException | None = None,
    ) -> None:
        self.raw = raw
        self.error = error
        self.calls: list[dict[str, Any]] = []

    def generate_structured(self, **kwargs: Any) -> str:
        self.calls.append(kwargs)
        if self.error is not None:
            raise self.error
        if self.raw is None:
            raise AiUnavailableError("sin respuesta")
        return self.raw


def _raw(adapted_text: str, notes: str | None = None) -> str:
    return json.dumps({"adapted_text": adapted_text, "notes": notes})


def _long_text() -> str:
    sentence = (
        "La célula es la unidad básica de la vida y cumple funciones "
        "esenciales para el organismo."
    )
    return " ".join([sentence] * 8)


def _install(monkeypatch: pytest.MonkeyPatch, ai: FakeAI) -> FakeAI:
    monkeypatch.setattr(adaptation_engine, "get_ai_service", lambda: ai)
    return ai


def test_adaptation_returns_full_contract(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _install(monkeypatch, FakeAI(_raw("Texto adaptado.", "Se simplificó.")))

    response = client.post(
        URL,
        json={
            "type": "simplify",
            "rule_id": "long_paragraph",
            "original_text": "Texto de prueba con varias oraciones.",
            "title": "Párrafo muy extenso",
            "recommendation": "Dividir el párrafo.",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert set(body) == {
        "id",
        "type",
        "rule_id",
        "original_text",
        "adapted_text",
        "notes",
        "source",
        "ai_status",
        "ai_notice",
        "provider",
        "created_at",
    }
    assert body["type"] == "simplify"
    assert body["rule_id"] == "long_paragraph"
    assert body["adapted_text"] == "Texto adaptado."
    assert body["source"] == "ai"
    assert body["ai_status"] == "ok"
    assert body["provider"] == "Google Gemini"


@pytest.mark.parametrize(
    "body",
    [
        {"original_text": "Texto de prueba."},
        {"type": "simplify"},
        {"type": "simplify", "original_text": "   "},
    ],
    ids=["sin_type", "sin_original_text", "texto_vacio"],
)
def test_invalid_body_returns_validation_error(
    client: TestClient,
    body: dict[str, Any],
) -> None:
    response = client.post(URL, json=body)

    assert response.status_code == 422
    assert response.json()["code"] == "VALIDATION_ERROR"


def test_not_adaptable_rule(client: TestClient) -> None:
    response = client.post(
        URL,
        json={
            "type": "describe",
            "rule_id": "no_headings",
            "original_text": "Texto de prueba.",
        },
    )

    assert response.status_code == 422
    assert response.json()["code"] == "observation_not_adaptable"


def test_text_too_long(client: TestClient) -> None:
    response = client.post(
        URL,
        json={"type": "simplify", "original_text": "a" * 8001},
    )

    assert response.status_code == 422
    assert response.json()["code"] == "text_too_long"


def test_ai_failure_returns_local_fallback(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _install(monkeypatch, FakeAI(error=AiUnavailableError("caído")))

    response = client.post(
        URL,
        json={
            "type": "simplify",
            "rule_id": "long_paragraph",
            "original_text": _long_text(),
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["ai_status"] == "unavailable"
    assert body["source"] == "local"
    assert body["adapted_text"] is not None
    assert "\n\n" in body["adapted_text"]


def test_openapi_includes_adaptation_contract(client: TestClient) -> None:
    schema = client.get("/openapi.json").json()

    assert URL in schema["paths"]
    components = schema["components"]["schemas"]
    assert "Adaptation" in components
    assert "AdaptationRequest" in components
    assert "AdaptationType" in components
