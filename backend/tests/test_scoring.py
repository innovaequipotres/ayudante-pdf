"""Tests del puntaje y los niveles del diagnóstico."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest

from app.scanner.rules import run_rules
from app.scanner.scoring import (
    MAX_PENALTY_PER_RULE,
    SEVERITY_PENALTY,
    build_diagnosis,
    calculate_score,
    category_results,
    overall_level,
)
from app.schemas.content import BlockType, ContentBlock, ExtractedContent
from app.schemas.diagnosis import (
    DIAGNOSIS_CATEGORIES,
    SCORE_DISCLAIMER,
    DiagnosisLevel,
)
from app.schemas.observation import Category, Observation, Severity
from app.schemas.session import SessionResponse, SessionStatus, SourceType
from app.services.content_service import build_content


def _observation(
    rule_id: str = "long_paragraph",
    severity: Severity = Severity.HIGH,
    category: Category = Category.COMPREHENSION,
    block_id: str = "b1",
) -> Observation:
    """Construye una observación mínima para probar el cálculo."""
    return Observation(
        id=f"{rule_id}:{block_id}",
        rule_id=rule_id,
        category=category,
        severity=severity,
        title="Observación de prueba",
        why_it_matters="Importa para la prueba.",
        recommendation="Corregir el material.",
        block_id=block_id,
    )


def _content_with(blocks: list[ContentBlock]) -> ExtractedContent:
    """Construye el contenido como lo hace ``content_service``."""
    session = SessionResponse(
        session_id=uuid4(),
        source_type=SourceType.TEXT,
        filename="Material de prueba",
        status=SessionStatus.UPLOADED,
        created_at=datetime.now(UTC),
    )
    return build_content(session, blocks, None)


def test_material_without_observations_scores_100() -> None:
    diagnosis = build_diagnosis(uuid4(), [])

    assert diagnosis.score == 100
    assert diagnosis.level is DiagnosisLevel.OK
    assert diagnosis.observations == []
    assert len(diagnosis.categories) == len(DIAGNOSIS_CATEGORIES)


def test_rules_without_findings_score_100() -> None:
    content = _content_with(
        [
            ContentBlock(type=BlockType.HEADING, level=1, text="Título"),
            ContentBlock(type=BlockType.PARAGRAPH, text="Un texto breve."),
        ]
    )

    observations = run_rules(content)
    diagnosis = build_diagnosis(content.session_id, observations)

    assert observations == []
    assert diagnosis.score == 100
    assert diagnosis.level is DiagnosisLevel.OK


@pytest.mark.parametrize(
    ("severity", "expected_score"),
    [
        (Severity.HIGH, 90),
        (Severity.MEDIUM, 96),
        (Severity.LOW, 99),
    ],
)
def test_severity_penalties(
    severity: Severity,
    expected_score: int,
) -> None:
    assert calculate_score([_observation(severity=severity)]) == expected_score


def test_penalties_accumulate_across_rules() -> None:
    observations = [
        _observation("long_paragraph", Severity.HIGH),
        _observation("long_sentence", Severity.MEDIUM),
        _observation("heading_skip", Severity.LOW),
    ]

    assert calculate_score(observations) == 100 - (10 + 4 + 1)
    assert overall_level(observations) is DiagnosisLevel.BARRIER


def test_penalty_is_capped_per_rule() -> None:
    observations = [
        _observation("image_without_alt", Severity.HIGH, block_id=f"b{i}")
        for i in range(1, 5)
    ]

    assert calculate_score(observations) == 100 - MAX_PENALTY_PER_RULE


def test_cap_applies_to_each_rule_separately() -> None:
    observations = [
        _observation("image_without_alt", Severity.HIGH, block_id=f"i{i}")
        for i in range(1, 5)
    ] + [
        _observation("long_paragraph", Severity.HIGH, block_id=f"p{i}")
        for i in range(1, 5)
    ]

    assert calculate_score(observations) == 100 - (2 * MAX_PENALTY_PER_RULE)


def test_score_never_goes_below_zero() -> None:
    observations = [
        _observation(f"regla_{i}", Severity.HIGH) for i in range(1, 13)
    ]

    assert calculate_score(observations) == 0


@pytest.mark.parametrize(
    ("severities", "expected"),
    [
        ([], DiagnosisLevel.OK),
        ([Severity.LOW], DiagnosisLevel.REVIEW),
        ([Severity.MEDIUM], DiagnosisLevel.REVIEW),
        ([Severity.MEDIUM, Severity.LOW], DiagnosisLevel.REVIEW),
        ([Severity.HIGH, Severity.LOW], DiagnosisLevel.BARRIER),
    ],
)
def test_overall_level(
    severities: list[Severity],
    expected: DiagnosisLevel,
) -> None:
    observations = [
        _observation(severity=severity, block_id=f"b{i}")
        for i, severity in enumerate(severities, start=1)
    ]

    assert overall_level(observations) is expected


def test_category_results_always_include_all_categories() -> None:
    results = category_results([])

    assert [result.category for result in results] == list(DIAGNOSIS_CATEGORIES)
    assert len(results) == 6
    assert all(result.severity is DiagnosisLevel.OK for result in results)
    assert all(result.barrier_count == 0 for result in results)
    assert all(result.review_count == 0 for result in results)
    assert all(result.suggestion_count == 0 for result in results)


def test_category_results_group_by_category_and_severity() -> None:
    results = {
        result.category: result
        for result in category_results(
            [
                _observation(
                    "long_paragraph",
                    Severity.HIGH,
                    Category.COMPREHENSION,
                ),
                _observation(
                    "long_sentence",
                    Severity.MEDIUM,
                    Category.COMPREHENSION,
                ),
                _observation(
                    "heading_skip",
                    Severity.LOW,
                    Category.STRUCTURE,
                ),
                _observation(
                    "image_without_alt",
                    Severity.HIGH,
                    Category.VISUAL,
                ),
            ]
        )
    }

    comprehension = results[Category.COMPREHENSION]
    assert comprehension.severity is DiagnosisLevel.BARRIER
    assert comprehension.barrier_count == 1
    assert comprehension.review_count == 1
    assert comprehension.suggestion_count == 0

    structure = results[Category.STRUCTURE]
    assert structure.severity is DiagnosisLevel.REVIEW
    assert structure.barrier_count == 0
    assert structure.review_count == 0
    assert structure.suggestion_count == 1

    visual = results[Category.VISUAL]
    assert visual.severity is DiagnosisLevel.BARRIER
    assert visual.barrier_count == 1

    for category in (
        Category.REPRESENTATION,
        Category.MULTIMEDIA,
        Category.NAVIGATION,
    ):
        assert results[category].severity is DiagnosisLevel.OK


def test_build_diagnosis_includes_disclaimer_and_metadata() -> None:
    session_id = uuid4()
    observations = [_observation(severity=Severity.HIGH)]

    diagnosis = build_diagnosis(session_id, observations)

    assert diagnosis.session_id == session_id
    assert diagnosis.score == 90
    assert diagnosis.level is DiagnosisLevel.BARRIER
    assert diagnosis.disclaimer == SCORE_DISCLAIMER
    assert "orientativo" in diagnosis.disclaimer
    assert "certificación" in diagnosis.disclaimer
    assert diagnosis.observations == observations
    assert diagnosis.created_at.tzinfo is not None


def test_diagnosis_uses_disclaimer_by_default() -> None:
    diagnosis = build_diagnosis(uuid4(), [])

    assert diagnosis.disclaimer == SCORE_DISCLAIMER


def test_penalties_cover_every_severity() -> None:
    assert set(SEVERITY_PENALTY) == set(Severity)
    assert all(penalty > 0 for penalty in SEVERITY_PENALTY.values())
