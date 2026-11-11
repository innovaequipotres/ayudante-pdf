"""Reglas automáticas de accesibilidad sobre el contenido extraído.

Las reglas trabajan sobre ``ExtractedContent`` y esperan los bloques
enriquecidos por ``content_service``: con ``id``, ``word_count`` y ``summary``
ya calculados. No hacen entrada/salida ni llamadas a la IA.

Umbrales
--------
Los valores de las constantes son propuestas iniciales. Solo el umbral de 300
palabras para un párrafo extenso viene del documento del proyecto; el resto
debe validarse con el equipo de Accesibilidad (BE-10). No son normas.
"""

from __future__ import annotations

import re
from collections.abc import Callable
from dataclasses import dataclass

from app.schemas.content import BlockType, ContentBlock, ExtractedContent
from app.schemas.observation import Category, Observation, Severity

__all__ = [
    "RULES",
    "RULES_BY_CODE",
    "Rule",
    "run_rules",
    "sort_observations",
    "split_sentences",
]

# --- Umbrales (a validar con Accesibilidad) ---
LONG_PARAGRAPH_WORDS_MEDIUM = 150
LONG_PARAGRAPH_WORDS_HIGH = 300
LONG_SENTENCE_WORDS_MEDIUM = 30
LONG_SENTENCE_WORDS_HIGH = 50
NO_HEADINGS_WORDS_MEDIUM = 150
NO_HEADINGS_WORDS_HIGH = 400
HEADING_SKIP_SEVERITY = Severity.LOW
EXCERPT_MAX_CHARS = 160

# Abreviaturas con más de un punto: se protegen todos sus puntos para no
# cortar la oración en medio de "EE. UU." o "p. ej.".
_MULTI_DOT_ABBREVIATION_RE = re.compile(
    r"(?i)\b(?:ee\.\s*uu|p\.\s*ej|a\.\s*c|d\.\s*c)\."
)
# Abreviaturas de un solo punto: se protege solo el punto final.
_ABBREVIATION_RE = re.compile(
    r"(?i)\b(?:dr|dra|sr|sra|lic|prof|ing|arq|etc|pág|núm|nro|art|cap|fig|ej"
    r"|aprox|máx|mín|av)\."
)
_DECIMAL_RE = re.compile(r"(?<=\d)\.(?=\d)")
_SENTENCE_END_RE = re.compile(
    r"(?<=[.!?…])\s+(?=[¿¡«\"'(]?[A-ZÁÉÍÓÚÜÑ0-9])"
)
_PROTECTED_DOT = "\u2024"  # punto que no debe cortar la oración


@dataclass(frozen=True)
class Rule:
    """Metadatos y verificador de una regla automática."""

    code: str
    category: Category
    title: str
    why_it_matters: str
    recommendation: str
    check: Callable[[ExtractedContent], list[Observation]]


def split_sentences(text: str) -> list[str]:
    """Divide un texto en oraciones.

    Es una heurística: protege abreviaturas y decimales frecuentes y solo corta
    cuando la oración siguiente empieza con mayúscula, número o signo de
    apertura. Puede fallar con usos poco habituales de los signos.
    """
    normalized = " ".join(text.split())
    if not normalized:
        return []

    protected = _MULTI_DOT_ABBREVIATION_RE.sub(
        lambda match: match.group(0).replace(".", _PROTECTED_DOT),
        normalized,
    )
    protected = _ABBREVIATION_RE.sub(
        lambda match: f"{match.group(0)[:-1]}{_PROTECTED_DOT}",
        protected,
    )
    protected = _DECIMAL_RE.sub(_PROTECTED_DOT, protected)

    return [
        part.replace(_PROTECTED_DOT, ".").strip()
        for part in _SENTENCE_END_RE.split(protected)
        if part.strip()
    ]


def _word_count(text: str) -> int:
    """Cuenta palabras separadas por espacios, igual que ``content_service``."""
    return len(text.split())


def _excerpt(text: str | None) -> str | None:
    """Recorta un fragmento sin cortar palabras."""
    if not text:
        return None
    normalized = " ".join(text.split())
    if len(normalized) <= EXCERPT_MAX_CHARS:
        return normalized
    cut = normalized[:EXCERPT_MAX_CHARS].rstrip()
    if " " in cut:
        cut = cut.rsplit(" ", 1)[0]
    return f"{cut}…"


def _texts(block: ContentBlock) -> list[str]:
    """Devuelve los textos que se escanean como oraciones."""
    if block.type is BlockType.PARAGRAPH and block.text:
        return [block.text]
    if block.type is BlockType.LIST and block.items:
        return block.items
    return []


def _first_text(block: ContentBlock) -> str | None:
    """Devuelve el primer texto del bloque, para usarlo como extracto."""
    if block.text:
        return block.text
    if block.items:
        return block.items[0]
    return None


def _observation(
    rule_id: str,
    severity: Severity,
    *,
    block: ContentBlock | None = None,
    page: int | None = None,
    excerpt: str | None = None,
    detail: str | None = None,
) -> Observation:
    """Arma una observación con los metadatos del catálogo."""
    rule = RULES_BY_CODE[rule_id]
    block_id = block.id if block is not None and block.id else None
    return Observation(
        id=f"{rule_id}:{block_id or 'documento'}",
        rule_id=rule_id,
        category=rule.category,
        severity=severity,
        title=rule.title,
        detail=detail,
        why_it_matters=rule.why_it_matters,
        recommendation=rule.recommendation,
        block_id=block_id,
        page=block.page if block is not None else page,
        excerpt=excerpt,
    )


# --- Reglas ---


def check_long_paragraph(content: ExtractedContent) -> list[Observation]:
    """Detecta párrafos que superan los umbrales de extensión."""
    found: list[Observation] = []
    for block in content.blocks:
        if block.type is not BlockType.PARAGRAPH:
            continue
        if block.word_count > LONG_PARAGRAPH_WORDS_HIGH:
            severity = Severity.HIGH
        elif block.word_count > LONG_PARAGRAPH_WORDS_MEDIUM:
            severity = Severity.MEDIUM
        else:
            continue
        found.append(
            _observation(
                "long_paragraph",
                severity,
                block=block,
                excerpt=_excerpt(block.text),
                detail=f"Tiene {block.word_count} palabras.",
            )
        )
    return found


def check_long_sentences(content: ExtractedContent) -> list[Observation]:
    """Detecta bloques con oraciones que superan los umbrales de extensión."""
    found: list[Observation] = []
    for block in content.blocks:
        sentences = [
            sentence
            for text in _texts(block)
            for sentence in split_sentences(text)
        ]
        long_sentences = [
            sentence
            for sentence in sentences
            if _word_count(sentence) > LONG_SENTENCE_WORDS_MEDIUM
        ]
        if not long_sentences:
            continue

        longest = max(long_sentences, key=_word_count)
        longest_words = _word_count(longest)
        severity = (
            Severity.HIGH
            if longest_words > LONG_SENTENCE_WORDS_HIGH
            else Severity.MEDIUM
        )
        if len(long_sentences) == 1:
            detail = (
                f"Una oración supera las {LONG_SENTENCE_WORDS_MEDIUM} palabras "
                f"y tiene {longest_words}."
            )
        else:
            detail = (
                f"{len(long_sentences)} oraciones superan las "
                f"{LONG_SENTENCE_WORDS_MEDIUM} palabras; la más larga tiene "
                f"{longest_words}."
            )
        found.append(
            _observation(
                "long_sentence",
                severity,
                block=block,
                excerpt=_excerpt(longest),
                detail=detail,
            )
        )
    return found


def check_no_headings(content: ExtractedContent) -> list[Observation]:
    """Detecta materiales extensos que no tienen ningún título."""
    if content.summary.heading_count > 0:
        return []
    if content.summary.word_count <= NO_HEADINGS_WORDS_MEDIUM:
        return []

    severity = (
        Severity.HIGH
        if content.summary.word_count > NO_HEADINGS_WORDS_HIGH
        else Severity.MEDIUM
    )
    anchor = next((block for block in content.blocks if _texts(block)), None)
    return [
        _observation(
            "no_headings",
            severity,
            block=anchor,
            excerpt=_excerpt(_first_text(anchor) if anchor is not None else None),
            detail=(
                f"El material tiene {content.summary.word_count} palabras y "
                "ningún título."
            ),
        )
    ]


def check_heading_skips(content: ExtractedContent) -> list[Observation]:
    """Detecta saltos de más de un nivel en la jerarquía de títulos."""
    found: list[Observation] = []
    previous_level: int | None = None
    for block in content.blocks:
        if block.type is not BlockType.HEADING or block.level is None:
            continue
        if previous_level is not None and block.level > previous_level + 1:
            found.append(
                _observation(
                    "heading_skip",
                    HEADING_SKIP_SEVERITY,
                    block=block,
                    excerpt=_excerpt(block.text),
                    detail=(
                        f"Pasa de un título de nivel {previous_level} a uno de "
                        f"nivel {block.level}."
                    ),
                )
            )
        previous_level = block.level
    return found


# Catálogo central: para sumar una regla alcanza con escribir su función y
# agregar una entrada acá. El resto del escáner no cambia.
RULES: tuple[Rule, ...] = (
    Rule(
        "long_paragraph",
        Category.COMPREHENSION,
        "Párrafo muy extenso",
        (
            "Los bloques de texto largos cansan y dificultan seguir la idea, "
            "sobre todo a quienes tienen dificultades de lectura o atención."
        ),
        "Dividir el párrafo en bloques más cortos, con una idea en cada uno.",
        check_long_paragraph,
    ),
    Rule(
        "long_sentence",
        Category.COMPREHENSION,
        "Oraciones muy largas",
        (
            "Las oraciones extensas obligan a retener muchas ideas a la vez y "
            "se entienden con más esfuerzo."
        ),
        "Reescribir con oraciones más breves, de una idea cada una.",
        check_long_sentences,
    ),
    Rule(
        "no_headings",
        Category.STRUCTURE,
        "El material no tiene títulos",
        (
            "Los títulos permiten ubicarse y saltar entre secciones; las "
            "personas que usan lector de pantalla navegan por ellos."
        ),
        "Organizar el contenido en secciones y ponerles títulos.",
        check_no_headings,
    ),
    Rule(
        "heading_skip",
        Category.STRUCTURE,
        "Salto en la jerarquía de títulos",
        (
            "Cuando se saltan niveles, la estructura se vuelve confusa para "
            "quien navega con tecnologías de asistencia."
        ),
        "Usar los niveles de título en orden, sin saltear ninguno.",
        check_heading_skips,
    ),
)

RULES_BY_CODE = {rule.code: rule for rule in RULES}


def sort_observations(
    observations: list[Observation],
    content: ExtractedContent,
) -> list[Observation]:
    """Ordena las observaciones por página y posición en el documento."""
    position = {block.id: index for index, block in enumerate(content.blocks)}
    observations.sort(
        key=lambda observation: (
            observation.page or 0,
            position.get(observation.block_id, -1),
        )
    )
    return observations


def run_rules(content: ExtractedContent) -> list[Observation]:
    """Ejecuta todas las reglas del catálogo sobre el contenido."""
    observations = [
        observation for rule in RULES for observation in rule.check(content)
    ]
    return sort_observations(observations, content)
