"""Tests de las reglas automáticas de texto."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest

from app.scanner.rules import (
    EXCERPT_MAX_CHARS,
    HEADING_SKIP_SEVERITY,
    LONG_PARAGRAPH_WORDS_HIGH,
    LONG_PARAGRAPH_WORDS_MEDIUM,
    LONG_SENTENCE_WORDS_HIGH,
    LONG_SENTENCE_WORDS_MEDIUM,
    NO_HEADINGS_WORDS_HIGH,
    NO_HEADINGS_WORDS_MEDIUM,
    RULES,
    RULES_BY_CODE,
    run_rules,
    split_sentences,
)
from app.schemas.content import BlockType, ContentBlock, ExtractedContent
from app.schemas.observation import Category, Observation, ObservationSource, Severity
from app.schemas.session import SessionResponse, SessionStatus, SourceType
from app.services.content_service import build_content


def _words(count: int, word: str = "palabra") -> str:
    """Devuelve ``count`` palabras separadas por espacios."""
    return " ".join([word] * count)


def _sentence(count: int, word: str = "palabra") -> str:
    """Devuelve una oración de ``count`` palabras que empieza en mayúscula."""
    words = [word] * count
    words[0] = words[0].capitalize()
    return f"{' '.join(words)}."


def _content(
    blocks: list[ContentBlock],
    page_count: int | None = None,
) -> ExtractedContent:
    """Construye el contenido como lo hace ``content_service``."""
    session = SessionResponse(
        session_id=uuid4(),
        source_type=SourceType.PDF if page_count is not None else SourceType.TEXT,
        filename="Material de prueba",
        status=SessionStatus.UPLOADED,
        created_at=datetime.now(UTC),
    )
    return build_content(session, blocks, page_count)


def _by_rule(observations: list[Observation], rule_id: str) -> list[Observation]:
    return [
        observation
        for observation in observations
        if observation.rule_id == rule_id
    ]


@pytest.mark.parametrize(
    ("count", "expected"),
    [
        (LONG_PARAGRAPH_WORDS_MEDIUM, None),
        (LONG_PARAGRAPH_WORDS_MEDIUM + 1, Severity.MEDIUM),
        (LONG_PARAGRAPH_WORDS_HIGH, Severity.MEDIUM),
        (LONG_PARAGRAPH_WORDS_HIGH + 1, Severity.HIGH),
    ],
)
def test_long_paragraph_thresholds(
    count: int,
    expected: Severity | None,
) -> None:
    content = _content(
        [ContentBlock(type=BlockType.PARAGRAPH, text=f"{_words(count)}.")]
    )

    found = _by_rule(run_rules(content), "long_paragraph")

    if expected is None:
        assert found == []
    else:
        assert [observation.severity for observation in found] == [expected]


def test_long_paragraph_ignores_lists_and_headings() -> None:
    content = _content(
        [
            ContentBlock(type=BlockType.HEADING, level=1, text=_words(400)),
            ContentBlock(type=BlockType.LIST, items=[_words(400)]),
        ]
    )

    assert _by_rule(run_rules(content), "long_paragraph") == []


@pytest.mark.parametrize(
    ("count", "expected"),
    [
        (LONG_SENTENCE_WORDS_MEDIUM, None),
        (LONG_SENTENCE_WORDS_MEDIUM + 1, Severity.MEDIUM),
        (LONG_SENTENCE_WORDS_HIGH, Severity.MEDIUM),
        (LONG_SENTENCE_WORDS_HIGH + 1, Severity.HIGH),
    ],
)
def test_long_sentence_thresholds(
    count: int,
    expected: Severity | None,
) -> None:
    content = _content(
        [
            ContentBlock(
                type=BlockType.PARAGRAPH,
                text=_sentence(count, "oracion"),
            )
        ]
    )

    found = _by_rule(run_rules(content), "long_sentence")

    if expected is None:
        assert found == []
    else:
        assert [observation.severity for observation in found] == [expected]


def test_long_sentence_reports_the_longest_sentence_once() -> None:
    short = _sentence(35, "breve")
    long = _sentence(60, "extensa")
    content = _content(
        [ContentBlock(type=BlockType.PARAGRAPH, text=f"{short} {long}")]
    )

    found = _by_rule(run_rules(content), "long_sentence")

    assert len(found) == 1
    assert found[0].severity is Severity.HIGH
    assert "Extensa" in (found[0].excerpt or "")
    assert "2 oraciones" in (found[0].detail or "")
    assert "60" in (found[0].detail or "")


def test_long_sentence_scans_list_items() -> None:
    content = _content(
        [
            ContentBlock(
                type=BlockType.LIST,
                items=[_sentence(40, "item"), "Corto."],
            )
        ]
    )

    found = _by_rule(run_rules(content), "long_sentence")

    assert len(found) == 1
    assert found[0].severity is Severity.MEDIUM
    assert found[0].block_id == "b1"
    assert "Item" in (found[0].excerpt or "")


def test_long_sentence_ignores_headings() -> None:
    content = _content(
        [
            ContentBlock(
                type=BlockType.HEADING,
                level=1,
                text=_sentence(60, "titulo"),
            )
        ]
    )

    assert _by_rule(run_rules(content), "long_sentence") == []


@pytest.mark.parametrize(
    ("count", "expected"),
    [
        (NO_HEADINGS_WORDS_MEDIUM, None),
        (NO_HEADINGS_WORDS_MEDIUM + 1, Severity.MEDIUM),
        (NO_HEADINGS_WORDS_HIGH, Severity.MEDIUM),
        (NO_HEADINGS_WORDS_HIGH + 1, Severity.HIGH),
    ],
)
def test_no_headings_thresholds(
    count: int,
    expected: Severity | None,
) -> None:
    content = _content(
        [ContentBlock(type=BlockType.PARAGRAPH, text=f"{_words(count)}.")]
    )

    found = _by_rule(run_rules(content), "no_headings")

    if expected is None:
        assert found == []
    else:
        assert [observation.severity for observation in found] == [expected]
        assert found[0].block_id == "b1"
        assert found[0].page is None
        assert found[0].excerpt
        assert str(count) in (found[0].detail or "")


def test_no_headings_ignored_when_material_has_a_heading() -> None:
    content = _content(
        [
            ContentBlock(type=BlockType.HEADING, level=1, text="Sección"),
            ContentBlock(
                type=BlockType.PARAGRAPH,
                text=f"{_words(NO_HEADINGS_WORDS_HIGH + 1)}.",
            ),
        ]
    )

    assert _by_rule(run_rules(content), "no_headings") == []


def test_no_headings_anchors_first_text_block() -> None:
    content = _content(
        [
            ContentBlock(type=BlockType.IMAGE, page=1, width=100, height=100),
            ContentBlock(
                type=BlockType.PARAGRAPH,
                page=2,
                text=f"{_words(NO_HEADINGS_WORDS_MEDIUM + 1)}.",
            ),
        ],
        page_count=2,
    )

    found = _by_rule(run_rules(content), "no_headings")

    assert len(found) == 1
    assert found[0].block_id == "b2"
    assert found[0].page == 2
    assert (found[0].excerpt or "").startswith("palabra")


def test_heading_skip_detects_jumps_and_ignores_downs() -> None:
    content = _content(
        [
            ContentBlock(type=BlockType.HEADING, level=1, page=1, text="Nivel 1"),
            ContentBlock(type=BlockType.HEADING, level=3, page=1, text="Nivel 3"),
            ContentBlock(type=BlockType.HEADING, level=2, page=2, text="Nivel 2"),
            ContentBlock(type=BlockType.HEADING, level=5, page=2, text="Nivel 5"),
        ],
        page_count=2,
    )

    found = _by_rule(run_rules(content), "heading_skip")

    assert [observation.block_id for observation in found] == ["b2", "b4"]
    assert all(
        observation.severity is HEADING_SKIP_SEVERITY for observation in found
    )
    assert "nivel 1" in (found[0].detail or "")
    assert "nivel 3" in (found[0].detail or "")
    assert "nivel 2" in (found[1].detail or "")
    assert "nivel 5" in (found[1].detail or "")


def test_heading_skip_ignores_first_heading_level() -> None:
    content = _content(
        [
            ContentBlock(
                type=BlockType.HEADING,
                level=3,
                text="Empieza en tres",
            ),
            ContentBlock(
                type=BlockType.HEADING,
                level=4,
                text="Sigue en cuatro",
            ),
        ]
    )

    assert _by_rule(run_rules(content), "heading_skip") == []


def test_observation_includes_all_required_fields() -> None:
    content = _content(
        [
            ContentBlock(
                type=BlockType.PARAGRAPH,
                page=2,
                text=f"{_words(LONG_PARAGRAPH_WORDS_HIGH + 1)}.",
            )
        ],
        page_count=2,
    )

    observation = _by_rule(run_rules(content), "long_paragraph")[0]

    assert observation.id == "long_paragraph:b1"
    assert observation.rule_id == "long_paragraph"
    assert observation.category is Category.COMPREHENSION
    assert observation.severity is Severity.HIGH
    assert observation.source is ObservationSource.RULE
    assert observation.title
    assert observation.why_it_matters
    assert observation.recommendation
    assert observation.block_id == "b1"
    assert observation.page == 2
    assert observation.excerpt
    assert observation.detail == (
        f"Tiene {LONG_PARAGRAPH_WORDS_HIGH + 1} palabras."
    )


def test_observation_ids_are_unique_and_stable() -> None:
    content = _content(
        [
            ContentBlock(type=BlockType.HEADING, level=1, text="Título"),
            ContentBlock(
                type=BlockType.PARAGRAPH,
                text=f"{_words(LONG_PARAGRAPH_WORDS_HIGH + 1)}.",
            ),
            ContentBlock(type=BlockType.HEADING, level=3, text="Salto"),
        ]
    )

    first = run_rules(content)
    second = run_rules(content)

    assert len(first) == len({observation.id for observation in first})
    assert [observation.id for observation in first] == [
        observation.id for observation in second
    ]


def test_observations_are_sorted_by_page_and_position() -> None:
    content = _content(
        [
            ContentBlock(
                type=BlockType.PARAGRAPH,
                page=2,
                text=f"{_words(LONG_PARAGRAPH_WORDS_MEDIUM + 1)}.",
            ),
            ContentBlock(
                type=BlockType.PARAGRAPH,
                page=1,
                text=f"{_words(LONG_PARAGRAPH_WORDS_MEDIUM + 1)}.",
            ),
        ],
        page_count=2,
    )

    found = _by_rule(run_rules(content), "long_paragraph")

    assert [observation.page for observation in found] == [1, 2]
    assert [observation.block_id for observation in found] == ["b2", "b1"]


def test_rules_catalog_is_consistent() -> None:
    codes = [rule.code for rule in RULES]

    assert codes == [
        "long_paragraph",
        "long_sentence",
        "no_headings",
        "heading_skip",
    ]
    assert len(codes) == len(set(codes))
    assert set(RULES_BY_CODE) == set(codes)
    for rule in RULES:
        assert rule.category in (Category.COMPREHENSION, Category.STRUCTURE)
        assert rule.title
        assert rule.why_it_matters
        assert rule.recommendation
        assert callable(rule.check)


def test_excerpt_is_truncated_without_cutting_words() -> None:
    content = _content(
        [
            ContentBlock(
                type=BlockType.PARAGRAPH,
                text=f"{_words(LONG_PARAGRAPH_WORDS_HIGH + 1)}.",
            )
        ]
    )

    excerpt = _by_rule(run_rules(content), "long_paragraph")[0].excerpt or ""

    assert excerpt.endswith("…")
    assert len(excerpt) <= EXCERPT_MAX_CHARS + 1
    assert excerpt.removesuffix("…").endswith("palabra")


def test_split_sentences_handles_abbreviations() -> None:
    assert split_sentences("El Dr. Pérez explicó el tema. Luego hubo preguntas.") == [
        "El Dr. Pérez explicó el tema.",
        "Luego hubo preguntas.",
    ]


def test_split_sentences_handles_decimals_and_ellipsis() -> None:
    assert split_sentences("El valor es 3.14 y sube. Fin.") == [
        "El valor es 3.14 y sube.",
        "Fin.",
    ]
    assert split_sentences("Espera… luego sigue. Fin.") == [
        "Espera… luego sigue.",
        "Fin.",
    ]


def test_split_sentences_handles_multi_dot_abbreviations() -> None:
    assert split_sentences("Usá p. ej. este formato. Después seguí.") == [
        "Usá p. ej. este formato.",
        "Después seguí.",
    ]
    assert split_sentences("Viajó a EE. UU. en avión. Volvió después.") == [
        "Viajó a EE. UU. en avión.",
        "Volvió después.",
    ]
