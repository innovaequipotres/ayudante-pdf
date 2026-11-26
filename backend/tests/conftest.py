import os
import subprocess
import sys
from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

# Debe definirse antes de importar app.main: Settings se instancia al importar.
# Es un secreto exclusivo de la suite, nunca el de producción.
os.environ.setdefault(
    "JWT_SECRET", "test-jwt-secret-no-usar-en-produccion-0123456789abcdef"
)

from app.core.config import settings  # noqa: E402
from app.main import app  # noqa: E402
from app.services import session_service  # noqa: E402

BACKEND_ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="session")
def migrated_test_database() -> None:
    """Aplica las migraciones a la base de tests una vez por sesión.

    Se ejecuta en un subproceso para que Alembic use ``TEST_DATABASE_URL`` sin
    tocar la configuración global de la suite.
    """
    if not settings.test_database_url:
        pytest.fail(
            "TEST_DATABASE_URL no está configurada. "
            "Copiá backend/.env.example a backend/.env."
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
    """Sesión de DB aislada: cada test corre dentro de una transacción.

    Los ``commit()`` del test liberan savepoints internos, pero el rollback de
    la transacción externa al final deshace todo. Así no hace falta limpiar
    tablas a mano ni ordenar los tests.
    """
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
def clean_session_store():
    """Limpia el almacenamiento en memoria antes y después de cada test."""
    session_service._sessions.clear()
    session_service._raw_contents.clear()
    session_service._extracted_contents.clear()
    session_service._diagnoses.clear()
    yield
    session_service._sessions.clear()
    session_service._raw_contents.clear()
    session_service._extracted_contents.clear()
    session_service._diagnoses.clear()


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture
def pdf_content() -> bytes:
    """PDF mínimo válido: solo importa la firma %PDF en esta issue."""
    return b"%PDF-1.4\n1 0 obj<</Type/Catalog>>endobj\ntrailer<</Root 1 0 R>>\n%%EOF\n"
