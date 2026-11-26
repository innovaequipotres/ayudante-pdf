"""Tests de autenticación con JWT (BE-27)."""

import logging
import uuid
from datetime import UTC, datetime, timedelta

import jwt
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.core.database import get_db
from app.core.security import create_access_token, verify_password
from app.main import app
from app.models.user import User

PASSWORD = "ClaveSegura123"
OTHER_SECRET = "otro-secreto-que-no-es-el-de-la-app-0123456789"


def _payload(**overrides):
    data = {
        "first_name": "Ana",
        "last_name": "Pérez",
        "email": "ana.perez@example.com",
        "password": PASSWORD,
        "phone": "123456789",
    }
    data.update(overrides)
    return data


def _register(client: TestClient, **overrides):
    return client.post("/api/v1/auth/register", json=_payload(**overrides))


def _auth_header(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def db_session():
    engine = create_engine(settings.test_database_url, pool_pre_ping=True)
    session = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)()
    session.query(User).delete()
    session.commit()
    try:
        yield session
    finally:
        session.rollback()
        session.query(User).delete()
        session.commit()
        session.close()
        engine.dispose()


@pytest.fixture
def api_client(db_session):
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    try:
        with TestClient(app) as client:
            yield client
    finally:
        app.dependency_overrides.clear()


def test_register_returns_token_and_normalized_user(api_client, db_session):
    response = _register(api_client, email="Ana.Perez@Example.COM")

    assert response.status_code == 201
    body = response.json()
    assert set(body) == {"access_token", "token_type", "expires_in", "user"}
    assert body["token_type"] == "bearer"
    assert body["expires_in"] == settings.jwt_expire_minutes * 60

    user = body["user"]
    assert set(user) == {"id", "email", "full_name", "role", "created_at"}
    assert user["email"] == "ana.perez@example.com"
    assert user["full_name"] == "Ana Pérez"
    assert user["role"] == "Docente"
    uuid.UUID(user["id"])

    decoded = jwt.decode(
        body["access_token"],
        settings.jwt_secret,
        algorithms=["HS256"],
        options={"require": ["exp", "iat", "sub"]},
    )
    now = datetime.now(UTC).timestamp()
    assert decoded["sub"] == user["id"]
    assert abs(decoded["iat"] - now) < 60
    assert abs(decoded["exp"] - decoded["iat"] - body["expires_in"]) < 5

    stored = db_session.get(User, uuid.UUID(user["id"]))
    assert stored is not None
    assert stored.email == "ana.perez@example.com"
    assert stored.password_hash.startswith("$argon2")
    assert stored.password_hash != PASSWORD
    assert verify_password(PASSWORD, stored.password_hash)


def test_register_duplicate_email_is_case_insensitive(api_client):
    assert _register(api_client).status_code == 201

    response = _register(api_client, email="ANA.PEREZ@EXAMPLE.COM")

    assert response.status_code == 409
    assert response.json()["code"] == "email_already_registered"


@pytest.mark.parametrize(
    "overrides",
    [
        {"email": "no-es-un-email"},
        {"password": "corta"},
        {"first_name": ""},
        {"email": None},
    ],
)
def test_register_invalid_data_returns_422(api_client, overrides):
    response = _register(api_client, **overrides)

    assert response.status_code == 422
    assert response.json()["code"] == "VALIDATION_ERROR"


def test_register_missing_fields_returns_422(api_client):
    response = api_client.post(
        "/api/v1/auth/register",
        json={"email": "incompleto@example.com"},
    )

    assert response.status_code == 422
    body = response.json()
    assert body["code"] == "VALIDATION_ERROR"
    assert "password" in body["message"]
    assert "first_name" in body["message"]


def test_login_returns_token_and_user(api_client):
    register = _register(api_client)
    assert register.status_code == 201

    response = api_client.post(
        "/api/v1/auth/login",
        json={"email": "ANA.PEREZ@EXAMPLE.COM", "password": PASSWORD},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"]
    assert body["user"] == register.json()["user"]


def test_login_wrong_password_and_unknown_email_are_indistinguishable(api_client):
    assert _register(api_client).status_code == 201

    wrong_password = api_client.post(
        "/api/v1/auth/login",
        json={"email": "ana.perez@example.com", "password": "OtraClave123"},
    )
    unknown_email = api_client.post(
        "/api/v1/auth/login",
        json={"email": "nadie@example.com", "password": PASSWORD},
    )

    assert wrong_password.status_code == 401
    assert unknown_email.status_code == 401
    assert wrong_password.json() == unknown_email.json()
    assert wrong_password.json()["code"] == "invalid_credentials"


def test_me_with_valid_token_returns_user(api_client):
    register = _register(api_client)
    token = register.json()["access_token"]

    response = api_client.get("/api/v1/auth/me", headers=_auth_header(token))

    assert response.status_code == 200
    assert response.json() == register.json()["user"]


def _signed_token(subject: str, secret: str, expires_delta: timedelta) -> str:
    now = datetime.now(UTC)
    return jwt.encode(
        {
            "sub": subject,
            "iat": now,
            "exp": now + expires_delta,
        },
        secret,
        algorithm="HS256",
    )


def _tamper_signature(token: str) -> str:
    replacement = "a" if not token.endswith("a") else "b"
    return token[:-1] + replacement


def test_me_without_header_returns_invalid_token(api_client):
    response = api_client.get("/api/v1/auth/me")

    assert response.status_code == 401
    assert response.json()["code"] == "invalid_token"


@pytest.mark.parametrize("case", ["expired", "tampered", "other_secret", "bad_sub"])
def test_me_with_invalid_token_returns_invalid_token(api_client, case):
    register = _register(api_client)
    token = register.json()["access_token"]
    user_id = register.json()["user"]["id"]

    if case == "expired":
        token = _signed_token(user_id, settings.jwt_secret, timedelta(seconds=-60))
    elif case == "tampered":
        token = _tamper_signature(token)
    elif case == "other_secret":
        token = _signed_token(user_id, OTHER_SECRET, timedelta(minutes=10))
    elif case == "bad_sub":
        token = _signed_token(
            "no-es-un-uuid", settings.jwt_secret, timedelta(minutes=10)
        )

    response = api_client.get("/api/v1/auth/me", headers=_auth_header(token))

    assert response.status_code == 401
    assert response.json()["code"] == "invalid_token"


def test_me_with_deleted_user_returns_invalid_token(api_client):
    token, _ = create_access_token(uuid.uuid4())

    response = api_client.get("/api/v1/auth/me", headers=_auth_header(token))

    assert response.status_code == 401
    assert response.json()["code"] == "invalid_token"


def _assert_no_credentials(data):
    forbidden = {"password", "password_hash"}
    if isinstance(data, dict):
        assert forbidden.isdisjoint(data)
        for value in data.values():
            _assert_no_credentials(value)
    elif isinstance(data, list):
        for value in data:
            _assert_no_credentials(value)


def test_responses_never_include_password_or_hash(api_client):
    register = _register(api_client)
    login = api_client.post(
        "/api/v1/auth/login",
        json={"email": "ana.perez@example.com", "password": PASSWORD},
    )
    me = api_client.get(
        "/api/v1/auth/me",
        headers=_auth_header(register.json()["access_token"]),
    )

    for response in (register, login, me):
        assert response.status_code in (200, 201)
        assert "password" not in response.text
        assert "password_hash" not in response.text
        _assert_no_credentials(response.json())


def test_logs_do_not_contain_password_or_token(api_client, caplog):
    with caplog.at_level(logging.INFO):
        register = _register(api_client)
        token = register.json()["access_token"]
        api_client.post(
            "/api/v1/auth/login",
            json={"email": "ana.perez@example.com", "password": PASSWORD},
        )
        api_client.get("/api/v1/auth/me", headers=_auth_header(token))

    assert PASSWORD not in caplog.text
    assert token not in caplog.text
    assert "password_hash" not in caplog.text
