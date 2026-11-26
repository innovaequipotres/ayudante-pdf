from logging.config import fileConfig

from alembic import context
from sqlalchemy import create_engine, pool

import app.models  # noqa: F401  # registra todos los modelos para autogenerate

from app.core.config import settings
from app.core.database import Base

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

# Cuando existan modelos, importarlos acá para que Alembic los registre:
# from app import models  # noqa: F401


def _database_url() -> str:
    """Devuelve la URL para migrar o falla con un mensaje accionable.

    En producción usa la conexión directa de Neon (sin ``-pooler``), que es la
    recomendada para cambios de esquema. En local cae a ``DATABASE_URL``, que
    apunta al Postgres de Docker.
    """
    url = settings.database_url_unpooled or settings.database_url
    if not url:
        raise RuntimeError(
            "DATABASE_URL no está configurada. "
            "Copiá backend/.env.example a backend/.env."
        )
    return url


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    context.configure(
        url=_database_url(),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    connectable = create_engine(
        _database_url(),
        pool_pre_ping=True,
        poolclass=pool.NullPool,
    )

    try:
        with connectable.connect() as connection:
            context.configure(
                connection=connection,
                target_metadata=target_metadata,
            )

            with context.begin_transaction():
                context.run_migrations()
    finally:
        connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
