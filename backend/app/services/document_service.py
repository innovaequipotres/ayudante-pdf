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
from app.models.document_edit import DocumentEdit
from app.models.observation_state import ObservationStateRecord
from app.schemas.edit import (
    DocumentEdit as DocumentEditSchema,
    EditsPayload,
    EditsResponse,
    ObservationStateItem,
)
from app.models.extracted_content import ExtractedContentRecord
from app.models.diagnosis import DiagnosisRecord
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

def save_edits(*args: Any, **kwargs: Any) -> EditsResponse:
    """Guarda (reemplaza) las ediciones y estados de un documento.

    Valida que cada block_id exista en el contenido extraído y cada
    observation_id exista en el diagnóstico. Cambia el estado del documento
    a 'editing' sin tocar el contenido original.
    """
    document_id = kwargs.get("document_id")
    payload = kwargs.get("payload")
    db = kwargs.get("db")
    for item in args:
        if isinstance(item, UUID) and document_id is None:
            document_id = item
        elif isinstance(item, str) and document_id is None:
            document_id = item
        elif isinstance(item, EditsPayload) and payload is None:
            payload = item
        elif isinstance(item, Session) and db is None:
            db = item

    if document_id is None or payload is None:
        raise TypeError("save_edits requiere document_id y payload.")

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

        # Validar block_ids contra el contenido extraído. Si todavía no hay
        # contenido extraído, ningún block_id es válido.
        extracted = db.get(ExtractedContentRecord, document.id)
        valid_block_ids = (
            {block["id"] for block in extracted.payload.get("blocks", [])}
            if extracted is not None
            else set()
        )
        for edit in payload.edits:
            if edit.block_id not in valid_block_ids:
                raise AppError(
                    code="invalid_block_id",
                    message=f"El bloque '{edit.block_id}' no existe en el contenido extraído.",
                    status_code=422,
                )

        # Igual con las observaciones: sin diagnóstico, ningún id es válido.
        diagnosis = db.get(DiagnosisRecord, document.id)
        valid_observation_ids = (
            {obs["id"] for obs in diagnosis.payload.get("observations", [])}
            if diagnosis is not None
            else set()
        )
        for state in payload.observation_states:
            if state.observation_id not in valid_observation_ids:
                raise AppError(
                    code="invalid_observation_id",
                    message=f"La observación '{state.observation_id}' no existe en el diagnóstico.",
                    status_code=422,
                )

        # Reemplazar ediciones (DELETE + INSERT)
        db.query(DocumentEdit).filter(DocumentEdit.document_id == document.id).delete()
        for edit in payload.edits:
            db.add(
                DocumentEdit(
                    document_id=document.id,
                    owner_id=document.owner_id,
                    block_id=edit.block_id,
                    text=edit.text,
                )
            )

        # Reemplazar estados (DELETE + INSERT)
        db.query(ObservationStateRecord).filter(
            ObservationStateRecord.document_id == document.id
        ).delete()
        for state in payload.observation_states:
            db.add(
                ObservationStateRecord(
                    document_id=document.id,
                    owner_id=document.owner_id,
                    observation_id=state.observation_id,
                    state=state.state.value,
                )
            )

        # Cambiar estado del documento a 'editing'
        if document.status != "completed":
            document.status = "editing"

        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            raise AppError(
                code="edit_save_conflict",
                message="No se pudieron guardar las ediciones.",
                status_code=409,
            ) from None

        db.refresh(document)

        return EditsResponse(
            document_id=str(document.id),
            edits=[
                DocumentEditSchema(block_id=e.block_id, text=e.text)
                for e in db.query(DocumentEdit)
                .filter(DocumentEdit.document_id == document.id)
                .all()
            ],
            observation_states=[
                ObservationStateItem(
                    observation_id=s.observation_id, state=s.state
                )
                for s in db.query(ObservationStateRecord)
                .filter(ObservationStateRecord.document_id == document.id)
                .all()
            ],
        )
    except Exception:
        if owns:
            db.rollback()
        raise
    finally:
        if owns:
            db.close()


def get_edits(*args: Any, **kwargs: Any) -> EditsResponse:
    """Devuelve las ediciones y estados guardados de un documento."""
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

        edits = (
            db.query(DocumentEdit)
            .filter(DocumentEdit.document_id == document.id)
            .all()
        )
        states = (
            db.query(ObservationStateRecord)
            .filter(ObservationStateRecord.document_id == document.id)
            .all()
        )

        return EditsResponse(
            document_id=str(document.id),
            edits=[
                DocumentEditSchema(block_id=e.block_id, text=e.text) for e in edits
            ],
            observation_states=[
                ObservationStateItem(observation_id=s.observation_id, state=s.state)
                for s in states
            ],
        )
    finally:
        if owns:
            db.close()