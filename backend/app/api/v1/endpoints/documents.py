"""Endpoints de gestión de documentos."""

from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.common import ErrorResponse
from app.schemas.document import DocumentListFilters, DocumentResponse, DocumentUpdate
from app.services import document_service

router = APIRouter(prefix="/documents", tags=["Documents"])

_DOCUMENTS_RESPONSES = {
    status.HTTP_404_NOT_FOUND: {
        "model": ErrorResponse,
        "description": "Documento o carpeta no encontrada (`document_not_found`, `folder_not_found`).",
    },
    status.HTTP_409_CONFLICT: {
        "model": ErrorResponse,
        "description": "Conflicto al actualizar (`document_update_conflict`).",
    },
}


@router.get(
    "",
    response_model=list[DocumentResponse],
    status_code=status.HTTP_200_OK,
    summary="Listar documentos con filtros opcionales",
)
def list_documents(
    filters: DocumentListFilters = Depends(),
    db: Session = Depends(get_db),
) -> list[DocumentResponse]:
    return document_service.list_documents(db, filters)


@router.get(
    "/{document_id}",
    response_model=DocumentResponse,
    status_code=status.HTTP_200_OK,
    summary="Obtener un documento por su ID",
    responses=_DOCUMENTS_RESPONSES,
)
def get_document(document_id: UUID, db: Session = Depends(get_db)) -> DocumentResponse:
    return document_service.get_document(db, document_id)


@router.patch(
    "/{document_id}",
    response_model=DocumentResponse,
    status_code=status.HTTP_200_OK,
    summary="Actualizar nombre o carpeta de un documento",
    responses=_DOCUMENTS_RESPONSES,
)
def update_document(
    document_id: UUID,
    payload: DocumentUpdate,
    db: Session = Depends(get_db),
) -> DocumentResponse:
    return document_service.update_document(db, document_id, payload)