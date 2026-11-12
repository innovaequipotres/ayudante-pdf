"""Cliente de Google Gemini para generar respuestas estructuradas.

El escáner semántico solo necesita que un proveedor reciba instrucciones y
material por separado y devuelva un JSON que cumpla un esquema de Pydantic.
``StructuredAI`` define ese contrato; ``GeminiService`` lo implementa con el
SDK ``google-genai``.

El material del estudiante nunca se registra en los logs: solo se informa qué
proveedor falló, sin incluir el texto enviado ni la clave.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from functools import lru_cache
from typing import Protocol, runtime_checkable

from pydantic import BaseModel

from app.core.config import get_settings

logger = logging.getLogger(__name__)

__all__ = [
    "AiUnavailableError",
    "GeminiConfig",
    "GeminiService",
    "StructuredAI",
    "get_gemini_service",
    "load_config",
]

_UNAVAILABLE_MESSAGE = (
    "El servicio de IA no está disponible en este momento. "
    "El diagnóstico por reglas sigue funcionando."
)


class AiUnavailableError(Exception):
    """La IA no está configurada, no respondió o devolvió algo inválido."""


@runtime_checkable
class StructuredAI(Protocol):
    """Contrato mínimo que debe cumplir un proveedor de IA."""

    provider_name: str

    def generate_structured(
        self,
        *,
        instructions: str,
        material: str,
        schema: type[BaseModel],
    ) -> str:
        """Genera una respuesta JSON que cumple ``schema``.

        Args:
            instructions: Indicaciones del sistema (nunca se mezclan con el
                material).
            material: Texto del material a analizar.
            schema: Modelo de Pydantic que describe la respuesta esperada.

        Returns:
            El JSON devuelto por el proveedor, sin validar. La validación del
            esquema la hace ``ai_analysis`` (o el propio proveedor).

        Raises:
            AiUnavailableError: Si el proveedor no está disponible, expira el
                tiempo de espera o devuelve una respuesta vacía.
        """


@dataclass(frozen=True)
class GeminiConfig:
    """Parámetros necesarios para usar Gemini."""

    api_key: str
    model: str


def load_config() -> GeminiConfig | None:
    """Lee la configuración de Gemini desde el entorno.

    Returns:
        La configuración, o ``None`` si falta la clave o el modelo. En ese caso
        deja un warning sin exponer la clave.
    """
    settings = get_settings()
    api_key = (settings.gemini_api_key or "").strip()
    model = (settings.gemini_model or "").strip()
    if not api_key or not model:
        logger.warning(
            "Gemini deshabilitado: falta GEMINI_API_KEY o GEMINI_MODEL."
        )
        return None
    return GeminiConfig(api_key=api_key, model=model)


class GeminiService:
    """Implementación de ``StructuredAI`` con Google Gemini."""

    provider_name = "Google Gemini"

    def __init__(self, config: GeminiConfig, client: object | None = None) -> None:
        self._config = config
        # El cliente se inyecta en los tests para no hacer llamadas de red.
        self._client = client

    @property
    def client(self) -> object:
        """Crea el cliente de Gemini la primera vez que se usa."""
        if self._client is None:
            from google import genai

            self._client = genai.Client(api_key=self._config.api_key)
        return self._client

    def generate_structured(
        self,
        *,
        instructions: str,
        material: str,
        schema: type[BaseModel],
    ) -> str:
        """Pide a Gemini un JSON que cumpla ``schema``.

        Raises:
            AiUnavailableError: Ante cualquier error del SDK, un timeout o una
                respuesta vacía.
        """
        try:
            from google.genai import types
        except ImportError as exc:  # pragma: no cover - depende del entorno
            raise AiUnavailableError(_UNAVAILABLE_MESSAGE) from exc

        try:
            response = self.client.models.generate_content(  # type: ignore[attr-defined]
                model=self._config.model,
                contents=material,
                config=types.GenerateContentConfig(
                    system_instruction=instructions,
                    response_mime_type="application/json",
                    response_schema=schema,
                ),
            )
        except Exception as exc:
            # No se incluye el material ni la clave en el mensaje.
            logger.warning("Gemini no pudo completar el análisis: %s", type(exc).__name__)
            raise AiUnavailableError(_UNAVAILABLE_MESSAGE) from exc

        text = getattr(response, "text", None)
        if text is None or not str(text).strip():
            logger.warning("Gemini devolvió una respuesta vacía.")
            raise AiUnavailableError(_UNAVAILABLE_MESSAGE)
        return str(text)


@lru_cache
def get_gemini_service() -> GeminiService | None:
    """Devuelve el servicio de Gemini o ``None`` si no está configurado."""
    config = load_config()
    if config is None:
        return None
    return GeminiService(config)
