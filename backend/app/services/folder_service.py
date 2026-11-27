"""Lógica de negocio de las carpetas de documentos."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.core.exceptions import AppError
from app.models.folder import Folder
from app.models.user import User
from app.schemas.folder import FolderCreate, FolderResponse, FolderUpdate

_SYSTEM_USER_EMAIL = "sessions@ayudante-pdf.local"


def _get_or_create_owner(db: Session) -> User:
    """Obtiene (o crea) el usuario sistema para el MVP."""
    user = db.query(User).filter(User.email == _SYSTEM_USER_EMAIL).first()
    if user is None:
        user = User(
            first_name="Sistema",
            last_name="Sesiones",
            email=_SYSTEM_USER_EMAIL,
            password_hash="!",
        )
        db.add(user)
        db.flush()
    return user


def _to_response(folder: Folder) -> FolderResponse:
    return FolderResponse(
        id=folder.id,
        owner_id=folder.owner_id,
        parent_id=folder.parent_id,
        name=folder.name,
        created_at=folder.created_at,
        updated_at=folder.updated_at,
    )


def _resolve_uuid(value: Any) -> UUID:
    if isinstance(value, UUID):
        return value
    return UUID(str(value))


def create_folder(*args: Any, **kwargs: Any) -> FolderResponse:
    """Crea una carpeta y la devuelve."""
    payload = kwargs.get("payload")
    db = kwargs.get("db")
    for item in args:
        if isinstance(item, FolderCreate) and payload is None:
            payload = item
        elif isinstance(item, Session) and db is None:
            db = item

    if payload is None:
        raise TypeError("create_folder requiere el payload.")

    owns = db is None
    if owns:
        db = SessionLocal()

    try:
        owner = _get_or_create_owner(db)

        # Validar que parent_id existe si se proporciona
        if payload.parent_id is not None:
            parent = db.get(Folder, payload.parent_id)
            if parent is None:
                raise AppError(
                    code="folder_not_found",
                    message="La carpeta padre indicada no existe.",
                    status_code=404,
                )
            # No permitir que el padre pertenezca a otro dueño
            if parent.owner_id != owner.id:
                raise AppError(
                    code="folder_not_found",
                    message="La carpeta padre indicada no existe.",
                    status_code=404,
                )

        folder = Folder(
            owner_id=owner.id,
            parent_id=payload.parent_id,
            name=payload.name,
        )
        db.add(folder)
        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            raise AppError(
                code="folder_name_conflict",
                message="Ya existe una carpeta con ese nombre en esta ubicación.",
                status_code=409,
            ) from None

        db.refresh(folder)
        return _to_response(folder)
    finally:
        if owns:
            db.close()


def list_folders(*args: Any, **kwargs: Any) -> list[FolderResponse]:
    """Lista todas las carpetas del usuario sistema (MVP)."""
    db = kwargs.get("db")
    for item in args:
        if isinstance(item, Session) and db is None:
            db = item

    owns = db is None
    if owns:
        db = SessionLocal()

    try:
        owner = _get_or_create_owner(db)
        folders = (
            db.query(Folder)
            .filter(Folder.owner_id == owner.id)
            .order_by(Folder.name)
            .all()
        )
        return [_to_response(folder) for folder in folders]
    finally:
        if owns:
            db.close()


def get_folder(*args: Any, **kwargs: Any) -> FolderResponse:
    """Obtiene una carpeta por su ID."""
    folder_id = kwargs.get("folder_id")
    db = kwargs.get("db")
    for item in args:
        if isinstance(item, UUID) and folder_id is None:
            folder_id = item
        elif isinstance(item, str) and folder_id is None:
            folder_id = item
        elif isinstance(item, Session) and db is None:
            db = item

    if folder_id is None:
        raise AppError(
            code="folder_not_found",
            message="La carpeta solicitada no existe.",
            status_code=404,
        )

    owns = db is None
    if owns:
        db = SessionLocal()

    try:
        folder = db.get(Folder, _resolve_uuid(folder_id))
        if folder is None:
            raise AppError(
                code="folder_not_found",
                message="La carpeta solicitada no existe.",
                status_code=404,
            )
        return _to_response(folder)
    finally:
        if owns:
            db.close()


def update_folder(*args: Any, **kwargs: Any) -> FolderResponse:
    """Actualiza el nombre o la carpeta padre de una carpeta."""
    folder_id = kwargs.get("folder_id")
    payload = kwargs.get("payload")
    db = kwargs.get("db")
    for item in args:
        if isinstance(item, UUID) and folder_id is None:
            folder_id = item
        elif isinstance(item, str) and folder_id is None:
            folder_id = item
        elif isinstance(item, FolderUpdate) and payload is None:
            payload = item
        elif isinstance(item, Session) and db is None:
            db = item

    if folder_id is None or payload is None:
        raise TypeError("update_folder requiere folder_id y payload.")

    owns = db is None
    if owns:
        db = SessionLocal()

    try:
        folder = db.get(Folder, _resolve_uuid(folder_id))
        if folder is None:
            raise AppError(
                code="folder_not_found",
                message="La carpeta solicitada no existe.",
                status_code=404,
            )

        # Validar nuevo parent_id si se proporciona
        if payload.parent_id is not None:
            new_parent = db.get(Folder, payload.parent_id)
            if new_parent is None:
                raise AppError(
                    code="folder_not_found",
                    message="La carpeta padre indicada no existe.",
                    status_code=404,
                )
            # No permitir mover una carpeta dentro de sí misma
            if new_parent.id == folder.id:
                raise AppError(
                    code="folder_cannot_be_own_parent",
                    message="Una carpeta no puede ser su propia padre.",
                    status_code=422,
                )
            # Validar que no sea un descendiente (evitar ciclos)
            current = new_parent
            while current is not None:
                if current.id == folder.id:
                    raise AppError(
                        code="folder_cannot_be_descendant",
                        message="No se puede mover una carpeta dentro de sí misma.",
                        status_code=422,
                    )
                current = db.get(Folder, current.parent_id)

        if payload.name is not None:
            folder.name = payload.name
        if payload.parent_id is not None:
            folder.parent_id = payload.parent_id

        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            raise AppError(
                code="folder_name_conflict",
                message="Ya existe una carpeta con ese nombre en esta ubicación.",
                status_code=409,
            ) from None

        db.refresh(folder)
        return _to_response(folder)
    finally:
        if owns:
            db.close()


def delete_folder(*args: Any, **kwargs: Any) -> None:
    """Elimina una carpeta. Los documentos pasan a raíz (folder_id=null)."""
    folder_id = kwargs.get("folder_id")
    db = kwargs.get("db")
    for item in args:
        if isinstance(item, UUID) and folder_id is None:
            folder_id = item
        elif isinstance(item, str) and folder_id is None:
            folder_id = item
        elif isinstance(item, Session) and db is None:
            db = item

    if folder_id is None:
        raise AppError(
            code="folder_not_found",
            message="La carpeta solicitada no existe.",
            status_code=404,
        )

    owns = db is None
    if owns:
        db = SessionLocal()

    try:
        folder = db.get(Folder, _resolve_uuid(folder_id))
        if folder is None:
            raise AppError(
                code="folder_not_found",
                message="La carpeta solicitada no existe.",
                status_code=404,
            )

        # Verificar que no tenga documentos (la issue dice 409)
        from app.models.document import Document

        has_documents = (
            db.query(Document)
            .filter(Document.folder_id == folder.id)
            .first()
            is not None
        )
        if has_documents:
            raise AppError(
                code="folder_has_documents",
                message="No se puede eliminar una carpeta que contiene documentos.",
                status_code=409,
            )

        db.delete(folder)
        db.commit()
    finally:
        if owns:
            db.close()