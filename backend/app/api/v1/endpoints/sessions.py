from uuid import UUID

from fastapi import APIRouter, File, UploadFile, status

from app.core.config import settings
from app.schemas.common import ErrorResponse
from app.schemas.session import SessionResponse, TextInput
from app.services import session_service

router = APIRouter(prefix="/sessions", tags=["Sessions"])

_FILE_RESPONSES = {
    status.HTTP_400_BAD_REQUEST: {
        "model": ErrorResponse,
        "description": (
            "Archivo vacío (`empty_content`) o archivo que no es un PDF real "
            "(`invalid_pdf`)."
        ),
    },
    status.HTTP_413_CONTENT_TOO_LARGE: {
        "model": ErrorResponse,
        "description": "El archivo supera el tamaño máximo permitido (`file_too_large`).",
    },
    status.HTTP_415_UNSUPPORTED_MEDIA_TYPE: {
        "model": ErrorResponse,
        "description": "La extensión del archivo no es `.pdf` (`unsupported_format`).",
    },
}

_TEXT_RESPONSES = {
    status.HTTP_400_BAD_REQUEST: {
        "model": ErrorResponse,
        "description": "El texto está vacío o solo contiene espacios (`empty_content`).",
    },
}

_SESSION_RESPONSES = {
    status.HTTP_404_NOT_FOUND: {
        "model": ErrorResponse,
        "description": "La sesión indicada no existe (`session_not_found`).",
    },
}


@router.post(
    "/file",
    response_model=SessionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Crear una sesión a partir de un archivo PDF",
    responses=_FILE_RESPONSES,
)
async def create_session_from_file(
    file: UploadFile = File(
        ...,
        description=f"Archivo PDF de hasta {settings.max_upload_mb} MB.",
    ),
) -> SessionResponse:
    content = await file.read()
    return session_service.create_from_file(file.filename or "", content)


@router.post(
    "/text",
    response_model=SessionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Crear una sesión a partir de un texto pegado",
    responses=_TEXT_RESPONSES,
)
def create_session_from_text(payload: TextInput) -> SessionResponse:
    return session_service.create_from_text(payload)


@router.get(
    "/{session_id}",
    response_model=SessionResponse,
    summary="Obtener una sesión por su identificador",
    responses=_SESSION_RESPONSES,
)
def get_session(session_id: UUID) -> SessionResponse:
    return session_service.get_session(session_id)
