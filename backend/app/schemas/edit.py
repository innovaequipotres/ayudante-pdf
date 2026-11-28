"""Schemas de ediciones y estados de barreras."""

from enum import Enum

from pydantic import BaseModel, Field


class ObservationState(str, Enum):
    """Estado de una barrera después de la revisión del docente."""

    PENDING = "pending"
    APPLIED = "applied"
    IGNORED = "ignored"


class DocumentEdit(BaseModel):
    """Texto final de un bloque editado por el docente."""

    block_id: str = Field(
        description="Identificador del bloque (b1, b2, etc.).",
    )
    text: str = Field(
        description="Texto final del bloque.",
        min_length=1,
        max_length=8000,
    )


class ObservationStateItem(BaseModel):
    """Estado de una barrera específica."""

    observation_id: str = Field(
        description="Identificador de la observación.",
    )
    state: ObservationState = Field(
        description="Estado de la barrera: pending, applied o ignored.",
    )


class EditsPayload(BaseModel):
    """Payload para guardar ediciones y estados de un documento."""

    edits: list[DocumentEdit] = Field(
        default_factory=list,
        description="Lista de bloques editados.",
    )
    observation_states: list[ObservationStateItem] = Field(
        default_factory=list,
        description="Lista de estados de barreras.",
    )


class EditsResponse(BaseModel):
    """Respuesta con las ediciones y estados guardados."""

    document_id: str = Field(description="ID del documento.")
    edits: list[DocumentEdit] = Field(description="Ediciones guardadas.")
    observation_states: list[ObservationStateItem] = Field(
        description="Estados de barreras guardados."
    )