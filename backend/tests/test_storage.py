import hashlib
import re
import uuid
from collections.abc import Iterator
from contextlib import contextmanager
from io import BytesIO

import pytest
from reportlab.pdfgen import canvas
from sqlalchemy import event, func, inspect, select

from app.models.document import Document
from app.models.document_file import DocumentFile
from app.models.user import User
from app.schemas.session import SourceType
from app.services.storage import (
    DocumentNotFoundError,
    StoredFileNotFoundError,
    delete_pdf,
    read_pdf,
    save_pdf,
)

_CONTENT_COLUMN = re.compile(r"document_files\.content(?!_text)")


def _create_user(db_session, email: str | None = None) -> User:
    user = User(
        first_name="Docente",
        last_name="Demo",
        email=email or f"docente-{uuid.uuid4()}@example.com",
        password_hash="hash-de-prueba",
    )
    db_session.add(user)
    db_session.commit()
    return user


def _create_document(
    db_session,
    owner: User,
    *,
    filename: str | None = "material.pdf",
    source_type: str = SourceType.PDF.value,
    size_bytes: int = 0,
) -> Document:
    document = Document(
        owner_id=owner.id,
        source_type=source_type,
        filename=filename,
        size_bytes=size_bytes,
    )
    db_session.add(document)
    db_session.commit()
    return document


def _make_pdf(text: str) -> bytes:
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer)
    pdf.drawString(72, 720, text)
    pdf.save()
    return buffer.getvalue()


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _count_files(db_session, document_id: uuid.UUID) -> int:
    return db_session.execute(
        select(func.count())
        .select_from(DocumentFile)
        .where(DocumentFile.document_id == document_id)
    ).scalar_one()


@contextmanager
def _capture_sql(db_session) -> Iterator[list[str]]:
    statements: list[str] = []

    def listener(conn, cursor, statement, parameters, context, executemany):
        statements.append(statement)

    bind = db_session.get_bind()
    event.listen(bind, "before_cursor_execute", listener)
    try:
        yield statements
    finally:
        event.remove(bind, "before_cursor_execute", listener)


def test_round_trip_preserves_sha256(db_session):
    owner = _create_user(db_session)
    document = _create_document(db_session, owner)
    original = _make_pdf("Material de prueba")

    save_pdf(db_session, document.id, original)
    db_session.commit()

    retrieved = read_pdf(db_session, document.id)

    assert retrieved == original
    assert _sha256(retrieved) == _sha256(original)


def test_save_replaces_existing_file_without_duplicating_rows(db_session):
    owner = _create_user(db_session)
    document = _create_document(db_session, owner)
    first = _make_pdf("Primera versión")
    second = _make_pdf("Segunda versión")

    save_pdf(db_session, document.id, first)
    save_pdf(db_session, document.id, second)

    assert _count_files(db_session, document.id) == 1
    assert read_pdf(db_session, document.id) == second


def test_documents_are_isolated(db_session):
    owner = _create_user(db_session)
    first_document = _create_document(db_session, owner)
    second_document = _create_document(db_session, owner)
    first_pdf = _make_pdf("Documento uno")
    second_pdf = _make_pdf("Documento dos")

    save_pdf(db_session, first_document.id, first_pdf)
    save_pdf(db_session, second_document.id, second_pdf)

    assert read_pdf(db_session, first_document.id) == first_pdf
    assert read_pdf(db_session, second_document.id) == second_pdf
    assert _count_files(db_session, first_document.id) == 1
    assert _count_files(db_session, second_document.id) == 1


def test_storage_key_is_document_uuid_not_filename(db_session):
    owner = _create_user(db_session)
    first_document = _create_document(db_session, owner, filename="material.pdf")
    second_document = _create_document(db_session, owner, filename="material.pdf")
    first_pdf = _make_pdf("Mismo nombre, primer contenido")
    second_pdf = _make_pdf("Mismo nombre, segundo contenido")

    save_pdf(db_session, first_document.id, first_pdf)
    save_pdf(db_session, second_document.id, second_pdf)

    assert read_pdf(db_session, first_document.id) == first_pdf
    assert read_pdf(db_session, second_document.id) == second_pdf
    assert _count_files(db_session, first_document.id) == 1
    assert _count_files(db_session, second_document.id) == 1


def test_listing_does_not_load_content(db_session, pdf_content):
    owner = _create_user(db_session)
    document = _create_document(db_session, owner, size_bytes=len(pdf_content))
    save_pdf(db_session, document.id, pdf_content)
    db_session.commit()
    document_id = document.id
    db_session.expunge_all()

    with _capture_sql(db_session) as statements:
        files = db_session.execute(select(DocumentFile)).scalars().all()
        stored = db_session.get(DocumentFile, document_id)

        assert len(files) == 1
        assert stored is not None
        assert "content" in inspect(stored).unloaded
        assert all(not _CONTENT_COLUMN.search(sql) for sql in statements)

        assert stored.content == pdf_content
        assert any(_CONTENT_COLUMN.search(sql) for sql in statements)


def test_pasted_text_has_no_pdf_and_delete_is_noop(db_session):
    owner = _create_user(db_session)
    text = "La célula es la unidad básica de la vida."
    document = _create_document(
        db_session,
        owner,
        filename=None,
        source_type=SourceType.TEXT.value,
        size_bytes=len(text.encode("utf-8")),
    )
    db_session.add(
        DocumentFile(
            document_id=document.id,
            owner_id=owner.id,
            content_text=text,
        )
    )
    db_session.commit()

    with pytest.raises(StoredFileNotFoundError):
        read_pdf(db_session, document.id)

    delete_pdf(db_session, document.id)

    stored = db_session.get(DocumentFile, document.id)
    assert stored is not None
    assert stored.content_text == text
    assert stored.content is None

    with pytest.raises(StoredFileNotFoundError):
        read_pdf(db_session, document.id)


def test_deleting_document_cascades_file_and_delete_is_idempotent(
    db_session, pdf_content
):
    owner = _create_user(db_session)
    document = _create_document(db_session, owner, size_bytes=len(pdf_content))
    save_pdf(db_session, document.id, pdf_content)
    db_session.commit()
    document_id = document.id

    db_session.delete(document)
    db_session.commit()

    assert _count_files(db_session, document_id) == 0

    delete_pdf(db_session, document_id)
    delete_pdf(db_session, document_id)

    assert _count_files(db_session, document_id) == 0


def test_binary_payload_round_trip(db_session):
    owner = _create_user(db_session)
    document = _create_document(db_session, owner)
    payload = bytes(range(256)) + b"\x00\x00\xff\xfe"

    save_pdf(db_session, document.id, payload)

    assert read_pdf(db_session, document.id) == payload


def test_save_pdf_flushes_without_committing(db_session, pdf_content):
    owner = _create_user(db_session)
    document = _create_document(db_session, owner, size_bytes=len(pdf_content))
    document_id = document.id

    save_pdf(db_session, document_id, pdf_content)
    assert _count_files(db_session, document_id) == 1

    db_session.rollback()

    assert _count_files(db_session, document_id) == 0


def test_save_pdf_requires_existing_document(db_session):
    with pytest.raises(DocumentNotFoundError):
        save_pdf(db_session, uuid.uuid4(), b"%PDF-1.4")


def test_read_pdf_raises_for_missing_document(db_session):
    with pytest.raises(StoredFileNotFoundError):
        read_pdf(db_session, uuid.uuid4())
