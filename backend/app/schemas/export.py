"""Modelos de la exportación del PDF con los textos adaptados.

La exportación es stateless: recibe el texto final de uno o más bloques y
devuelve el PDF con una capa visual de reemplazo. No modifica la sesión ni
guarda los textos enviados.
"""

from __future__ import annotations

from pydantic import BaseModel, Field

__all__ = ["ExportEdit", "ExportRequest"]


class ExportEdit(BaseModel):
    """Texto final que se dibuja sobre un bloque del PDF."""

    block_id: str = Field(
        description="Identificador del bloque (``b1``, ``b2``, …).",
    )
    text: str = Field(
        description=(
            "Texto final del bloque. No puede quedar vacío después de quitar "
            "los espacios; máximo 8.000 caracteres."
        ),
        json_schema_extra={"maxLength": 8000},
    )


class ExportRequest(BaseModel):
    """Textos finales para aplicar sobre el PDF de una sesión.

    Los textos pueden venir de la IA, estar escritos a mano o ser una mezcla:
    el backend no distingue el origen. El límite y el texto no vacío se validan
    en el servicio para devolver ``text_too_long`` y ``empty_text``.
    """

    edits: list[ExportEdit] = Field(
        min_length=1,
        description="Textos finales de los bloques que se quieren reemplazar.",
    )
