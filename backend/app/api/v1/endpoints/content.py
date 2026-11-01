from uuid import UUID

from fastapi import APIRouter, status

from app.schemas.common import ErrorResponse
from app.schemas.content import ExtractedContent
from app.services import content_service

router = APIRouter(prefix="/sessions/{session_id}", tags=["Content"])

_EXTRACT_RESPONSES = {
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

_CONTENT_RESPONSES = {
    status.HTTP_404_NOT_FOUND: {
        "model": ErrorResponse,
        "description": "La sesión indicada no existe (`session_not_found`).",
    },
    status.HTTP_409_CONFLICT: {
        "model": ErrorResponse,
        "description": (
            "El contenido todavía no fue extraído (`content_not_extracted`)."
        ),
    },
}


@router.post(
    "/extract",
    response_model=ExtractedContent,
    status_code=status.HTTP_200_OK,
    summary="Extraer el contenido de una sesión",
    responses=_EXTRACT_RESPONSES,
)
def extract_content(session_id: UUID) -> ExtractedContent:
    return content_service.extract(session_id)


@router.get(
    "/content",
    response_model=ExtractedContent,
    status_code=status.HTTP_200_OK,
    summary="Obtener el contenido extraído de una sesión",
    responses=_CONTENT_RESPONSES,
)
def get_content(session_id: UUID) -> ExtractedContent:
    return content_service.get_content(session_id)
