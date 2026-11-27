"""Frontera de almacenamiento de los PDFs de los documentos.

Este módulo es el único punto de la aplicación que conoce cómo se guardan los
bytes de un PDF. El resto del backend debe usar solamente estas tres
funciones, de modo que reemplazar PostgreSQL por Cloudflare R2 o Supabase
Storage implique reescribir únicamente este archivo.

Contrato
--------

``save_pdf(db, document_id, data) -> None``
    Guarda o reemplaza los bytes del PDF del documento ``document_id``. La
    clave es siempre el UUID del documento; el nombre original del archivo es
    un metadato de ``documents`` y no participa del almacenamiento. Si el
    documento no existe lanza ``DocumentNotFoundError``.

``read_pdf(db, document_id) -> bytes``
    Devuelve exactamente los bytes guardados. Si el documento no tiene un PDF
    (por ejemplo, es un texto pegado o no existe) lanza
    ``StoredFileNotFoundError``.

``delete_pdf(db, document_id) -> None``
    Elimina el PDF del documento. Es idempotente: si no hay PDF, no hace nada.
    No elimina el texto pegado de ``document_files.content_text``.

Las tres funciones hacen ``flush()`` y nunca ``commit()``: quien las llama
decide cuándo confirmar la transacción, para que el documento y su archivo se
guarden o se descarten juntos.

Los textos pegados viven en ``document_files.content_text`` y no pasan por
este módulo.
"""

from __future__ import annotations

from uuid import UUID

from sqlalchemy.orm import Session

from app.models.document import Document
from app.models.document_file import DocumentFile


class DocumentNotFoundError(LookupError):
    """No existe el documento indicado."""

    def __init__(self, document_id: UUID) -> None:
        self.document_id = document_id
        super().__init__(f"No existe el documento {document_id}.")


class StoredFileNotFoundError(LookupError):
    """El documento no tiene un PDF almacenado."""

    def __init__(self, document_id: UUID) -> None:
        self.document_id = document_id
        super().__init__(f"El documento {document_id} no tiene un PDF almacenado.")


def save_pdf(db: Session, document_id: UUID, data: bytes) -> None:
    """Guarda o reemplaza el PDF de un documento.

    Args:
        db: Sesión de SQLAlchemy controlada por quien llama.
        document_id: UUID del documento, única clave de almacenamiento.
        data: Bytes exactos del PDF.

    Raises:
        DocumentNotFoundError: Si no existe el documento.
    """
    document = db.get(Document, document_id)
    if document is None:
        raise DocumentNotFoundError(document_id)

    stored = db.get(DocumentFile, document_id)
    if stored is None:
        db.add(
            DocumentFile(
                document_id=document_id,
                owner_id=document.owner_id,
                content=data,
            )
        )
    else:
        stored.owner_id = document.owner_id
        stored.content = data
        # El CHECK exige exactamente uno de los dos contenidos. Si la fila
        # tenía texto pegado, el PDF lo reemplaza.
        stored.content_text = None

    db.flush()


def read_pdf(db: Session, document_id: UUID) -> bytes:
    """Devuelve los bytes exactos del PDF de un documento.

    Raises:
        StoredFileNotFoundError: Si el documento no existe o no tiene un PDF
            almacenado (por ejemplo, porque es un texto pegado).
    """
    stored = db.get(DocumentFile, document_id)
    data = stored.content if stored is not None else None
    if data is None:
        raise StoredFileNotFoundError(document_id)
    return data


def delete_pdf(db: Session, document_id: UUID) -> None:
    """Elimina el PDF de un documento; no falla si no existe.

    Solo borra filas cuyo contenido sea un PDF. Una fila de texto pegado
    (``content_text``) se conserva porque no hay PDF que eliminar.
    """
    stored = db.get(DocumentFile, document_id)
    if stored is not None and stored.content_text is None:
        db.delete(stored)

    db.flush()
