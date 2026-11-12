"""Cliente de OpenRouter para generar respuestas estructuradas.

OpenRouter expone una API compatible con la de OpenAI, así que se usa el SDK
``openai`` apuntando a su ``base_url``. El nivel de soporte de *structured
outputs* depende del modelo elegido: por eso se exige que el endpoint declare
soportar todos los parámetros enviados y, si la API rechaza el
``response_format``, se reintenta una sola vez en modo ``json_object``.

El material y la clave nunca se registran en los logs.
"""

from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass
from functools import lru_cache
from typing import Any

from pydantic import BaseModel, ValidationError

from app.core.config import get_settings
from app.services.gemini import AiUnavailableError

logger = logging.getLogger(__name__)

__all__ = [
    "OpenRouterConfig",
    "OpenRouterService",
    "build_response_schema",
    "get_openrouter_service",
    "load_config",
]

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

_UNAVAILABLE_MESSAGE = (
    "El servicio de IA no está disponible en este momento. "
    "El diagnóstico por reglas sigue funcionando."
)

# Cercas de código que algunos modelos agregan alrededor del JSON.
_FENCE_RE = re.compile(
    r"^\s*```(?:json)?\s*(?P<body>.*?)\s*```\s*$",
    re.DOTALL | re.IGNORECASE,
)


@dataclass(frozen=True)
class OpenRouterConfig:
    """Parámetros necesarios para usar OpenRouter."""

    api_key: str
    model: str
    app_name: str = "Ayudante PDF"
    referer: str = ""
    timeout: float = 30.0


def load_config() -> OpenRouterConfig | None:
    """Lee la configuración de OpenRouter desde el entorno.

    Returns:
        La configuración, o ``None`` si falta la clave o el modelo. En ese caso
        deja un warning sin exponer la clave.
    """
    settings = get_settings()
    api_key = (settings.openrouter_api_key or "").strip()
    model = (settings.openrouter_model or "").strip()
    if not api_key or not model:
        logger.warning(
            "OpenRouter deshabilitado: falta OPENROUTER_API_KEY u "
            "OPENROUTER_MODEL."
        )
        return None
    return OpenRouterConfig(
        api_key=api_key,
        model=model,
        app_name=(settings.openrouter_app_name or "").strip(),
        referer=(settings.openrouter_referer or "").strip(),
        timeout=settings.openrouter_timeout_seconds,
    )


def _resolve_refs(node: Any, defs: dict[str, Any], seen: tuple[str, ...] = ()) -> Any:
    """Reemplaza los ``$ref`` de Pydantic por las definiciones inlineadas."""
    if isinstance(node, dict):
        ref = node.get("$ref")
        if isinstance(ref, str) and ref.startswith("#/$defs/"):
            name = ref.rsplit("/", 1)[-1]
            if name in seen:  # Esquema recursivo: se deja la referencia.
                return dict(node)
            target = defs.get(name, {})
            resolved = _resolve_refs(target, defs, seen + (name,))
            extra = {key: value for key, value in node.items() if key != "$ref"}
            if extra:
                resolved = {**resolved, **extra}
            return _resolve_refs(resolved, defs, seen)
        return {key: _resolve_refs(value, defs, seen) for key, value in node.items()}
    if isinstance(node, list):
        return [_resolve_refs(item, defs, seen) for item in node]
    return node


def _close_objects(node: Any) -> Any:
    """Marca los objetos como estrictos: sin claves extra y todas requeridas."""
    if isinstance(node, dict):
        result = {key: _close_objects(value) for key, value in node.items()}
        if result.get("type") == "object" and "properties" in result:
            result["additionalProperties"] = False
            result["required"] = list(result["properties"].keys())
        return result
    if isinstance(node, list):
        return [_close_objects(item) for item in node]
    return node


def build_response_schema(schema: type[BaseModel]) -> dict[str, Any]:
    """Arma el JSON Schema estricto que espera el modo ``json_schema``.

    Pydantic genera ``$defs`` y ``$ref``; los proveedores que soportan salidas
    estructuradas esperan las definiciones inlineadas, ``additionalProperties``
    en ``false`` y todos los campos en ``required``.
    """
    raw = schema.model_json_schema()
    defs = raw.pop("$defs", {})
    resolved = _resolve_refs(raw, defs)
    return _close_objects(resolved)


def _messages(instructions: str, material: str) -> list[dict[str, str]]:
    """Separa siempre las instrucciones (system) del material (user)."""
    return [
        {"role": "system", "content": instructions},
        {"role": "user", "content": material},
    ]


def _strip_fences(text: str) -> str:
    """Quita las cercas de código que algunos modelos agregan al JSON."""
    match = _FENCE_RE.match(text)
    return match.group("body") if match else text


def _content_from(response: object) -> str:
    """Extrae el texto de la primera opción de la respuesta."""
    choices = getattr(response, "choices", None)
    if not choices:
        raise AiUnavailableError(_UNAVAILABLE_MESSAGE)
    message = getattr(choices[0], "message", None)
    content = getattr(message, "content", None)
    if content is None or not str(content).strip():
        raise AiUnavailableError(_UNAVAILABLE_MESSAGE)
    return str(content)


class OpenRouterService:
    """Implementación de ``StructuredAI`` con OpenRouter."""

    def __init__(self, config: OpenRouterConfig, client: object | None = None) -> None:
        self._config = config
        # El cliente se inyecta en los tests para no hacer llamadas de red.
        self._client = client

    @property
    def provider_name(self) -> str:
        """Nombre del proveedor, con el modelo elegido."""
        return f"OpenRouter y el proveedor del modelo {self._config.model}"

    @property
    def client(self) -> object:
        """Crea el cliente de OpenAI apuntando a OpenRouter la primera vez."""
        if self._client is None:
            from openai import OpenAI

            headers: dict[str, str] = {}
            if self._config.referer:
                headers["HTTP-Referer"] = self._config.referer
            if self._config.app_name:
                headers["X-Title"] = self._config.app_name

            self._client = OpenAI(
                api_key=self._config.api_key,
                base_url=OPENROUTER_BASE_URL,
                timeout=self._config.timeout,
                default_headers=headers or None,
            )
        return self._client

    def _create(
        self,
        instructions: str,
        material: str,
        response_format: dict[str, Any],
    ) -> object:
        """Hace una llamada al endpoint de chat completions."""
        return self.client.chat.completions.create(  # type: ignore[attr-defined]
            model=self._config.model,
            messages=_messages(instructions, material),
            response_format=response_format,
            extra_body={"provider": {"require_parameters": True}},
        )

    def generate_structured(
        self,
        *,
        instructions: str,
        material: str,
        schema: type[BaseModel],
    ) -> str:
        """Pide a OpenRouter un JSON que cumpla ``schema``.

        Si el primer intento falla con un 400 (el endpoint no acepta
        ``json_schema``), reintenta **una sola vez** con ``json_object`` y el
        esquema agregado a las instrucciones. Cualquier otro error se traduce a
        ``AiUnavailableError``; los 429 no se reintentan.

        Raises:
            AiUnavailableError: Ante errores de la API, timeouts, respuestas
                vacías o JSON/esquema inválidos.
        """
        schema_payload = build_response_schema(schema)
        response_format = {
            "type": "json_schema",
            "json_schema": {
                "name": schema.__name__,
                "strict": True,
                "schema": schema_payload,
            },
        }

        try:
            response = self._create(instructions, material, response_format)
        except Exception as exc:
            if getattr(exc, "status_code", None) != 400:
                logger.warning(
                    "OpenRouter no pudo completar el análisis: %s",
                    type(exc).__name__,
                )
                raise AiUnavailableError(_UNAVAILABLE_MESSAGE) from exc

            # Fallback único para endpoints sin soporte de json_schema.
            fallback_instructions = (
                f"{instructions}\n\n"
                "Respondé únicamente con un objeto JSON que cumpla este "
                "esquema:\n"
                f"{json.dumps(schema_payload, ensure_ascii=False)}"
            )
            try:
                response = self._create(
                    fallback_instructions,
                    material,
                    {"type": "json_object"},
                )
            except Exception as fallback_exc:
                logger.warning(
                    "OpenRouter no pudo completar el análisis: %s",
                    type(fallback_exc).__name__,
                )
                raise AiUnavailableError(_UNAVAILABLE_MESSAGE) from fallback_exc

        text = _strip_fences(_content_from(response))
        try:
            schema.model_validate_json(text)
        except (ValidationError, ValueError) as exc:
            logger.warning("OpenRouter devolvió un JSON que no cumple el esquema.")
            raise AiUnavailableError(_UNAVAILABLE_MESSAGE) from exc
        return text


@lru_cache
def get_openrouter_service() -> OpenRouterService | None:
    """Devuelve el servicio de OpenRouter o ``None`` si no está configurado."""
    config = load_config()
    if config is None:
        return None
    return OpenRouterService(config)
