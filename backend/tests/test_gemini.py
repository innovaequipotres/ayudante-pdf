"""Tests del cliente de Gemini con respuestas simuladas."""

from __future__ import annotations

import logging
from types import SimpleNamespace
from typing import Any

import pytest
from pydantic import BaseModel

from app.services import gemini
from app.services.gemini import (
    AiUnavailableError,
    GeminiConfig,
    GeminiService,
    load_config,
)


class _FakeModels:
    """Simula ``client.models`` del SDK de Gemini."""

    def __init__(self, outcome: Any) -> None:
        self.outcome = outcome
        self.calls: list[dict[str, Any]] = []

    def generate_content(self, **kwargs: Any) -> Any:
        self.calls.append(kwargs)
        if isinstance(self.outcome, BaseException):
            raise self.outcome
        return self.outcome


class _FakeClient:
    def __init__(self, outcome: Any) -> None:
        self.models = _FakeModels(outcome)


class _Schema(BaseModel):
    value: str


class _FakeResponse:
    def __init__(self, text: str | None) -> None:
        self.text = text


def _service(outcome: Any) -> tuple[GeminiService, _FakeClient]:
    client = _FakeClient(outcome)
    config = GeminiConfig(api_key="clave-de-prueba", model="gemini-test")
    return GeminiService(config, client=client), client


def test_returns_provider_text() -> None:
    service, client = _service(_FakeResponse('{"value": "ok"}'))

    result = service.generate_structured(
        instructions="Instrucciones del sistema.",
        material="Material a analizar.",
        schema=_Schema,
    )

    assert result == '{"value": "ok"}'
    assert len(client.models.calls) == 1


def test_keeps_instructions_and_material_separate() -> None:
    service, client = _service(_FakeResponse('{"value": "ok"}'))

    service.generate_structured(
        instructions="Sos un asistente.",
        material="Texto del material.",
        schema=_Schema,
    )

    call = client.models.calls[0]
    assert call["contents"] == "Texto del material."
    assert call["config"].system_instruction == "Sos un asistente."
    assert call["config"].response_mime_type == "application/json"
    assert call["config"].response_schema is _Schema
    assert call["model"] == "gemini-test"


@pytest.mark.parametrize("text", [None, "", "   "])
def test_empty_response_raises_unavailable(text: str | None) -> None:
    service, _ = _service(_FakeResponse(text))

    with pytest.raises(AiUnavailableError):
        service.generate_structured(
            instructions="Instrucciones.",
            material="Material.",
            schema=_Schema,
        )


def test_sdk_exception_raises_unavailable() -> None:
    service, _ = _service(RuntimeError("falló el SDK"))

    with pytest.raises(AiUnavailableError):
        service.generate_structured(
            instructions="Instrucciones.",
            material="Material.",
            schema=_Schema,
        )


def test_timeout_raises_unavailable() -> None:
    service, _ = _service(TimeoutError("timeout"))

    with pytest.raises(AiUnavailableError):
        service.generate_structured(
            instructions="Instrucciones.",
            material="Material.",
            schema=_Schema,
        )


def test_does_not_log_material(
    caplog: pytest.LogCaptureFixture,
) -> None:
    material = "Texto confidencial del estudiante."
    service, _ = _service(RuntimeError("falló"))

    with caplog.at_level(logging.WARNING):
        with pytest.raises(AiUnavailableError):
            service.generate_structured(
                instructions="Instrucciones.",
                material=material,
                schema=_Schema,
            )

    assert material not in caplog.text


def test_load_config_requires_key_and_model(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        gemini,
        "get_settings",
        lambda: SimpleNamespace(gemini_api_key="", gemini_model="gemini-test"),
    )
    assert load_config() is None

    monkeypatch.setattr(
        gemini,
        "get_settings",
        lambda: SimpleNamespace(gemini_api_key="clave", gemini_model=""),
    )
    assert load_config() is None

    monkeypatch.setattr(
        gemini,
        "get_settings",
        lambda: SimpleNamespace(
            gemini_api_key="clave",
            gemini_model="gemini-test",
        ),
    )
    config = load_config()
    assert config == GeminiConfig(api_key="clave", model="gemini-test")


def test_get_gemini_service_without_config_returns_none(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        gemini,
        "get_settings",
        lambda: SimpleNamespace(gemini_api_key="", gemini_model="gemini-test"),
    )
    gemini.get_gemini_service.cache_clear()

    assert gemini.get_gemini_service() is None
