"""Hash de contraseñas y emisión/validación de tokens JWT."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

import jwt
from pwdlib import PasswordHash

from app.core.config import settings

# Algoritmo único de firma. Se exige explícitamente al decodificar para no
# aceptar tokens firmados con otro algoritmo.
JWT_ALGORITHM = "HS256"

# Hash Argon2 de una contraseña ficticia. Se verifica contra él cuando el email
# no existe en el login para que el tiempo de respuesta no delate si la cuenta
# está registrada. No es un secreto.
DUMMY_PASSWORD_HASH = (
    "$argon2id$v=19$m=65536,t=3,p=4$/89WdTYwwHWEmTU94UE3Jg$"
    "qip+U29rA7xmh3w2tjpngNJL4mSAvzVbM0YN8VAOM5k"
)

_password_hash = PasswordHash.recommended()


class InvalidTokenError(Exception):
    """Token JWT ausente, inválido, vencido o con claims incorrectos."""


def hash_password(password: str) -> str:
    """Devuelve el hash Argon2 de ``password``."""
    return _password_hash.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    """Verifica ``password`` contra un hash Argon2 almacenado."""
    try:
        return _password_hash.verify(password, password_hash)
    except Exception:
        # Un hash corrupto o con otro formato se trata como credencial inválida.
        return False


def _jwt_secret() -> str:
    """Devuelve el secreto de firma o falla con un error claro si falta."""
    if not settings.jwt_secret:
        raise RuntimeError(
            "JWT_SECRET no está configurada. "
            "Copiá backend/.env.example a backend/.env y definí un secreto."
        )
    return settings.jwt_secret


def create_access_token(user_id: uuid.UUID) -> tuple[str, int]:
    """Crea un access token para ``user_id`` y devuelve ``(token, expires_in)``.

    ``expires_in`` está en segundos.
    """
    expires_in = settings.jwt_expire_minutes * 60
    now = datetime.now(UTC)
    payload = {
        "sub": str(user_id),
        "iat": now,
        "exp": now + timedelta(seconds=expires_in),
    }
    token = jwt.encode(payload, _jwt_secret(), algorithm=JWT_ALGORITHM)
    return token, expires_in


def decode_access_token(token: str) -> dict[str, Any]:
    """Decodifica y valida un access token.

    Exige ``exp``, ``iat`` y ``sub``. Cualquier error de PyJWT (firma,
    vencimiento, formato) se traduce en :class:`InvalidTokenError`.
    """
    secret = _jwt_secret()
    try:
        return jwt.decode(
            token,
            secret,
            algorithms=[JWT_ALGORITHM],
            options={"require": ["exp", "iat", "sub"]},
        )
    except jwt.PyJWTError as exc:
        raise InvalidTokenError("Token de acceso inválido") from exc
