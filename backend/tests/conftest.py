import os
import subprocess
import sys
from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

# Debe definirse antes de importar app.main: Settings se instancia al importar.
# Es un secreto exclusivo de la suite, nunca el de producción.
os.environ.setdefault(
    "JWT_SECRET", "test-jwt-secret-no-usar-en-produccion-0123456789abcdef"
)

from app.core.config import settings  # noqa: E402
from app.core.database import Base, get_db  # noqa: E402
from app.main import app  # noqa: E402
from app.services import session_service  # noqa: E402

BACKEND_ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="session")
def migrated_test_database() -> None:
    """Aplica las migraciones a la base de tests una vez por sesión."""
    if not settings.test_database_url:
        pytest.fail(
            "TEST_DATABASE_URL no está configurada. "
            "Copia backend/.env.example a backend/.env."
        )

    env = os.environ.copy()
    env["DATABASE_URL"] = settings.test_database_url
    env["DATABASE_URL_UNPOOLED"] = ""

    result = subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        cwd=BACKEND_ROOT,
        env=env,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(
            "No se pudieron aplicar las migraciones a la base de tests.\n"
            f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
        )


@pytest.fixture
def db_session(migrated_test_database: None) -> Iterator[Session]:
    """Sesión de DB aislada: cada test corre dentro de una transacción."""
    engine = create_engine(settings.test_database_url, pool_pre_ping=True)
    connection = engine.connect()
    transaction = connection.begin()
    session = Session(
        bind=connection,
        join_transaction_mode="create_savepoint",
        expire_on_commit=False,
    )
    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()
        engine.dispose()


@pytest.fixture(autouse=True)
def clean_database_tables(migrated_test_database: None) -> Iterator[None]:
    """Trunca las tablas de la app entre tests y limpia estado en memoria."""
    # Guardia de seguridad: solo la base de tests.
    if not settings.test_database_url:
        pytest.fail("TEST_DATABASE_URL no está configurada.")
    if settings.test_database_url == settings.database_url:
        pytest.fail("TEST_DATABASE_URL no puede ser igual a DATABASE_URL.")
    if not settings.test_database_url.rstrip("/").endswith("_test"):
        pytest.fail("TEST_DATABASE_URL debe apuntar a una base cuyo nombre termine en _test.")

    engine = create_engine(settings.test_database_url, pool_pre_ping=True)
    with engine.connect() as connection:
        db_name = connection.execute(text("SELECT current_database()")).scalar_one()
        if db_name != settings.test_database_url.rsplit("/", 1)[-1]:
            pytest.fail(
                f"La base conectada ({db_name}) no coincide con TEST_DATABASE_URL."
            )
        if not str(db_name).endswith("_test"):
            pytest.fail("Abortado: la base de datos no es la de tests.")

    # Truncar todas las tablas de la app (no alembic_version).
    with engine.begin() as connection:
        for table in reversed(Base.metadata.sorted_tables):
            connection.execute(
                text(f"TRUNCATE TABLE {table.name} RESTART IDENTITY CASCADE")
            )

    # Limpieza residual del estado en memoria aún no migrado.
    session_service._extracted_contents.clear()
    session_service._diagnoses.clear()

    yield

    with engine.begin() as connection:
        for table in reversed(Base.metadata.sorted_tables):
            connection.execute(
                text(f"TRUNCATE TABLE {table.name} RESTART IDENTITY CASCADE")
            )
    session_service._extracted_contents.clear()
    session_service._diagnoses.clear()
    engine.dispose()


@pytest.fixture
def client() -> TestClient:
    engine = create_engine(settings.test_database_url, pool_pre_ping=True)
    TestSession = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)

    def override_get_db() -> Iterator[Session]:
        db = TestSession()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.pop(get_db, None)
    engine.dispose()


@pytest.fixture
def pdf_content() -> bytes:
    """PDF mínimo válido: solo importa la firma %PDF en esta issue."""
    return b"%PDF-1.4\n1 0 obj<</Type/Catalog>>endobj\ntrailer<</Root 1 0 R>>\n%%EOF\n"
