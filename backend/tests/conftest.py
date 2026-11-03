import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services import session_service


@pytest.fixture(autouse=True)
def clean_session_store():
    """Limpia el almacenamiento en memoria antes y después de cada test."""
    session_service._sessions.clear()
    session_service._raw_contents.clear()
    session_service._extracted_contents.clear()
    yield
    session_service._sessions.clear()
    session_service._raw_contents.clear()
    session_service._extracted_contents.clear()


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture
def pdf_content() -> bytes:
    """PDF mínimo válido: solo importa la firma %PDF en esta issue."""
    return b"%PDF-1.4\n1 0 obj<</Type/Catalog>>endobj\ntrailer<</Root 1 0 R>>\n%%EOF\n"
