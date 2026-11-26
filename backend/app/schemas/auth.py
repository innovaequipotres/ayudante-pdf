from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


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
