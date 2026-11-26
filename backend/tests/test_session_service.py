import hashlib
from uuid import UUID

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exceptions import AppError
from app.services import session_service, storage
from app.services.session_service import SourceType


PDF = b"%PDF-1.4\n1 0 obj<</Type/Catalog>>endobj\ntrailer<</Root 1 0 R>>\n%%EOF\n"


def _engine():
    return create_engine(settings.test_database_url, pool_pre_ping=True)


def test_session_persists_across_db_sessions() -> None:
    engine = _engine()
    created_id = None
    try:
        with Session(engine) as db:
            session = session_service.create_from_file(db, "clase.pdf", PDF)
            db.commit()
            created_id = session.session_id
            assert session.source_type is SourceType.PDF
            assert session.filename == "clase.pdf"
            assert session.size_bytes == len(PDF)

        with Session(engine) as db2:
            loaded = session_service.get_session(db2, created_id)
            assert loaded.session_id == created_id
            assert loaded.source_type is SourceType.PDF
            assert loaded.filename == "clase.pdf"
            assert loaded.size_bytes == len(PDF)

            raw = session_service.get_raw_content(db2, created_id)
            assert isinstance(raw, (bytes, bytearray))
            assert hashlib.sha256(bytes(raw)).hexdigest() == hashlib.sha256(PDF).hexdigest()
    finally:
        engine.dispose()


def test_text_session_persists_across_db_sessions() -> None:
    text = "La célula es la unidad básica de la vida."
    engine = _engine()
    try:
        with Session(engine) as db:
            session = session_service.create_from_text(db, {"title": "Bio", "text": text})
            db.commit()
            sid = session.session_id

        with Session(engine) as db2:
            loaded = session_service.get_session(db2, sid)
            assert loaded.source_type is SourceType.TEXT
            assert loaded.filename == "Bio"
            assert loaded.size_bytes == len(text.encode("utf-8"))

            raw = session_service.get_raw_content(db2, sid)
            assert raw == text
    finally:
        engine.dispose()


def test_create_from_file_is_atomic(monkeypatch: pytest.MonkeyPatch) -> None:
    engine = _engine()
    try:
        def boom(*args, **kwargs):
            raise RuntimeError("fallo de storage")

        monkeypatch.setattr(storage, "save_pdf", boom)

        with Session(engine) as db:
            with pytest.raises(RuntimeError):
                session_service.create_from_file(db, "clase.pdf", PDF)
            db.commit()

            from sqlalchemy import select
            from app.models.document import Document

            rows = db.execute(select(Document)).scalars().all()
            assert rows == []
    finally:
        engine.dispose()


def test_no_private_dicts() -> None:
    assert not hasattr(session_service, "_sessions")
    assert not hasattr(session_service, "_raw_contents")