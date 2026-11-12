"""Tests del selector de proveedor de IA y de los avisos de privacidad."""

from __future__ import annotations

import logging
from types import SimpleNamespace
from typing import Any

import pytest

from app.scanner import ai_analysis
from app.scanner.ai_analysis import analyze_with_ai
from app.schemas.ai import AI_NOTICE, build_ai_notice
from app.schemas.content import BlockType, ContentBlock
from app.services import ai_provider
from app.services.ai_provider import get_ai_service, get_provider_label


class _FakeAI:
    provider_name = "Google Gemini"

    def __init__(self) -> None:
        self.calls = 0

    def generate_structured(self, **kwargs: Any) -> str:
        self.calls += 1
        return '{"findings": []}'


def _settings(provider: str, model: str = "") -> SimpleNamespace:
    return SimpleNamespace(ai_provider=provider, openrouter_model=model)


def test_gemini_is_the_default_provider(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    sentinel = object()
    monkeypatch.setattr(
        ai_provider, "get_settings", lambda: _settings("gemini")
    )
    monkeypatch.setattr(
        ai_provider, "get_gemini_service", lambda: sentinel
    )

    assert get_ai_service() is sentinel


def test_openrouter_is_used_when_configured(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    sentinel = object()
    monkeypatch.setattr(
        ai_provider, "get_settings", lambda: _settings("openrouter", "test/model")
    )
    monkeypatch.setattr(
        ai_provider, "get_openrouter_service", lambda: sentinel
    )

    assert get_ai_service() is sentinel


def test_openrouter_without_key_or_model_returns_none(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        ai_provider, "get_settings", lambda: _settings("openrouter")
    )
    monkeypatch.setattr(ai_provider, "get_openrouter_service", lambda: None)

    assert get_ai_service() is None


def test_unknown_provider_returns_none_and_warns(
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    monkeypatch.setattr(
        ai_provider, "get_settings", lambda: _settings("otro")
    )

    with caplog.at_level(logging.WARNING):
        assert get_ai_service() is None

    assert "desconocido" in caplog.text


def test_provider_label_for_gemini(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        ai_provider, "get_settings", lambda: _settings("gemini")
    )

    assert get_provider_label() == "Google Gemini"


def test_provider_label_for_openrouter_includes_model(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        ai_provider,
        "get_settings",
        lambda: _settings("openrouter", "test/model"),
    )

    label = get_provider_label()

    assert label.startswith("OpenRouter")
    assert "test/model" in label


def test_provider_label_for_openrouter_without_model(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        ai_provider, "get_settings", lambda: _settings("openrouter")
    )

    assert "no configurado" in get_provider_label()


def test_notice_names_gemini() -> None:
    notice = build_ai_notice(False, "Google Gemini")

    assert "Google Gemini" in notice
    assert "OpenRouter" not in notice
    assert AI_NOTICE == build_ai_notice(False)


def test_notice_names_openrouter_and_model() -> None:
    provider = "OpenRouter y el proveedor del modelo test/model"

    notice = build_ai_notice(False, provider)

    assert "OpenRouter" in notice
    assert "test/model" in notice
    assert "datos personales" in notice


def test_notice_mentions_truncation() -> None:
    notice = build_ai_notice(True, "Google Gemini")

    assert "solo una parte" in notice


def test_analyze_with_ai_uses_provider_selector(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    ai = _FakeAI()
    monkeypatch.setattr(ai_analysis, "get_ai_service", lambda: ai)
    blocks = [
        ContentBlock(
            id="b1",
            type=BlockType.PARAGRAPH,
            text="Un texto breve.",
            page=1,
        )
    ]

    result = analyze_with_ai(blocks)

    assert ai.calls == 1
    assert result.status.value == "ok"
    assert result.observations == []
