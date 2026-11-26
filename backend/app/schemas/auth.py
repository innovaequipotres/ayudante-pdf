from datetime import datetime
from typing import TYPE_CHECKING, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

if TYPE_CHECKING:
    from app.models.user import User


class UserCreate(BaseModel):
    first_name: str = Field(min_length=1)
    last_name: str = Field(min_length=1)
    phone: str | None = None
    email: EmailStr
    password: str = Field(min_length=1)

    @field_validator("first_name", "last_name", mode="before")
    @classmethod
    def strip_names(cls, value: object) -> object:
        if isinstance(value, str):
            return value.strip()
        return value

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        return value.strip().lower()

    @field_validator("phone", mode="before")
    @classmethod
    def strip_phone(cls, value: object) -> object:
        if isinstance(value, str):
            return value.strip() or None
        return value


class UserPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    first_name: str
    last_name: str
    phone: str | None
    email: EmailStr
    role: str
    created_at: datetime


class RegisterRequest(BaseModel):
    """Datos de alta de un usuario. El email se normaliza a minúsculas."""

    first_name: str = Field(min_length=1)
    last_name: str = Field(min_length=1)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    phone: str | None = None

    @field_validator("first_name", "last_name", mode="before")
    @classmethod
    def strip_names(cls, value: object) -> object:
        if isinstance(value, str):
            return value.strip()
        return value

    @field_validator("email", mode="before")
    @classmethod
    def normalize_email(cls, value: object) -> object:
        if isinstance(value, str):
            return value.strip().lower()
        return value

    @field_validator("phone", mode="before")
    @classmethod
    def strip_phone(cls, value: object) -> object:
        if isinstance(value, str):
            return value.strip() or None
        return value


class LoginRequest(BaseModel):
    email: EmailStr
    password: str

    @field_validator("email", mode="before")
    @classmethod
    def normalize_email(cls, value: object) -> object:
        if isinstance(value, str):
            return value.strip().lower()
        return value


class UserResponse(BaseModel):
    """Usuario expuesto por la API. Nunca incluye contraseña ni hash."""

    id: UUID
    email: EmailStr
    full_name: str
    role: str
    created_at: datetime

    @classmethod
    def from_user(cls, user: "User") -> "UserResponse":
        full_name = " ".join(
            part for part in (user.first_name, user.last_name) if part
        ).strip()
        return cls(
            id=user.id,
            email=user.email,
            full_name=full_name,
            role=user.role,
            created_at=user.created_at,
        )


class AuthResponse(BaseModel):
    access_token: str
    token_type: Literal["bearer"] = "bearer"
    expires_in: int
    user: UserResponse
