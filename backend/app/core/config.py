from functools import lru_cache
from pathlib import Path

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Directorio raíz del backend (backend/)
BASE_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    """Configuración de la aplicación, leída desde variables de entorno y .env."""

    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    ai_provider: str = "gemini"
    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.0-flash"
    openrouter_api_key: str = ""
    # Sin modelo por defecto: los nombres cambian y los disponibles dependen de
    # la cuenta. Elegir uno en https://openrouter.ai/models filtrando por
    # structured_outputs. Los modelos :free tienen límites de uso variables.
    openrouter_model: str = ""
    openrouter_app_name: str = "Ayudante PDF"
    openrouter_referer: str = ""
    openrouter_timeout_seconds: float = 30.0
    max_upload_mb: int = 25
    cors_origins: str = (
        "http://localhost:3000,http://127.0.0.1:3000,"
        "http://localhost:8000,http://127.0.0.1:8000"
    )
    # Sin valor por defecto para no hardcodear credenciales. Si falta, la app
    # arranca igual y la base falla con un error claro al usarse.
    database_url: str = ""
    test_database_url: str = ""

    # Secreto para firmar los JWT. Sin valor por defecto inseguro: si falta, la
    # app arranca pero el login y la validación de tokens fallan con un error
    # claro. Generar con: python -c "import secrets; print(secrets.token_urlsafe(64))"
    jwt_secret: str = ""
    jwt_expire_minutes: int = 1440

    @field_validator("database_url", "test_database_url")
    @classmethod
    def validate_postgres_url(cls, value: str) -> str:
        """Exige el driver psycopg 3; ``postgresql://`` usaría psycopg2."""
        value = value.strip()
        if value and not value.startswith("postgresql+psycopg://"):
            raise ValueError(
                "La URL debe empezar con postgresql+psycopg:// (driver psycopg 3)."
            )
        return value

    @property
    def max_upload_bytes(self) -> int:
        """Devuelve el tamaño máximo de subida en bytes."""
        return self.max_upload_mb * 1024 * 1024

    @property
    def cors_origin_list(self) -> list[str]:
        """Devuelve los orígenes de CORS como lista, ignorando espacios vacíos."""
        return [
            origin.strip() for origin in self.cors_origins.split(",") if origin.strip()
        ]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
