"""Lógica de negocio de los documentos de la biblioteca."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy import or_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.core.exceptions import AppError
from app.models.document import Document
from app.models.folder import Folder
from app.models.user import User
from app.schemas.document import DocumentListFilters, DocumentResponse, DocumentUpdate
from app.schemas.session import SessionStatus

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


def _to_response(document: Document) -> DocumentResponse:
    return DocumentResponse(
        id=document.id,
        owner_id=document.owner_id,
        folder_id=document.folder_id,
        source_type=document.source_type,
        filename=document.filename,
        size_bytes=document.size_bytes,
        status=document.status,
        created_at=document.created_at,
        updated_at=document.updated_at,
    )


def _resolve_uuid(value: Any) -> UUID:
    if isinstance(value, UUID):
        return value
    return UUID(str(value))


def list_documents(*args: Any, **kwargs: Any) -> list[DocumentResponse]:
    """Lista documentos del usuario sistema con filtros opcionales."""
    filters = kwargs.get("filters")
    db = kwargs.get("db")
    for item in args:
        if isinstance(item, DocumentListFilters) and filters is None:
            filters = item
        elif isinstance(item, Session) and db is None:
            db = item

    owns = db is None
    if owns:
        db = SessionLocal()

    try:
        owner = _get_or_create_owner(db)
        query = db.query(Document).filter(Document.owner_id == owner.id)

        if filters is not None:
            if filters.folder_id is not None:
                query = query.filter(Document.folder_id == filters.folder_id)
            if filters.status is not None:
                query = query.filter(Document.status == filters.status.value)
            if filters.q is not None and filters.q.strip():
                search = f"%{filters.q.strip().lower()}%"
                query = query.filter(
                    or_(
                        Document.filename.ilike(search),
                    )
                )

        documents = query.order_by(Document.created_at.desc()).all()
        return [_to_response(doc) for doc in documents]
    finally:
        if owns:
            db.close()


def get_document(*args: Any, **kwargs: Any) -> DocumentResponse:
    """Obtiene un documento por su ID."""
    document_id = kwargs.get("document_id")
    db = kwargs.get("db")
    for item in args:
        if isinstance(item, UUID) and document_id is None:
            document_id = item
        elif isinstance(item, str) and document_id is None:
            document_id = item
        elif isinstance(item, Session) and db is None:
            db = item

    if document_id is None:
        raise AppError(
            code="document_not_found",
            message="El documento solicitado no existe.",
            status_code=404,
        )

    owns = db is None
    if owns:
        db = SessionLocal()

    try:
        document = db.get(Document, _resolve_uuid(document_id))
        if document is None:
            raise AppError(
                code="document_not_found",
                message="El documento solicitado no existe.",
                status_code=404,
            )
        return _to_response(document)
    finally:
        if owns:
            db.close()


def update_document(*args: Any, **kwargs: Any) -> DocumentResponse:
    """Actualiza el nombre o la carpeta de un documento."""
    document_id = kwargs.get("document_id")
    payload = kwargs.get("payload")
    db = kwargs.get("db")
    for item in args:
        if isinstance(item, UUID) and document_id is None:
            document_id = item
        elif isinstance(item, str) and document_id is None:
            document_id = item
        elif isinstance(item, DocumentUpdate) and payload is None:
            payload = item
        elif isinstance(item, Session) and db is None:
            db = item

    if document_id is None or payload is None:
        raise TypeError("update_document requiere document_id y payload.")

    owns = db is None
    if owns:
        db = SessionLocal()

    try:
        document = db.get(Document, _resolve_uuid(document_id))
        if document is None:
            raise AppError(
                code="document_not_found",
                message="El documento solicitado no existe.",
                status_code=404,
            )

        # Validar nueva carpeta si se proporciona
        if payload.folder_id is not None:
            folder = db.get(Folder, payload.folder_id)
            if folder is None:
                raise AppError(
                    code="folder_not_found",
                    message="La carpeta indicada no existe.",
                    status_code=404,
                )

        if payload.filename is not None:
            document.filename = payload.filename
        if payload.folder_id is not None:
            document.folder_id = payload.folder_id

        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            raise AppError(
                code="document_update_conflict",
                message="No se pudo actualizar el documento.",
                status_code=409,
            ) from None

        db.refresh(document)
        return _to_response(document)
    finally:
        if owns:
            db.close()