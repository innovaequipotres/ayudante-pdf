"""Endpoints de gestión de carpetas."""

from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.common import ErrorResponse
from app.schemas.folder import FolderCreate, FolderResponse, FolderUpdate
from app.services import folder_service

router = APIRouter(prefix="/folders", tags=["Folders"])

_FOLDERS_RESPONSES = {
    status.HTTP_404_NOT_FOUND: {
        "model": ErrorResponse,
        "description": "Carpeta no encontrada (`folder_not_found`).",
    },
    status.HTTP_409_CONFLICT: {
        "model": ErrorResponse,
        "description": "Nombre de carpeta duplicado (`folder_name_conflict`).",
    },
    status.HTTP_422_UNPROCESSABLE_CONTENT: {
        "model": ErrorResponse,
        "description": "Error de validación (`folder_cannot_be_own_parent`, `folder_cannot_be_descendant`).",
    },
}


@router.post(
    "",
    response_model=FolderResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Crear una carpeta",
    responses=_FOLDERS_RESPONSES,
)
def create_folder(
    payload: FolderCreate, db: Session = Depends(get_db)
) -> FolderResponse:
    return folder_service.create_folder(db, payload)


@router.get(
    "",
    response_model=list[FolderResponse],
    status_code=status.HTTP_200_OK,
    summary="Listar todas las carpetas",
)
def list_folders(db: Session = Depends(get_db)) -> list[FolderResponse]:
    return folder_service.list_folders(db)


@router.get(
    "/{folder_id}",
    response_model=FolderResponse,
    status_code=status.HTTP_200_OK,
    summary="Obtener una carpeta por su ID",
    responses=_FOLDERS_RESPONSES,
)
def get_folder(folder_id: UUID, db: Session = Depends(get_db)) -> FolderResponse:
    return folder_service.get_folder(db, folder_id)


@router.patch(
    "/{folder_id}",
    response_model=FolderResponse,
    status_code=status.HTTP_200_OK,
    summary="Actualizar nombre o carpeta padre",
    responses=_FOLDERS_RESPONSES,
)
def update_folder(
    folder_id: UUID,
    payload: FolderUpdate,
    db: Session = Depends(get_db),
) -> FolderResponse:
    return folder_service.update_folder(db, folder_id, payload)


@router.delete(
    "/{folder_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar una carpeta",
    responses={
        status.HTTP_409_CONFLICT: {
            "model": ErrorResponse,
            "description": "La carpeta contiene documentos (`folder_has_documents`).",
        },
        **_FOLDERS_RESPONSES,
    },
)
def delete_folder(folder_id: UUID, db: Session = Depends(get_db)) -> None:
    folder_service.delete_folder(db, folder_id)