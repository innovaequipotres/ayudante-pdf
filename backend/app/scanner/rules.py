"""Reglas automáticas de accesibilidad sobre el contenido extraído.

Las reglas trabajan sobre ``ExtractedContent`` y esperan los bloques
enriquecidos por ``content_service``: con ``id``, ``word_count`` y ``summary``
ya calculados. No hacen entrada/salida ni llamadas a la IA.

Umbrales
--------
Los valores de las constantes son propuestas iniciales. Solo el umbral de 300
palabras para un párrafo extenso viene del documento del proyecto; el resto
son decisiones del equipo a calibrar con Accesibilidad. No son normas. El
detalle de fuentes y estados está en ``docs/accessibility-criteria.md``.

Límites de las reglas visuales
------------------------------
- **Texto alternativo en PDF:** ``pdfplumber`` no expone el texto alternativo,
  así que ``pdf_processor`` deja ``alt_text`` en ``None`` y toda imagen de un
  PDF se marca como si no tuviera descripción. Puede ser un falso positivo; la
  observación lo aclara y conviene revisar la imagen antes de descartarla.
- **Contenido de las imágenes:** no se analiza el contraste ni lo que muestra
  la imagen, solo su presencia, tamaño y posición.
"""

from __future__ import annotations

import re
from collections import defaultdict
from collections.abc import Callable
from dataclasses import dataclass

from app.schemas.content import BlockType, ContentBlock, ExtractedContent
from app.schemas.observation import Category, Observation, Severity
from app.schemas.session import SourceType

__all__ = [
    "RULES",
    "RULES_BY_CODE",
    "Rule",
    "run_rules",
    "sort_observations",
    "split_sentences",
]

# --- Umbrales (propuestas del equipo, ver docs/accessibility-criteria.md) ---
LONG_PARAGRAPH_WORDS_MEDIUM = 150
LONG_PARAGRAPH_WORDS_HIGH = 300
LONG_SENTENCE_WORDS_MEDIUM = 30
LONG_SENTENCE_WORDS_HIGH = 50
NO_HEADINGS_WORDS_MEDIUM = 150
NO_HEADINGS_WORDS_HIGH = 400
HEADING_SKIP_SEVERITY = Severity.LOW
EXCERPT_MAX_CHARS = 160
IMAGE_ONLY_PAGE_MAX_WORDS = 15
IMAGE_WITHOUT_ALT_SEVERITY = Severity.HIGH
IMAGE_ONLY_PAGE_SEVERITY = Severity.MEDIUM

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
    """Metadatos y verificador de una regla automática.

    ``reference`` cita la fuente del criterio o indica que se trata de una
    decisión del equipo. La documentación completa está en
    ``docs/accessibility-criteria.md``.
    """

    code: str
    category: Category
    title: str
    why_it_matters: str
    recommendation: str
    check: Callable[[ExtractedContent], list[Observation]]
    reference: str


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
    key: str | None = None,
) -> Observation:
    """Arma una observación con los metadatos del catálogo.

    ``key`` identifica las observaciones que afectan a una página completa y no
    a un bloque, para que sus identificadores no se repitan.
    """
    rule = RULES_BY_CODE[rule_id]
    block_id = block.id if block is not None and block.id else None
    subject = block_id or key or "documento"
    return Observation(
        id=f"{rule_id}:{subject}",
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


def check_images_without_alt(content: ExtractedContent) -> list[Observation]:
    """Detecta imágenes sin texto alternativo, una observación por imagen."""
    found: list[Observation] = []
    for block in content.blocks:
        if block.type is not BlockType.IMAGE:
            continue
        if (block.alt_text or "").strip():
            continue

        detail = None
        if block.page is not None:
            detail = f"Está en la página {block.page}."
        if content.source_type is SourceType.PDF:
            note = (
                "En un PDF no se puede leer el texto alternativo original: "
                "la imagen podría tenerlo y aun así marcarse."
            )
            detail = f"{detail} {note}" if detail else note

        found.append(
            _observation(
                "image_without_alt",
                IMAGE_WITHOUT_ALT_SEVERITY,
                block=block,
                detail=detail,
            )
        )
    return found


def check_image_only_pages(
    content: ExtractedContent,
    max_words: int = IMAGE_ONLY_PAGE_MAX_WORDS,
) -> list[Observation]:
    """Detecta páginas con imágenes y poco texto.

    ``max_words`` permite ajustar el umbral; por defecto usa
    ``IMAGE_ONLY_PAGE_MAX_WORDS``.
    """
    words: dict[int, int] = defaultdict(int)
    images: dict[int, int] = defaultdict(int)
    for block in content.blocks:
        if block.page is None:
            continue
        if block.type is BlockType.IMAGE:
            images[block.page] += 1
        else:
            words[block.page] += block.word_count

    found: list[Observation] = []
    for page, image_count in sorted(images.items()):
        if words[page] > max_words:
            continue
        noun = "imagen" if image_count == 1 else "imágenes"
        found.append(
            _observation(
                "image_only_page",
                IMAGE_ONLY_PAGE_SEVERITY,
                page=page,
                key=f"pagina-{page}",
                detail=(
                    f"La página {page} tiene {words[page]} palabras y "
                    f"{image_count} {noun}."
                ),
            )
        )
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
        reference=(
            "Documento del proyecto (300 palabras); decisión del equipo (150 "
            "palabras). Relacionado: WCAG 2.2 3.1.5 (AAA), ISO 24495-1 y UNE "
            "153101."
        ),
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
        reference=(
            "Decisión del equipo. Relacionado: WCAG 2.2 3.1.5 (AAA) y UNE "
            "153101."
        ),
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
        reference=(
            "Decisión del equipo. Relacionado: WCAG 2.2 1.3.1 (A), 2.4.6 (AA) "
            "y 2.4.10 (AAA)."
        ),
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
        reference=(
            "PDF/UA-1 (ISO 14289-1) 7.4.2, test 1. Relacionado: WCAG 2.2 "
            "1.3.1 (A) y 2.4.6 (AA)."
        ),
    ),
    Rule(
        "image_without_alt",
        Category.VISUAL,
        "Imagen sin descripción",
        (
            "La información visual puede no estar disponible para quienes usan "
            "lectores de pantalla."
        ),
        (
            "Incorporar un texto alternativo que describa la información "
            "relevante de la imagen."
        ),
        check_images_without_alt,
        reference=(
            "WCAG 2.2 1.1.1 Non-text Content (A) y PDF/UA-1 (ISO 14289-1) "
            "7.3, test 1."
        ),
    ),
    Rule(
        "image_only_page",
        Category.VISUAL,
        "Página con poco texto y con imágenes",
        (
            "Si la información está solo en imágenes, no llega a quienes no "
            "pueden verlas."
        ),
        (
            "Revisar que el contenido de las imágenes también esté explicado "
            "con texto."
        ),
        check_image_only_pages,
        reference=(
            "Decisión del equipo. Relacionado: WCAG 2.2 1.1.1 (A) y 1.4.5 "
            "Images of Text (AA)."
        ),
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
