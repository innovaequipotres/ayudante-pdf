from pathlib import Path

from alembic.config import Config
from alembic.script import ScriptDirectory
from sqlalchemy import text

from app.core.config import settings

BACKEND_ROOT = Path(__file__).resolve().parents[1]

EXPECTED_TABLES = {
    "alembic_version",
    "diagnoses",
    "document_files",
    "documents",
    "extracted_contents",
    "folders",
    "users",
}

TEXT_ENUM_COLUMNS = {
    ("documents", "source_type"),
    ("documents", "status"),
    ("diagnoses", "level"),
    ("diagnoses", "ai_status"),
}


def test_alembic_upgrade_head_creates_tables(db_session):
    tables = set(
        db_session.execute(
            text(
                "SELECT table_name FROM information_schema.tables "
                "WHERE table_schema = 'public'"
            )
        ).scalars()
    )

    assert EXPECTED_TABLES <= tables


def test_alembic_version_is_head(db_session):
    config = Config(str(BACKEND_ROOT / "alembic.ini"))
    head = ScriptDirectory.from_config(config).get_current_head()

    version = db_session.execute(
        text("SELECT version_num FROM alembic_version")
    ).scalar_one()

    assert version == head


def test_enums_are_stored_as_text(db_session):
    rows = db_session.execute(
        text(
            "SELECT table_name, column_name, data_type, udt_name "
            "FROM information_schema.columns "
            "WHERE table_schema = 'public' "
            "AND column_name IN ('source_type', 'status', 'level', 'ai_status')"
        )
    ).all()

    found = {
        (row.table_name, row.column_name): (row.data_type, row.udt_name)
        for row in rows
        if (row.table_name, row.column_name) in TEXT_ENUM_COLUMNS
    }

    assert set(found) == TEXT_ENUM_COLUMNS
    for data_type, udt_name in found.values():
        assert data_type in {"character varying", "text"}
        assert udt_name in {"varchar", "text"}


def test_no_native_enum_types(db_session):
    enum_types = set(
        db_session.execute(
            text("SELECT typname FROM pg_type WHERE typtype = 'e'")
        ).scalars()
    )

    assert enum_types == set()


def test_test_database_url_is_configured():
    assert settings.test_database_url
    assert settings.test_database_url != settings.database_url
