"""Endpoint de adaptación de barreras con IA."""

from fastapi import APIRouter, status

from app.scanner import adaptation
from app.schemas.adaptation import Adaptation, AdaptationRequest
from app.schemas.common import ErrorResponse

router = APIRouter(prefix="/adaptations", tags=["Adaptations"])

_ADAPT_RESPONSES = {
    status.HTTP_422_UNPROCESSABLE_CONTENT: {
        "model": ErrorResponse,
        "description": (
            "El texto supera los 8.000 caracteres (`text_too_long`), la "
            "barrera no se puede adaptar (`observation_not_adaptable`) o la "
            "regla no existe (`unknown_rule`)."
        ),
    },
}


@router.post(
    "",
    response_model=Adaptation,
    status_code=status.HTTP_200_OK,
    summary="Generar una versión adaptada de un texto",
    responses=_ADAPT_RESPONSES,
)
def adapt_text(payload: AdaptationRequest) -> Adaptation:
    return adaptation.adapt(payload)
