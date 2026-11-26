"""Dependencias compartidas de la API."""

import uuid

from fastapi import Depends, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.exceptions import AppError
from app.core.security import InvalidTokenError, decode_access_token
from app.models.user import User

# auto_error=False para controlar el error y devolver siempre 401 invalid_token
# con el formato de error de la API, en lugar del 403 de HTTPBearer.
_bearer_scheme = HTTPBearer(auto_error=False)

_INVALID_TOKEN_MESSAGE = "Token de acceso inválido o expirado."


def _invalid_token() -> AppError:
    return AppError("invalid_token", _INVALID_TOKEN_MESSAGE, 401)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Security(_bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    """Devuelve el usuario autenticado o lanza 401 ``invalid_token``.

    Cubre header ausente, esquema distinto de Bearer, firma inválida, token
    vencido, ``sub`` ausente o que no sea un UUID, y usuario inexistente.
    """
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise _invalid_token()

    try:
        payload = decode_access_token(credentials.credentials)
    except InvalidTokenError as exc:
        raise _invalid_token() from exc

    subject = payload.get("sub")
    try:
        user_id = uuid.UUID(str(subject))
    except (TypeError, ValueError, AttributeError) as exc:
        raise _invalid_token() from exc

    user = db.get(User, user_id)
    if user is None:
        raise _invalid_token()
    return user
