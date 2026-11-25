import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL, make_url
from sqlalchemy.orm import sessionmaker

from app.core import database
from app.core.config import settings


def _test_database_url() -> URL:
    """Valida que la URL de test sea segura y devuelve el objeto URL."""
    assert settings.test_database_url, (
        "TEST_DATABASE_URL no está configurada. "
        "Copiá backend/.env.example a backend/.env."
    )
    assert settings.test_database_url != settings.database_url, (
        "TEST_DATABASE_URL no puede ser igual a DATABASE_URL."
    )

    url = make_url(settings.test_database_url)
    assert url.drivername == "postgresql+psycopg", (
        "TEST_DATABASE_URL debe usar el driver postgresql+psycopg."
    )
    assert url.database and url.database.endswith("_test"), (
        "El nombre de la base de TEST_DATABASE_URL debe terminar en _test."
    )
    return url


def test_test_database_url_is_safe() -> None:
    _test_database_url()


def test_test_database_connection() -> None:
    engine = create_engine(_test_database_url(), pool_pre_ping=True)
    try:
        with engine.connect() as connection:
            assert connection.execute(text("SELECT 1")).scalar_one() == 1
    finally:
        engine.dispose()


def test_get_db_yields_working_session(monkeypatch: pytest.MonkeyPatch) -> None:
    test_engine = create_engine(_test_database_url(), pool_pre_ping=True)
    test_session_local = sessionmaker(
        bind=test_engine,
        autoflush=False,
        expire_on_commit=False,
    )
    monkeypatch.setattr(database, "engine", test_engine)
    monkeypatch.setattr(database, "SessionLocal", test_session_local)

    session_generator = database.get_db()
    session = next(session_generator)
    try:
        assert session.execute(text("SELECT 1")).scalar_one() == 1
    finally:
        session_generator.close()
        test_engine.dispose()
