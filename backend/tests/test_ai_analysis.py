"""Tests del análisis semántico con IA sobre respuestas simuladas."""

from __future__ import annotations

import json
from typing import Any

import pytest

from app.scanner import ai_analysis
from app.scanner.ai_analysis import (
    AI_MAX_CHARS,
    AI_RULES,
    AiResponse,
    analyze_with_ai,
)
from app.schemas.content import BlockType, ContentBlock
from app.schemas.observation import Category, ObservationSource, Severity
from app.services.gemini import AiUnavailableError


class FakeAI:
    """Servicio simulado que cumple ``StructuredAI``."""

    def __init__(
        self,
        raw: str | None = None,
        error: BaseException | None = None,
        provider_name: str = "Google Gemini",
    ) -> None:
        self.raw = raw
        self.error = error
        self.provider_name = provider_name
        self.calls: list[dict[str, Any]] = []

    def generate_structured(self, **kwargs: Any) -> str:
        self.calls.append(kwargs)
        if self.error is not None:
            raise self.error
        if self.raw is None:
            raise AiUnavailableError("sin respuesta")
        return self.raw


def _blocks() -> list[ContentBlock]:
    return [
        ContentBlock(
            id="b1",
            type=BlockType.PARAGRAPH,
            text="La célula es la unidad básica de la vida y cumple funciones.",
            page=1,
        ),
        ContentBlock(
            id="b2",
            type=BlockType.HEADING,
            level=2,
            text="Partes de la célula",
            page=1,
        ),
        ContentBlock(
            id="b3",
            type=BlockType.LIST,
            items=["Membrana", "Citoplasma"],
            page=2,
        ),
    ]


def _raw(findings: list[dict[str, Any]]) -> str:
    return json.dumps({"findings": findings})


def _finding(rule_id: str = "undefined_term", block_id: str = "b1") -> dict[str, Any]:
    return {
        "rule_id": rule_id,
        "block_id": block_id,
        "detail": "El término no está definido en el material.",
    }


def test_returns_validated_observation() -> None:
    ai = FakeAI(_raw([_finding()]))

    result = analyze_with_ai(_blocks(), ai)

    assert result.status.value == "ok"
    assert result.truncated is False
    assert len(result.observations) == 1

    observation = result.observations[0]
    assert observation.id == "ai:undefined_term:b1"
    assert observation.rule_id == "undefined_term"
    assert observation.category is Category.REPRESENTATION
    assert observation.severity is Severity.MEDIUM
    assert observation.source is ObservationSource.AI
    assert observation.block_id == "b1"
    assert observation.page == 1
    assert observation.excerpt == (
        "La célula es la unidad básica de la vida y cumple funciones."
    )
    assert "El término no está definido" in (observation.detail or "")


def test_sends_instructions_and_material_separately() -> None:
    ai = FakeAI(_raw([]))

    analyze_with_ai(_blocks(), ai)

    call = ai.calls[0]
    assert "accesibilidad" in call["instructions"]
    assert "undefined_term" in call["instructions"]
    assert "Material a analizar" not in call["instructions"]
    assert "[b1]" in call["material"]
    assert "La célula es la unidad básica" in call["material"]
    assert call["schema"] is AiResponse


def test_discards_unknown_rules_and_blocks() -> None:
    ai = FakeAI(
        _raw(
            [
                _finding(rule_id="regla_inventada", block_id="b1"),
                _finding(rule_id="undefined_term", block_id="b99"),
                _finding(rule_id="dense_section", block_id="b1"),
            ]
        )
    )

    result = analyze_with_ai(_blocks(), ai)

    assert len(result.observations) == 1
    assert result.observations[0].rule_id == "dense_section"


def test_discards_duplicates() -> None:
    ai = FakeAI(
        _raw(
            [
                _finding(rule_id="undefined_term", block_id="b1"),
                _finding(rule_id="undefined_term", block_id="b1"),
            ]
        )
    )

    result = analyze_with_ai(_blocks(), ai)

    assert len(result.observations) == 1


def test_ignores_severity_sent_by_model() -> None:
    finding = {**_finding(), "severity": "high"}
    ai = FakeAI(_raw([finding]))

    result = analyze_with_ai(_blocks(), ai)

    assert result.observations[0].severity is Severity.MEDIUM


def test_accepts_json_inside_code_fences() -> None:
    raw = f"```json\n{_raw([_finding()])}\n```"
    ai = FakeAI(raw)

    result = analyze_with_ai(_blocks(), ai)

    assert result.status.value == "ok"
    assert len(result.observations) == 1


def test_truncates_long_material_and_mentions_it() -> None:
    ai = FakeAI(_raw([]))
    blocks = [
        ContentBlock(
            id="b1",
            type=BlockType.PARAGRAPH,
            text="palabra " * 200,
            page=1,
        )
    ]

    result = analyze_with_ai(blocks, ai, max_chars=100)

    assert result.truncated is True
    assert "solo una parte" in result.notice
    assert len(ai.calls[0]["material"]) <= 100


def test_default_limit_is_applied() -> None:
    ai = FakeAI(_raw([]))
    text = "palabra " * (AI_MAX_CHARS // 4)

    result = analyze_with_ai(
        [ContentBlock(id="b1", type=BlockType.PARAGRAPH, text=text, page=1)],
        ai,
    )

    assert result.truncated is True


def test_invalid_json_returns_unavailable() -> None:
    ai = FakeAI("esto no es JSON")

    result = analyze_with_ai(_blocks(), ai)

    assert result.status.value == "unavailable"
    assert result.observations == []


def test_invalid_schema_returns_unavailable() -> None:
    ai = FakeAI(json.dumps({"findings": "no es una lista"}))

    result = analyze_with_ai(_blocks(), ai)

    assert result.status.value == "unavailable"


def test_provider_error_returns_unavailable() -> None:
    ai = FakeAI(error=AiUnavailableError("429"))

    result = analyze_with_ai(_blocks(), ai)

    assert result.status.value == "unavailable"
    assert result.observations == []
    assert "Google Gemini" in result.notice


def test_unexpected_provider_error_returns_unavailable() -> None:
    ai = FakeAI(error=RuntimeError("boom"))

    result = analyze_with_ai(_blocks(), ai)

    assert result.status.value == "unavailable"


def test_no_service_returns_unavailable(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(ai_analysis, "get_ai_service", lambda: None)
    monkeypatch.setattr(
        ai_analysis, "get_provider_label", lambda: "Google Gemini"
    )

    result = analyze_with_ai(_blocks())

    assert result.status.value == "unavailable"
    assert "Google Gemini" in result.notice


def test_uses_provider_selector(monkeypatch: pytest.MonkeyPatch) -> None:
    ai = FakeAI(_raw([_finding()]))
    monkeypatch.setattr(ai_analysis, "get_ai_service", lambda: ai)

    result = analyze_with_ai(_blocks())

    assert result.status.value == "ok"
    assert len(ai.calls) == 1


def test_openrouter_notice_names_provider_and_model() -> None:
    ai = FakeAI(
        _raw([]),
        provider_name="OpenRouter y el proveedor del modelo test/model",
    )

    result = analyze_with_ai(_blocks(), ai)

    assert "OpenRouter" in result.notice
    assert "test/model" in result.notice
    assert "datos personales" in result.notice


def test_empty_material_does_not_call_provider() -> None:
    ai = FakeAI(_raw([]))
    blocks = [ContentBlock(id="b1", type=BlockType.IMAGE, page=1)]

    result = analyze_with_ai(blocks, ai)

    assert result.status.value == "ok"
    assert result.observations == []
    assert ai.calls == []


def test_non_positive_limit_is_rejected() -> None:
    with pytest.raises(ValueError):
        analyze_with_ai(_blocks(), FakeAI(_raw([])), max_chars=0)


def test_ai_rules_catalog_is_consistent() -> None:
    codes = [rule.code for rule in AI_RULES]

    assert len(codes) == len(set(codes))
    for rule in AI_RULES:
        assert rule.title
        assert rule.description
        assert rule.why_it_matters
        assert rule.recommendation
        assert rule.reference
