import os
import subprocess
import sys
import uuid
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.user import User

BACKEND_ROOT = Path(__file__).resolve().parents[1]


def test_seed_user_script_is_idempotent(migrated_test_database):
    email = f"seed-{uuid.uuid4()}@example.com"
    env = os.environ.copy()
    env["DATABASE_URL"] = settings.test_database_url
    env["DATABASE_URL_UNPOOLED"] = ""

    command = [
        sys.executable,
        "scripts/seed_user.py",
        "--email",
        email,
        "--password",
        "secreto123",
        "--first-name",
        "Demo",
        "--last-name",
        "Usuario",
    ]

    for _ in range(2):
        result = subprocess.run(
            command,
            cwd=BACKEND_ROOT,
            env=env,
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, result.stderr
        assert "Usuario creado" in result.stdout or "ya existe" in result.stdout

    engine = create_engine(settings.test_database_url, pool_pre_ping=True)
    try:
        with Session(engine) as session:
            users = session.query(User).filter(User.email == email).all()
            assert len(users) == 1
            assert users[0].role == "Docente"

            session.delete(users[0])
            session.commit()
    finally:
        engine.dispose()
