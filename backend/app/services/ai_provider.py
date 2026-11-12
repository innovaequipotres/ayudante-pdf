"""Selector del proveedor de IA configurado.

Gemini sigue siendo el proveedor por defecto. OpenRouter se usa solo si
``AI_PROVIDER=openrouter`` y están configuradas la clave y el modelo.
"""

from __future__ import annotations

import logging

from app.core.config import get_settings
from app.services.gemini import StructuredAI, get_gemini_service
from app.services.openrouter import get_openrouter_service

logger = logging.getLogger(__name__)

__all__ = ["get_ai_service", "get_provider_label"]


def _provider_name() -> str:
    """Devuelve el proveedor configurado en minúsculas."""
    return ((get_settings().ai_provider or "gemini")).strip().lower()


def get_provider_label() -> str:
    """Devuelve el nombre visible del proveedor configurado.

    Se usa en el aviso de privacidad incluso cuando el servicio no está
    disponible, para que el aviso nombre al proveedor real.
    """
    if _provider_name() == "openrouter":
        model = (get_settings().openrouter_model or "").strip()
        if model:
            return f"OpenRouter y el proveedor del modelo {model}"
        return "OpenRouter (modelo no configurado)"
    return "Google Gemini"


def get_ai_service() -> StructuredAI | None:
    """Devuelve el servicio del proveedor configurado, o ``None``.

    Un proveedor desconocido, o la falta de clave/modelo, deshabilitan el
    análisis con IA con un warning que no expone credenciales.
    """
    provider = _provider_name()

    if provider == "gemini":
        return get_gemini_service()

    if provider == "openrouter":
        return get_openrouter_service()

    logger.warning(
        "Proveedor de IA desconocido: %s. Se deshabilita el análisis con IA.",
        provider,
    )
    return None
