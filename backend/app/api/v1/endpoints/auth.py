"""Endpoints de alta, login y datos del usuario autenticado."""

from fastapi import APIRouter, Depends, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.core.database import get_db
from app.core.exceptions import AppError
from app.core.security import (
    DUMMY_PASSWORD_HASH,
    create_access_token,
    hash_password,
    verify_password,
)
from app.models.user import User
from app.schemas.auth import (
    AuthResponse,
    LoginRequest,
    RegisterRequest,
    UserResponse,
)
from app.schemas.common import ErrorResponse

router = APIRouter(prefix="/auth", tags=["Auth"])


def _email_already_registered() -> AppError:
    return AppError(
        "email_already_registered",
        "Ya existe un usuario registrado con ese email.",
        409,
    )


def _invalid_credentials() -> AppError:
    return AppError(
        "invalid_credentials",
        "Email o contraseña incorrectos.",
        401,
    )


_AUTH_RESPONSES = {
    status.HTTP_409_CONFLICT: {
        "model": ErrorResponse,
        "description": "El email ya está registrado (`email_already_registered`).",
    },
}
_LOGIN_RESPONSES = {
    status.HTTP_401_UNAUTHORIZED: {
        "model": ErrorResponse,
        "description": "Credenciales inválidas (`invalid_credentials`).",
    },
}
_ME_RESPONSES = {
    status.HTTP_401_UNAUTHORIZED: {
        "model": ErrorResponse,
        "description": "Token ausente, inválido o vencido (`invalid_token`).",
    },
}


def _auth_response(user: User) -> AuthResponse:
    token, expires_in = create_access_token(user.id)
    return AuthResponse(
        access_token=token,
        expires_in=expires_in,
        user=UserResponse.from_user(user),
    )


@router.post(
    "/register",
    response_model=AuthResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar un usuario",
    responses=_AUTH_RESPONSES,
)
def register(
    payload: RegisterRequest,
    db: Session = Depends(get_db),
) -> AuthResponse:
    """Crea el usuario y devuelve un access token."""
    email = str(payload.email)
    existing = db.query(User).filter(User.email == email).first()
    if existing is not None:
        raise _email_already_registered()

    user = User(
        first_name=payload.first_name,
        last_name=payload.last_name,
        phone=payload.phone,
        email=email,
        password_hash=hash_password(payload.password),
    )
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        # Condición de carrera: otro request registró el email entre la
        # consulta y el commit. La restricción única lo garantiza igual.
        db.rollback()
        raise _email_already_registered() from None

    db.refresh(user)
    return _auth_response(user)


@router.post(
    "/login",
    response_model=AuthResponse,
    status_code=status.HTTP_200_OK,
    summary="Iniciar sesión",
    responses=_LOGIN_RESPONSES,
)
def login(
    payload: LoginRequest,
    db: Session = Depends(get_db),
) -> AuthResponse:
    """Verifica las credenciales y devuelve un access token."""
    email = str(payload.email)
    user = db.query(User).filter(User.email == email).first()

    if user is None:
        # Se verifica contra un hash ficticio para que el tiempo de respuesta
        # no revele si el email está registrado.
        verify_password(payload.password, DUMMY_PASSWORD_HASH)
        raise _invalid_credentials()

    if not verify_password(payload.password, user.password_hash):
        raise _invalid_credentials()

    return _auth_response(user)


@router.get(
    "/me",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Datos del usuario autenticado",
    responses=_ME_RESPONSES,
)
def read_me(current_user: User = Depends(get_current_user)) -> UserResponse:
    """Devuelve el usuario dueño del token."""
    return UserResponse.from_user(current_user)
