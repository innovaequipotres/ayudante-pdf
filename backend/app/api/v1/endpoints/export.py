"""Endpoint de exportación del PDF con los textos adaptados."""

from uuid import UUID

from fastapi import APIRouter, Depends, status
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.common import ErrorResponse
from app.schemas.export import ExportRequest
from app.services import export_service

router = APIRouter(prefix="/sessions/{session_id}", tags=["Export"])

_EXPORT_RESPONSES = {
    status.HTTP_200_OK: {
        "content": {"application/pdf": {}},
        "description": (
            "PDF con la misma cantidad de páginas que el original y la capa "
            "visual de reemplazo aplicada."
        ),
    },
    status.HTTP_404_NOT_FOUND: {
        "model": ErrorResponse,
        "description": "La sesión indicada no existe (`session_not_found`).",
    },
    status.HTTP_409_CONFLICT: {
        "model": ErrorResponse,
        "description": (
            "El contenido todavía no fue extraído (`content_not_extracted`) o "
            "la sesión no se creó desde un PDF (`export_unavailable`)."
        ),
    },
    status.HTTP_422_UNPROCESSABLE_CONTENT: {
        "model": ErrorResponse,
        "description": (
            "El bloque no existe (`unknown_block`), no tiene coordenadas "
            "(`block_without_bbox`), está repetido (`duplicate_block_id`), el "
            "texto está vacío (`empty_text`), supera los 8.000 caracteres "
            "(`text_too_long`) o el PDF no se puede leer (`invalid_pdf`)."
        ),
    },
}


@router.post(
    "/export",
    status_code=status.HTTP_200_OK,
    response_class=Response,
    summary="Aplicar los textos finales y exportar el PDF adaptado",
    responses=_EXPORT_RESPONSES,
)
def export_pdf(
    session_id: UUID, payload: ExportRequest, db: Session = Depends(get_db)
) -> Response:
    result = export_service.export_pdf(db, session_id, payload)
    return Response(
        content=result.content,
        media_type="application/pdf",
        headers={"Content-Disposition": result.content_disposition},
    )
