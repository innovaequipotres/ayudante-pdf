import uuid
from datetime import UTC, datetime

import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from app.models.diagnosis import DiagnosisRecord
from app.models.document import Document
from app.models.document_file import DocumentFile
from app.models.extracted_content import ExtractedContentRecord
from app.models.folder import Folder
from app.models.user import User
from app.schemas.ai import AiStatus
from app.schemas.content import ContentSummary, ExtractedContent
from app.schemas.diagnosis import Diagnosis, DiagnosisLevel
from app.schemas.session import SourceType


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


def _create_folder(db_session, owner: User, name: str = "Matemática") -> Folder:
    folder = Folder(owner_id=owner.id, name=name)
    db_session.add(folder)
    db_session.commit()
    return folder


def _create_document(
    db_session,
    owner: User,
    *,
    source_type: str,
    filename: str | None,
    size_bytes: int,
    folder: Folder | None = None,
) -> Document:
    document = Document(
        owner_id=owner.id,
        folder_id=folder.id if folder else None,
        source_type=source_type,
        filename=filename,
        size_bytes=size_bytes,
    )
    db_session.add(document)
    db_session.commit()
    return document


def _extracted_payload(document: Document) -> dict:
    return ExtractedContent(
        session_id=document.id,
        source_type=SourceType(document.source_type),
        title="Material de prueba",
        page_count=1,
        pages=[],
        summary=ContentSummary(
            word_count=3,
            heading_count=1,
            paragraph_count=1,
            list_count=0,
            image_count=0,
            images_without_alt=0,
        ),
        blocks=[],
    ).model_dump(mode="json")


def _diagnosis_payload(document: Document) -> dict:
    return Diagnosis(
        session_id=document.id,
        score=96,
        level=DiagnosisLevel.REVIEW,
        categories=[],
        observations=[],
        created_at=datetime.now(UTC),
        ai_status=AiStatus.SKIPPED,
    ).model_dump(mode="json")


def test_insert_and_read_pdf_document(db_session, pdf_content):
    owner = _create_user(db_session)
    folder = _create_folder(db_session, owner)
    document = _create_document(
        db_session,
        owner,
        source_type=SourceType.PDF.value,
        filename="material.pdf",
        size_bytes=len(pdf_content),
        folder=folder,
    )
    db_session.add(
        DocumentFile(
            document_id=document.id,
            owner_id=owner.id,
            content=pdf_content,
        )
    )
    db_session.commit()
    db_session.expire_all()

    loaded = db_session.get(Document, document.id)
    stored_file = db_session.get(DocumentFile, document.id)

    assert loaded is not None
    assert loaded.owner_id == owner.id
    assert loaded.folder_id == folder.id
    assert loaded.source_type == "pdf"
    assert loaded.filename == "material.pdf"
    assert loaded.size_bytes == len(pdf_content)
    assert loaded.status == "uploaded"
    assert loaded.created_at is not None
    assert loaded.updated_at is not None

    assert stored_file is not None
    assert stored_file.content == pdf_content
    assert stored_file.content_text is None

    raw = db_session.execute(
        text("SELECT source_type, status FROM documents WHERE id = :id"),
        {"id": document.id},
    ).one()
    assert tuple(raw) == ("pdf", "uploaded")


def test_insert_and_read_text_document(db_session):
    owner = _create_user(db_session)
    content_text = "La célula es la unidad básica de la vida."
    document = _create_document(
        db_session,
        owner,
        source_type=SourceType.TEXT.value,
        filename=None,
        size_bytes=len(content_text.encode("utf-8")),
    )
    db_session.add(
        DocumentFile(
            document_id=document.id,
            owner_id=owner.id,
            content_text=content_text,
        )
    )
    db_session.commit()
    db_session.expire_all()

    loaded = db_session.get(Document, document.id)
    stored_file = db_session.get(DocumentFile, document.id)

    assert loaded is not None
    assert loaded.folder_id is None
    assert loaded.source_type == "text"
    assert loaded.filename is None
    assert loaded.size_bytes == len(content_text.encode("utf-8"))

    assert stored_file is not None
    assert stored_file.content is None
    assert stored_file.content_text == content_text

    raw = db_session.execute(
        text("SELECT source_type, status FROM documents WHERE id = :id"),
        {"id": document.id},
    ).one()
    assert tuple(raw) == ("text", "uploaded")


def test_store_extracted_content_and_diagnosis(db_session):
    owner = _create_user(db_session)
    document = _create_document(
        db_session,
        owner,
        source_type=SourceType.PDF.value,
        filename="material.pdf",
        size_bytes=128,
    )

    extracted = ExtractedContentRecord(
        document_id=document.id,
        owner_id=owner.id,
        payload=_extracted_payload(document),
    )
    diagnosis = DiagnosisRecord(
        document_id=document.id,
        owner_id=owner.id,
        payload=_diagnosis_payload(document),
        score=96,
        level=DiagnosisLevel.REVIEW.value,
        ai_status=AiStatus.SKIPPED.value,
    )
    db_session.add_all([extracted, diagnosis])
    db_session.commit()
    db_session.expire_all()

    stored_content = db_session.get(ExtractedContentRecord, document.id)
    stored_diagnosis = db_session.get(DiagnosisRecord, document.id)

    assert stored_content is not None
    assert stored_content.owner_id == owner.id
    assert stored_content.payload["summary"]["word_count"] == 3
    assert stored_content.payload["session_id"] == str(document.id)

    assert stored_diagnosis is not None
    assert stored_diagnosis.owner_id == owner.id
    assert stored_diagnosis.score == 96
    assert stored_diagnosis.level == "review"
    assert stored_diagnosis.ai_status == "skipped"
    assert stored_diagnosis.payload["score"] == 96
    assert stored_diagnosis.payload["level"] == "review"


def test_document_file_requires_exactly_one_content(db_session):
    owner = _create_user(db_session)
    document = _create_document(
        db_session,
        owner,
        source_type=SourceType.PDF.value,
        filename="material.pdf",
        size_bytes=10,
    )

    db_session.add(
        DocumentFile(
            document_id=document.id,
            owner_id=owner.id,
            content=b"%PDF-1.4",
            content_text="texto",
        )
    )
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()

    db_session.add(DocumentFile(document_id=document.id, owner_id=owner.id))
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_document_rejects_invalid_source_type_and_status(db_session):
    owner = _create_user(db_session)

    invalid_source = Document(
        owner_id=owner.id,
        source_type="docx",
        filename="material.docx",
        size_bytes=10,
    )
    db_session.add(invalid_source)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()

    invalid_status = Document(
        owner_id=owner.id,
        source_type=SourceType.PDF.value,
        filename="material.pdf",
        size_bytes=10,
        status="desconocido",
    )
    db_session.add(invalid_status)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_diagnosis_score_must_be_in_range(db_session):
    owner = _create_user(db_session)
    document = _create_document(
        db_session,
        owner,
        source_type=SourceType.PDF.value,
        filename="material.pdf",
        size_bytes=10,
    )

    db_session.add(
        DiagnosisRecord(
            document_id=document.id,
            owner_id=owner.id,
            payload=_diagnosis_payload(document),
            score=101,
            level=DiagnosisLevel.REVIEW.value,
            ai_status=AiStatus.SKIPPED.value,
        )
    )
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_deleting_document_cascades_children(db_session):
    owner = _create_user(db_session)
    document = _create_document(
        db_session,
        owner,
        source_type=SourceType.PDF.value,
        filename="material.pdf",
        size_bytes=10,
    )
    db_session.add_all(
        [
            DocumentFile(
                document_id=document.id,
                owner_id=owner.id,
                content=b"%PDF-1.4",
            ),
            ExtractedContentRecord(
                document_id=document.id,
                owner_id=owner.id,
                payload=_extracted_payload(document),
            ),
            DiagnosisRecord(
                document_id=document.id,
                owner_id=owner.id,
                payload=_diagnosis_payload(document),
                score=96,
                level=DiagnosisLevel.REVIEW.value,
                ai_status=AiStatus.SKIPPED.value,
            ),
        ]
    )
    db_session.commit()

    db_session.delete(document)
    db_session.commit()
    db_session.expire_all()

    assert db_session.get(Document, document.id) is None
    assert db_session.get(DocumentFile, document.id) is None
    assert db_session.get(ExtractedContentRecord, document.id) is None
    assert db_session.get(DiagnosisRecord, document.id) is None
