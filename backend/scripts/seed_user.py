"""Siembra un usuario de demo en la base de datos.

Uso:
    python scripts/seed_user.py \\
      --email demo@ejemplo.com --password "clave-segura" \\
      --first-name Demo --last-name Usuario

También se pueden pasar los valores por variables de entorno:
SEED_USER_EMAIL, SEED_USER_PASSWORD, SEED_USER_FIRST_NAME,
SEED_USER_LAST_NAME y SEED_USER_PHONE.

El script es manual: no se ejecuta al arrancar la app ni desde migraciones.
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parent.parent
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.core.database import SessionLocal, engine
from app.core.security import hash_password
from app.models.user import User


def _arg_or_env(value: str | None, env_name: str) -> str | None:
    if value is not None:
        return value
    return os.getenv(env_name)


def main() -> int:
    parser = argparse.ArgumentParser(description="Siembra un usuario de demo.")
    parser.add_argument("--email", default=None)
    parser.add_argument("--password", default=None)
    parser.add_argument("--first-name", default=None)
    parser.add_argument("--last-name", default=None)
    parser.add_argument("--phone", default=None)
    args = parser.parse_args()

    email = _arg_or_env(args.email, "SEED_USER_EMAIL")
    password = _arg_or_env(args.password, "SEED_USER_PASSWORD")
    first_name = _arg_or_env(args.first_name, "SEED_USER_FIRST_NAME")
    last_name = _arg_or_env(args.last_name, "SEED_USER_LAST_NAME")
    phone = _arg_or_env(args.phone, "SEED_USER_PHONE")

    missing = [
        name
        for name, value in (
            ("email", email),
            ("password", password),
            ("first_name", first_name),
            ("last_name", last_name),
        )
        if not value
    ]
    if missing:
        parser.error(f"Faltan datos obligatorios: {', '.join(missing)}")

    if engine is None:
        print("DATABASE_URL no está configurada. Copiá backend/.env.example a backend/.env.")
        return 1

    normalized_email = email.strip().lower()

    password_hash = hash_password(password)

    session = SessionLocal()
    try:
        existing = session.query(User).filter(User.email == normalized_email).first()
        if existing is not None:
            print(f"El usuario ya existe (id={existing.id}); no se duplica.")
            return 0

        user = User(
            first_name=first_name.strip(),
            last_name=last_name.strip(),
            phone=phone.strip() if phone else None,
            email=normalized_email,
            password_hash=password_hash,
        )
        session.add(user)
        session.commit()
        session.refresh(user)
        print(f"Usuario creado: id={user.id}, email={user.email}, role={user.role}")
        return 0
    finally:
        session.close()


if __name__ == "__main__":
    raise SystemExit(main())
