import socket
from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.scanner import ai_analysis
from app.services import session_service
from tests.materials import CLEAN_TEXT, PROBLEM_TEXT
from tests.pdf_factory import (
    make_blank_pdf,
    make_clean_pdf,
    make_image_pdf,
    make_malformed_pdf,
    make_multipage_pdf,
    make_problem_pdf,
    make_problem_pdf_with_image,
)


@pytest.fixture(autouse=True)
def clean_session_store() -> Iterator[None]:
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


_LOOPBACK_HOSTS = {"", "localhost", "127.0.0.1", "::1"}


def _is_loopback(address: object) -> bool:
    """Indica si una dirección de socket apunta a la propia máquina."""
    if isinstance(address, tuple) and address:
        host = address[0]
    else:
        host = address
    return isinstance(host, str) and host.lower() in _LOOPBACK_HOSTS


@pytest.fixture(autouse=True)
def block_network(monkeypatch: pytest.MonkeyPatch) -> None:
    """Falla si un test intenta abrir una conexión a internet.

    Se permite el loopback porque el ``TestClient`` de Starlette crea un
    ``socketpair`` local en Windows.
    """
    original_connect = socket.socket.connect
    original_connect_ex = socket.socket.connect_ex
    original_create_connection = socket.create_connection
    original_getaddrinfo = socket.getaddrinfo

    def guard(message: str) -> None:
        raise AssertionError(
            f"Un test intentó una llamada de red ({message}). "
            "La IA y los servicios externos deben simularse."
        )

    def connect(sock: socket.socket, address: object) -> None:
        if not _is_loopback(address):
            guard(f"connect a {address!r}")
        return original_connect(sock, address)  # type: ignore[arg-type]

    def connect_ex(sock: socket.socket, address: object) -> int:
        if not _is_loopback(address):
            guard(f"connect_ex a {address!r}")
        return original_connect_ex(sock, address)  # type: ignore[arg-type]

    def create_connection(
        address: tuple[str, int],
        *args: object,
        **kwargs: object,
    ) -> socket.socket:
        if not _is_loopback(address):
            guard(f"create_connection a {address!r}")
        return original_create_connection(  # type: ignore[arg-type]
            address,
            *args,
            **kwargs,
        )

    def getaddrinfo(host: object, *args: object, **kwargs: object) -> object:
        if not _is_loopback(host):
            guard(f"getaddrinfo de {host!r}")
        return original_getaddrinfo(host, *args, **kwargs)  # type: ignore[arg-type]

    monkeypatch.setattr(socket.socket, "connect", connect)
    monkeypatch.setattr(socket.socket, "connect_ex", connect_ex)
    monkeypatch.setattr(socket, "create_connection", create_connection)
    monkeypatch.setattr(socket, "getaddrinfo", getaddrinfo)


@pytest.fixture(autouse=True)
def disable_real_ai(monkeypatch: pytest.MonkeyPatch) -> None:
    """Evita que un test que olvida mockear la IA use un proveedor real."""
    monkeypatch.setattr(ai_analysis, "get_ai_service", lambda: None)


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture(scope="session")
def clean_text() -> str:
    """Texto sin problemas de accesibilidad pedagógica."""
    return CLEAN_TEXT


@pytest.fixture(scope="session")
def problem_text() -> str:
    """Texto con párrafos, oraciones y estructura problemáticos."""
    return PROBLEM_TEXT


@pytest.fixture(scope="session")
def clean_pdf() -> bytes:
    """PDF real, generado con reportlab, sin problemas detectables."""
    return make_clean_pdf()


@pytest.fixture(scope="session")
def problem_pdf() -> bytes:
    """PDF real sin títulos y con párrafo y oración extensos."""
    return make_problem_pdf()


@pytest.fixture(scope="session")
def blank_pdf() -> bytes:
    """PDF válido sin capa de texto."""
    return make_blank_pdf()


@pytest.fixture(scope="session")
def multipage_pdf() -> bytes:
    """PDF real de tres páginas."""
    return make_multipage_pdf()


@pytest.fixture(scope="session")
def image_pdf() -> bytes:
    """PDF real con una imagen sin texto alternativo."""
    return make_image_pdf()


@pytest.fixture(scope="session")
def problem_pdf_with_image() -> bytes:
    """PDF real con problemas de texto y de imagen."""
    return make_problem_pdf_with_image()


@pytest.fixture(scope="session")
def malformed_pdf() -> bytes:
    """Archivo con firma PDF pero contenido inválido."""
    return make_malformed_pdf()


@pytest.fixture
def pdf_content(clean_pdf: bytes) -> bytes:
    """PDF mínimo válido usado por los tests de sesiones."""
    return clean_pdf
