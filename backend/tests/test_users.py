import uuid

import pytest
from pwdlib import PasswordHash
from sqlalchemy.exc import IntegrityError

from app.models.user import User
from app.schemas.auth import UserPublic


def _hashed_password(password: str = "secreto123") -> str:
    return PasswordHash.recommended().hash(password)


def test_create_user_sets_defaults(db_session):
    password = "secreto123"
    user = User(
        first_name="Ana",
        last_name="Pérez",
        email="Ana@Mail.com",
        password_hash=_hashed_password(password),
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    assert isinstance(user.id, uuid.UUID)
    assert user.first_name == "Ana"
    assert user.last_name == "Pérez"
    assert user.phone is None
    assert user.email == "ana@mail.com"
    assert user.role == "Docente"
    assert user.created_at is not None


def test_create_user_with_phone(db_session):
    user = User(
        first_name="Ana",
        last_name="Pérez",
        phone="123456789",
        email="ana2@mail.com",
        password_hash=_hashed_password(),
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    assert user.phone == "123456789"


def test_duplicate_email_is_case_insensitive(db_session):
    password_hash = _hashed_password()
    first = User(
        first_name="Ana",
        last_name="Pérez",
        email="ana@mail.com",
        password_hash=password_hash,
    )
    db_session.add(first)
    db_session.commit()

    duplicate = User(
        first_name="Otra",
        last_name="Persona",
        email="Ana@Mail.com",
        password_hash=password_hash,
    )
    db_session.add(duplicate)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_password_is_never_stored_plain(db_session):
    password = "secreto123"
    user = User(
        first_name="Ana",
        last_name="Pérez",
        email="ana3@mail.com",
        password_hash=_hashed_password(password),
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    assert user.password_hash != password
    assert user.password_hash.startswith("$argon2")
    assert PasswordHash.recommended().verify(password, user.password_hash)


def test_user_public_schema_does_not_expose_password(db_session):
    user = User(
        first_name="Ana",
        last_name="Pérez",
        email="ana4@mail.com",
        password_hash=_hashed_password(),
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    public = UserPublic.model_validate(user)

    assert "password_hash" not in UserPublic.model_fields
    assert "password" not in UserPublic.model_fields
    assert "password_hash" not in public.model_dump()
    assert "password" not in public.model_dump()
    assert public.email == "ana4@mail.com"
    assert public.role == "Docente"
