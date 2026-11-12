"""Tests del cliente de OpenRouter con respuestas simuladas.

No se hace ninguna llamada de red: se inyecta un cliente falso que imita
``chat.completions.create``.
"""

from __future__ import annotations

import json
import logging
from types import SimpleNamespace
from typing import Any

import pytest

from app.scanner.ai_analysis import AiResponse
from app.services import openrouter
from app.services.gemini import AiUnavailableError
from app.services.openrouter import (
    OPENROUTER_BASE_URL,
    OpenRouterConfig,
    OpenRouterService,
    build_response_schema,
    load_config,
)

INSTRUCTIONS = "Sos un asistente de accesibilidad."
MATERIAL = "[b1] La célula es la unidad básica de la vida."


class FakeStatusError(Exception):
    """Imita los errores del SDK que exponen ``status_code``."""

    def __init__(self, status_code: int) -> None:
        super().__init__(f"error {status_code}")
        self.status_code = status_code


class _FakeCompletions:
    def __init__(self, outcomes: list[Any]) -> None:
        self.outcomes = list(outcomes)
        self.calls: list[dict[str, Any]] = []

    def create(self, **kwargs: Any) -> Any:
        self.calls.append(kwargs)
        outcome = self.outcomes.pop(0)
        if isinstance(outcome, BaseException):
            raise outcome
        return outcome


class _FakeChat:
    def __init__(self, outcomes: list[Any]) -> None:
        self.completions = _FakeCompletions(outcomes)


class _FakeClient:
    def __init__(self, outcomes: list[Any]) -> None:
        self.chat = _FakeChat(outcomes)


def _response(content: str | None) -> Any:
    return SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(content=content))]
    )


def _raw(findings: list[dict[str, Any]] | None = None) -> str:
    return json.dumps({"findings": findings or []})


def _service(
    outcomes: list[Any],
) -> tuple[OpenRouterService, _FakeClient]:
    client = _FakeClient(outcomes)
    config = OpenRouterConfig(
        api_key="sk-clave-de-prueba",
        model="test/model",
        app_name="Ayudante PDF",
        referer="https://example.com",
        timeout=12.0,
    )
    return OpenRouterService(config, client=client), client


def _generate(service: OpenRouterService, material: str = MATERIAL) -> str:
    return service.generate_structured(
        instructions=INSTRUCTIONS,
        material=material,
        schema=AiResponse,
    )


def test_returns_validated_object() -> None:
    raw = _raw(
        [
            {
                "rule_id": "undefined_term",
                "block_id": "b1",
                "detail": "No se define el término.",
            }
        ]
    )
    service, client = _service([_response(raw)])

    result = _generate(service)

    parsed = AiResponse.model_validate_json(result)
    assert parsed.findings[0].rule_id == "undefined_term"
    assert len(client.chat.completions.calls) == 1


def test_keeps_instructions_and_material_separate() -> None:
    service, client = _service([_response(_raw())])

    _generate(service)

    messages = client.chat.completions.calls[0]["messages"]
    assert messages[0] == {"role": "system", "content": INSTRUCTIONS}
    assert messages[1] == {"role": "user", "content": MATERIAL}
    assert len(messages) == 2


def test_sends_strict_json_schema_and_require_parameters() -> None:
    service, client = _service([_response(_raw())])

    _generate(service)

    call = client.chat.completions.calls[0]
    assert call["model"] == "test/model"
    assert call["extra_body"] == {"provider": {"require_parameters": True}}

    response_format = call["response_format"]
    assert response_format["type"] == "json_schema"
    assert response_format["json_schema"]["strict"] is True
    assert response_format["json_schema"]["name"] == "AiResponse"

    schema = response_format["json_schema"]["schema"]
    assert "$defs" not in json.dumps(schema)
    assert schema["additionalProperties"] is False
    assert schema["required"] == ["findings"]

    item = schema["properties"]["findings"]["items"]
    assert item["additionalProperties"] is False
    assert set(item["required"]) == {"rule_id", "block_id", "detail"}


def test_build_response_schema_inlines_defs() -> None:
    schema = build_response_schema(AiResponse)

    assert "$defs" not in schema
    assert "$ref" not in json.dumps(schema)
    assert schema["properties"]["findings"]["items"]["additionalProperties"] is False


def test_retries_once_with_json_object_on_400() -> None:
    fenced = f"```json\n{_raw()}\n```"
    service, client = _service([FakeStatusError(400), _response(fenced)])

    result = _generate(service)

    assert result == _raw()
    calls = client.chat.completions.calls
    assert len(calls) == 2
    assert calls[1]["response_format"] == {"type": "json_object"}
    assert calls[1]["messages"][1] == {"role": "user", "content": MATERIAL}
    system = calls[1]["messages"][0]["content"]
    assert "esquema" in system
    assert "findings" in system


def test_does_not_retry_more_than_once() -> None:
    service, client = _service([FakeStatusError(400), FakeStatusError(400)])

    with pytest.raises(AiUnavailableError):
        _generate(service)

    assert len(client.chat.completions.calls) == 2


def test_accepts_json_inside_code_fences() -> None:
    service, _ = _service([_response(f"```json\n{_raw()}\n```")])

    result = _generate(service)

    assert json.loads(result) == {"findings": []}


@pytest.mark.parametrize("content", [None, "", "   "])
def test_empty_content_raises_unavailable(content: str | None) -> None:
    service, _ = _service([_response(content)])

    with pytest.raises(AiUnavailableError):
        _generate(service)


def test_invalid_json_raises_unavailable() -> None:
    service, _ = _service([_response("esto no es JSON")])

    with pytest.raises(AiUnavailableError):
        _generate(service)


def test_invalid_schema_raises_unavailable() -> None:
    service, _ = _service([_response(json.dumps({"findings": "no es lista"}))])

    with pytest.raises(AiUnavailableError):
        _generate(service)


def test_sdk_exception_raises_unavailable() -> None:
    service, _ = _service([RuntimeError("falló el SDK")])

    with pytest.raises(AiUnavailableError):
        _generate(service)


def test_timeout_raises_unavailable() -> None:
    service, _ = _service([TimeoutError("timeout")])

    with pytest.raises(AiUnavailableError):
        _generate(service)


@pytest.mark.parametrize("status_code", [401, 402, 429])
def test_auth_payment_and_rate_limit_raise_unavailable(
    status_code: int,
) -> None:
    service, client = _service([FakeStatusError(status_code)])

    with pytest.raises(AiUnavailableError):
        _generate(service)

    assert len(client.chat.completions.calls) == 1


def test_does_not_log_material_or_key(
    caplog: pytest.LogCaptureFixture,
) -> None:
    service, _ = _service([RuntimeError("falló")])

    with caplog.at_level(logging.WARNING):
        with pytest.raises(AiUnavailableError):
            _generate(service)

    assert MATERIAL not in caplog.text
    assert "sk-clave-de-prueba" not in caplog.text


def test_client_uses_openrouter_base_url_and_headers(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, Any] = {}

    def fake_openai(**kwargs: Any) -> object:
        captured.update(kwargs)
        return object()

    monkeypatch.setattr("openai.OpenAI", fake_openai)
    config = OpenRouterConfig(
        api_key="sk-clave",
        model="test/model",
        app_name="Ayudante PDF",
        referer="https://example.com",
        timeout=12.0,
    )
    service = OpenRouterService(config)

    _ = service.client

    assert captured["base_url"] == OPENROUTER_BASE_URL
    assert captured["timeout"] == 12.0
    assert captured["default_headers"] == {
        "HTTP-Referer": "https://example.com",
        "X-Title": "Ayudante PDF",
    }


def test_client_omits_empty_optional_headers(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, Any] = {}

    def fake_openai(**kwargs: Any) -> object:
        captured.update(kwargs)
        return object()

    monkeypatch.setattr("openai.OpenAI", fake_openai)
    config = OpenRouterConfig(
        api_key="sk-clave",
        model="test/model",
        app_name="",
        referer="",
    )

    _ = OpenRouterService(config).client

    assert captured["default_headers"] is None


def test_provider_name_includes_model() -> None:
    service, _ = _service([_response(_raw())])

    assert "OpenRouter" in service.provider_name
    assert "test/model" in service.provider_name


@pytest.mark.parametrize(
    ("api_key", "model"),
    [("", "test/model"), ("sk-clave", ""), ("", "")],
)
def test_load_config_requires_key_and_model(
    monkeypatch: pytest.MonkeyPatch,
    api_key: str,
    model: str,
) -> None:
    monkeypatch.setattr(
        openrouter,
        "get_settings",
        lambda: SimpleNamespace(
            openrouter_api_key=api_key,
            openrouter_model=model,
            openrouter_app_name="Ayudante PDF",
            openrouter_referer="",
            openrouter_timeout_seconds=30.0,
        ),
    )

    assert load_config() is None


def test_load_config_reads_all_values(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        openrouter,
        "get_settings",
        lambda: SimpleNamespace(
            openrouter_api_key="sk-clave",
            openrouter_model="test/model",
            openrouter_app_name="Ayudante PDF",
            openrouter_referer="https://example.com",
            openrouter_timeout_seconds=15.0,
        ),
    )

    config = load_config()

    assert config is not None
    assert config.api_key == "sk-clave"
    assert config.model == "test/model"
    assert config.app_name == "Ayudante PDF"
    assert config.referer == "https://example.com"
    assert config.timeout == 15.0
