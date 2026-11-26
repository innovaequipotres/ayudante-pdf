from collections.abc import Generator

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import settings


class Base(DeclarativeBase):
    """Base declarativa de SQLAlchemy 2.x para los modelos."""


# create_engine no abre conexiones: el engine se crea al importar el módulo,
# pero recién se conecta cuando se pide una sesión.
engine: Engine | None = None
if settings.database_url:
    engine = create_engine(settings.database_url, pool_pre_ping=True)

SessionLocal: sessionmaker[Session] = sessionmaker(
    bind=engine,
    autoflush=False,
    expire_on_commit=False,
)


def get_db() -> Generator[Session, None, None]:
    """Entrega una sesión por request y la cierra siempre al terminar."""
    if engine is None:
        raise RuntimeError(
            "DATABASE_URL no está configurada. "
            "Copiá backend/.env.example a backend/.env."
        )

    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
