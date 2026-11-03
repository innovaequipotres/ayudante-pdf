"""Extracción heurística de contenido estructurado desde texto plano.

El procesador recorre las líneas del texto y las agrupa en títulos, listas y
párrafos. Es una heurística simple pensada para textos pegados por el docente,
no para Markdown completo.

Reglas
------
- **Títulos:** una línea que empieza con 1 a 6 ``#`` seguidos de espacio o
  tabulación. El nivel es la cantidad de ``#``.
- **Listas:** líneas consecutivas que empiezan con una viñeta o numeración
  (se reutiliza ``BULLET_RE`` del procesador de PDFs). Una línea siguiente que
  empieza con espacio o tabulación es continuación del ítem anterior.
- **Párrafos:** líneas no vacías consecutivas, unidas con un espacio. Una línea
  en blanco corta el párrafo.
- Los bloques de texto no tienen página y quedan sin identificador; esas etapas
  se completan en ``content_service``.
"""

from __future__ import annotations

import re

from app.processors.pdf_processor import BULLET_RE
from app.schemas.content import BlockType, ContentBlock

__all__ = ["extract_from_text"]

# Título: 1 a 6 "#" al inicio de la línea, seguidos de espacio o tabulación.
_HEADING_RE = re.compile(r"^(#{1,6})[ \t]+(.*)$")


def _normalize(text: str) -> str:
    """Colapsa espacios y tabulaciones en un único espacio."""
    return " ".join(text.split())


def extract_from_text(text: str) -> list[ContentBlock]:
    """Extrae los bloques de contenido de un texto plano.

    Args:
        text: Texto pegado por el docente.

    Returns:
        Los bloques en orden de lectura. Los títulos y párrafos usan ``text``;
        las listas usan ``items``. Todos quedan con ``page=None`` e ``id=""``.
    """
    blocks: list[ContentBlock] = []
    current_kind: BlockType | None = None
    current_level: int | None = None
    current_text: list[str] = []
    current_items: list[str] = []

    def flush() -> None:
        """Cierra el bloque abierto, si hay uno, y lo agrega a la salida."""
        nonlocal current_kind, current_level, current_text, current_items

        if current_kind is BlockType.HEADING:
            blocks.append(
                ContentBlock(
                    type=BlockType.HEADING,
                    text=" ".join(current_text),
                    level=current_level,
                )
            )
        elif current_kind is BlockType.LIST:
            blocks.append(
                ContentBlock(type=BlockType.LIST, items=list(current_items))
            )
        elif current_kind is BlockType.PARAGRAPH:
            blocks.append(
                ContentBlock(type=BlockType.PARAGRAPH, text=" ".join(current_text))
            )

        current_kind = None
        current_level = None
        current_text = []
        current_items = []

    for raw_line in text.splitlines():
        # Una línea en blanco corta cualquier bloque en curso.
        if not raw_line.strip():
            flush()
            continue

        heading = _HEADING_RE.match(raw_line)
        if heading is not None:
            flush()
            heading_text = _normalize(heading.group(2))
            if heading_text:
                current_kind = BlockType.HEADING
                current_level = len(heading.group(1))
                current_text = [heading_text]
            continue

        # La continuación por indentación tiene prioridad sobre una nueva
        # viñeta, de modo que las listas anidadas se aplanan en un solo bloque.
        if current_kind is BlockType.LIST and raw_line[:1] in (" ", "\t"):
            current_items[-1] = _normalize(f"{current_items[-1]} {raw_line}")
            continue

        bullet = BULLET_RE.match(raw_line)
        if bullet is not None:
            item = _normalize(raw_line[bullet.end() :])
            if current_kind is BlockType.LIST:
                if item:
                    current_items.append(item)
            else:
                flush()
                if item:
                    current_kind = BlockType.LIST
                    current_items = [item]
            continue

        line = raw_line.strip()
        if current_kind is BlockType.PARAGRAPH:
            current_text.append(line)
        else:
            flush()
            current_kind = BlockType.PARAGRAPH
            current_text = [line]

    flush()
    return blocks
