"""Endpoints del diagnóstico de accesibilidad de una sesión."""

from uuid import UUID

from fastapi import APIRouter, Query, status

from app.schemas.common import ErrorResponse
from app.schemas.diagnosis import Diagnosis
from app.services import analysis_service

router = APIRouter(prefix="/sessions/{session_id}", tags=["Diagnosis"])

_ANALYZE_RESPONSES = {
    status.HTTP_404_NOT_FOUND: {
        "model": ErrorResponse,
        "description": "La sesión indicada no existe (`session_not_found`).",
    },
    status.HTTP_422_UNPROCESSABLE_CONTENT: {
        "model": ErrorResponse,
        "description": (
            "El material no tiene texto extraíble (`no_extractable_text`) o el "
            "PDF no se puede leer (`invalid_pdf`)."
        ),
    },
}

_DIAGNOSIS_RESPONSES = {
    status.HTTP_404_NOT_FOUND: {
        "model": ErrorResponse,
        "description": "La sesión indicada no existe (`session_not_found`).",
    },
    status.HTTP_409_CONFLICT: {
        "model": ErrorResponse,
        "description": (
            "La sesión todavía no fue analizada (`session_not_analyzed`)."
        ),
    },
}


@router.post(
    "/analyze",
    response_model=Diagnosis,
    status_code=status.HTTP_200_OK,
    summary="Analizar una sesión y generar su diagnóstico",
    responses=_ANALYZE_RESPONSES,
)
def analyze_session(
    session_id: UUID,
    use_ai: bool = Query(
        default=True,
        description=(
            "Si es `true`, complementa las reglas con el análisis semántico "
            "de la IA. Con `false` solo se ejecutan las reglas."
        ),
    ),
) -> Diagnosis:
    return analysis_service.analyze(session_id, use_ai)


@router.get(
    "/diagnosis",
    response_model=Diagnosis,
    status_code=status.HTTP_200_OK,
    summary="Obtener el diagnóstico guardado de una sesión",
    responses=_DIAGNOSIS_RESPONSES,
)
def get_diagnosis(session_id: UUID) -> Diagnosis:
    return analysis_service.get_diagnosis(session_id)
