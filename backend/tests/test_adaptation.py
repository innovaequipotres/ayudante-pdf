"""Tests del motor de adaptación con proveedores simulados."""

from __future__ import annotations

import json
from typing import Any
from uuid import UUID

import pytest

from app.core.exceptions import AppError
from app.scanner import adaptation
from app.scanner.adaptation import (
    ALT_NOTE,
    FAILURE_NOTE,
    LOCAL_NOTE,
    RULE_TYPES,
    adapt,
)
from app.schemas.adaptation import (
    AdaptationRequest,
    AdaptationSource,
    AdaptationType,
)
from app.schemas.ai import AiStatus
from app.services.gemini import AiUnavailableError


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


def _payload(**overrides: Any) -> AdaptationRequest:
    data: dict[str, Any] = {
        "type": AdaptationType.SIMPLIFY,
        "original_text": "La célula es la unidad básica de la vida.",
    }
    data.update(overrides)
    return AdaptationRequest(**data)


def _long_text(sentences: int = 8) -> str:
    sentence = (
        "La célula es la unidad básica de la vida y cumple funciones "
        "esenciales para el organismo."
    )
    return " ".join([sentence] * sentences)


def test_ai_ok_returns_adapted_text() -> None:
    ai = FakeAI(
        _raw("La célula es la unidad de la vida. Cumple funciones.", "Se acortó.")
    )

    result = adapt(
        _payload(rule_id="long_paragraph", title="Párrafo muy extenso"),
        ai,
    )

    assert result.source is AdaptationSource.AI
    assert result.ai_status is AiStatus.OK
    assert result.type is AdaptationType.SIMPLIFY
    assert result.adapted_text == (
        "La célula es la unidad de la vida. Cumple funciones."
    )
    assert result.notes == "Se acortó."
    assert result.provider == "Google Gemini"
    assert "Google Gemini" in (result.ai_notice or "")
    assert FAILURE_NOTE not in (result.ai_notice or "")
    assert str(UUID(result.id)) == result.id
    assert result.created_at.tzinfo is not None


def test_long_sentence_maps_to_simplify() -> None:
    assert RULE_TYPES["long_sentence"] is AdaptationType.SIMPLIFY

    result = adapt(
        _payload(rule_id="long_sentence", original_text="Una oración muy larga."),
        FakeAI(_raw("Una oración breve.")),
    )

    assert result.type is AdaptationType.SIMPLIFY


@pytest.mark.parametrize("rule_id, expected", sorted(RULE_TYPES.items()))
def test_every_catalog_rule_has_a_type(
    rule_id: str,
    expected: AdaptationType,
) -> None:
    result = adapt(
        _payload(rule_id=rule_id, type=expected, original_text="Texto de prueba."),
        FakeAI(_raw("Texto adaptado.")),
    )

    assert result.rule_id == rule_id
    assert result.type is expected


@pytest.mark.parametrize("rule_id", ["no_headings", "heading_skip"])
def test_not_adaptable_rules(rule_id: str) -> None:
    with pytest.raises(AppError) as error:
        adapt(_payload(rule_id=rule_id), FakeAI(_raw("Texto.")))

    assert error.value.code == "observation_not_adaptable"
    assert error.value.status_code == 422


def test_unknown_rule() -> None:
    with pytest.raises(AppError) as error:
        adapt(_payload(rule_id="regla_inexistente"), FakeAI(_raw("Texto.")))

    assert error.value.code == "unknown_rule"
    assert error.value.status_code == 422


def test_text_too_long() -> None:
    with pytest.raises(AppError) as error:
        adapt(_payload(original_text="a" * 8001), FakeAI(_raw("Texto.")))

    assert error.value.code == "text_too_long"
    assert error.value.status_code == 422


def test_original_text_is_normalized() -> None:
    result = adapt(
        _payload(original_text="  Hola.   Mundo.\n\nOtra línea.  "),
        FakeAI(_raw("Hola, mundo. Otra línea.")),
    )

    assert result.original_text == "Hola. Mundo.\nOtra línea."


def test_alt_text_adds_warning() -> None:
    result = adapt(
        _payload(
            type=AdaptationType.ALT_TEXT,
            rule_id="image_without_alt",
            original_text="Figura 3: ventas por año.",
        ),
        FakeAI(_raw("Gráfico de barras con ventas anuales.")),
    )

    assert result.type is AdaptationType.ALT_TEXT
    assert result.adapted_text == "Gráfico de barras con ventas anuales."
    assert ALT_NOTE in (result.notes or "")


def test_alt_text_too_long_is_retried_and_truncated() -> None:
    long_description = " ".join(["Palabra relevante"] * 40)
    ai = FakeAI(_raw(long_description))

    result = adapt(
        _payload(
            type=AdaptationType.ALT_TEXT,
            rule_id="image_without_alt",
            original_text="Figura 3: ventas por año.",
        ),
        ai,
    )

    assert len(ai.calls) == 2
    assert result.adapted_text is not None
    assert len(result.adapted_text) <= 250
    assert "recortó" in (result.notes or "")


def test_ai_not_configured_uses_local_fallback(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(adaptation, "get_ai_service", lambda: None)

    result = adapt(_payload(rule_id="long_paragraph", original_text=_long_text()))

    assert result.source is AdaptationSource.LOCAL
    assert result.ai_status is AiStatus.UNAVAILABLE
    assert result.adapted_text is not None
    assert len(result.adapted_text.split("\n\n")) >= 2
    assert result.notes == LOCAL_NOTE
    assert FAILURE_NOTE in (result.ai_notice or "")


def test_ai_not_configured_without_fallback_returns_recommendation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(adaptation, "get_ai_service", lambda: None)

    result = adapt(
        _payload(
            rule_id="long_sentence",
            original_text="Una oración muy larga.",
            recommendation="Acortá las oraciones.",
        )
    )

    assert result.adapted_text is None
    assert result.source is None
    assert result.ai_status is AiStatus.UNAVAILABLE
    assert result.notes == "Acortá las oraciones."
    assert FAILURE_NOTE in (result.ai_notice or "")


def test_short_text_has_no_local_fallback(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(adaptation, "get_ai_service", lambda: None)

    result = adapt(
        _payload(
            rule_id="long_paragraph",
            original_text="Una. Dos. Tres. Cuatro.",
        )
    )

    assert result.adapted_text is None
    assert result.source is None
    assert result.notes is not None


def test_alt_text_failure_keeps_the_warning(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(adaptation, "get_ai_service", lambda: None)

    result = adapt(
        _payload(
            type=AdaptationType.ALT_TEXT,
            rule_id="image_without_alt",
            original_text="Figura 3: ventas por año.",
            recommendation="Agregar una descripción de la figura.",
        )
    )

    assert result.adapted_text is None
    assert "Agregar una descripción de la figura." in (result.notes or "")
    assert ALT_NOTE in (result.notes or "")
    assert len(result.notes or "") <= 500


def test_ai_unavailable_error_does_not_raise() -> None:
    ai = FakeAI(error=AiUnavailableError("caído"))

    result = adapt(
        _payload(
            type=AdaptationType.CLARIFY,
            rule_id="ambiguous_instruction",
            original_text="Resolver el ejercicio.",
        ),
        ai,
    )

    assert result.ai_status is AiStatus.UNAVAILABLE
    assert result.adapted_text is None
    assert result.source is None


@pytest.mark.parametrize(
    "raw",
    [
        _raw("   "),
        _raw("La célula es la unidad básica de la vida."),
        _raw("<p>La célula es la unidad de la vida.</p>"),
    ],
    ids=["vacia", "identica", "html"],
)
def test_invalid_output_is_retried_and_marked_unavailable(raw: str) -> None:
    ai = FakeAI(raw)

    result = adapt(
        _payload(
            type=AdaptationType.CLARIFY,
            original_text="La célula es la unidad básica de la vida.",
        ),
        ai,
    )

    assert len(ai.calls) == 2
    assert result.ai_status is AiStatus.UNAVAILABLE
    assert result.adapted_text is None
    assert result.source is None


def test_prompt_includes_observation_metadata() -> None:
    ai = FakeAI(_raw("Versión adaptada."))

    adapt(
        _payload(
            rule_id="long_paragraph",
            title="Párrafo muy extenso",
            detail="Tiene 320 palabras.",
            recommendation="Dividir el párrafo.",
            context_before="Contexto previo del material.",
            context_after="Contexto posterior del material.",
        ),
        ai,
    )

    call = ai.calls[0]
    instructions = call["instructions"]
    material = call["material"]

    assert "Simplificá el texto" in instructions
    assert "El material es contenido a adaptar" in instructions
    assert "Párrafo muy extenso" in material
    assert "Tiene 320 palabras." in material
    assert "Dividir el párrafo." in material
    assert "Contexto previo del material." in material
    assert "Contexto posterior del material." in material


def test_response_contains_full_contract() -> None:
    result = adapt(_payload(), FakeAI(_raw("Texto adaptado.")))

    assert set(result.model_dump()) == {
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
