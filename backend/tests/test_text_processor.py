"""Tests del procesador de texto plano."""

from __future__ import annotations

import pytest

from app.processors.text_processor import extract_from_text
from app.schemas.content import BlockType


def test_extract_from_text_detects_all_block_types() -> None:
    text = (
        "# Tema\n"
        "\n"
        "La célula es la unidad\n"
        "básica de la vida.\n"
        "\n"
        "- Membrana\n"
        "- Citoplasma\n"
        "  con ribosomas\n"
        "\n"
        "Texto suelto."
    )

    blocks = extract_from_text(text)

    assert [block.type for block in blocks] == [
        BlockType.HEADING,
        BlockType.PARAGRAPH,
        BlockType.LIST,
        BlockType.PARAGRAPH,
    ]

    heading, paragraph_one, list_block, paragraph_two = blocks
    assert heading.text == "Tema"
    assert heading.level == 1
    assert paragraph_one.text == "La célula es la unidad básica de la vida."
    assert list_block.items == ["Membrana", "Citoplasma con ribosomas"]
    assert paragraph_two.text == "Texto suelto."


@pytest.mark.parametrize(
    ("line", "level"),
    [
        ("# Uno", 1),
        ("## Dos", 2),
        ("### Tres", 3),
        ("#### Cuatro", 4),
        ("##### Cinco", 5),
        ("###### Seis", 6),
    ],
)
def test_heading_levels(line: str, level: int) -> None:
    blocks = extract_from_text(line)

    assert len(blocks) == 1
    assert blocks[0].type == BlockType.HEADING
    assert blocks[0].level == level
    assert blocks[0].text == line.split(" ", 1)[1]


def test_lines_without_heading_separator_are_paragraphs() -> None:
    blocks = extract_from_text("#sin espacio\n####### Siete")

    assert [block.type for block in blocks] == [BlockType.PARAGRAPH]
    assert blocks[0].text == "#sin espacio ####### Siete"


def test_blank_line_cuts_paragraphs() -> None:
    blocks = extract_from_text("Primera línea\nsegunda línea\n\nOtro párrafo")

    assert [block.type for block in blocks] == [
        BlockType.PARAGRAPH,
        BlockType.PARAGRAPH,
    ]
    assert blocks[0].text == "Primera línea segunda línea"
    assert blocks[1].text == "Otro párrafo"


def test_blank_line_cuts_lists() -> None:
    blocks = extract_from_text("- Uno\n\n  Texto indentado")

    assert [block.type for block in blocks] == [
        BlockType.LIST,
        BlockType.PARAGRAPH,
    ]
    assert blocks[0].items == ["Uno"]
    assert blocks[1].text == "Texto indentado"


def test_nested_list_is_flattened_into_previous_item() -> None:
    blocks = extract_from_text("- Uno\n  - Subítem\n- Dos")

    assert len(blocks) == 1
    assert blocks[0].type == BlockType.LIST
    assert blocks[0].items == ["Uno - Subítem", "Dos"]


def test_text_blocks_have_no_page_and_no_id() -> None:
    blocks = extract_from_text("# Título\n\nPárrafo\n\n- Ítem")

    assert all(block.page is None for block in blocks)
    assert all(block.id == "" for block in blocks)
    assert all(block.word_count == 0 for block in blocks)


def test_empty_headings_and_markers_are_ignored() -> None:
    blocks = extract_from_text("# \n-\n\nTexto")

    assert len(blocks) == 1
    assert blocks[0].type == BlockType.PARAGRAPH
    assert blocks[0].text == "Texto"


def test_extracts_clean_material(clean_text: str) -> None:
    blocks = extract_from_text(clean_text)

    assert [block.type for block in blocks] == [
        BlockType.HEADING,
        BlockType.PARAGRAPH,
        BlockType.HEADING,
        BlockType.LIST,
        BlockType.PARAGRAPH,
    ]
    assert blocks[0].text == "La célula"
    assert blocks[2].text == "Partes de la célula"
    assert blocks[3].items == ["Membrana", "Citoplasma", "Núcleo"]


def test_extracts_problem_material_as_one_paragraph(problem_text: str) -> None:
    blocks = extract_from_text(problem_text)

    assert len(blocks) == 1
    assert blocks[0].type == BlockType.PARAGRAPH
    assert blocks[0].text is not None
    assert len(blocks[0].text.split()) > 150
    assert "#" not in blocks[0].text


def test_single_paragraph_is_returned_as_one_block() -> None:
    blocks = extract_from_text(
        "La célula es la unidad básica de la vida y cumple funciones vitales."
    )

    assert len(blocks) == 1
    assert blocks[0].type == BlockType.PARAGRAPH
    assert blocks[0].page is None


def test_empty_text_returns_no_blocks() -> None:
    assert extract_from_text("") == []
    assert extract_from_text("   \n\t\n") == []
