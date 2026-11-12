"""Modelos del análisis semántico con IA."""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field

from app.schemas.observation import Observation


class AiStatus(str, Enum):
    """Resultado del análisis semántico."""

    OK = "ok"
    UNAVAILABLE = "unavailable"


def build_ai_notice(truncated: bool, provider: str = "Google Gemini") -> str:
    """Arma el aviso de privacidad del análisis con IA.

    Args:
        truncated: Si solo se analizó una parte del material.
        provider: Nombre del proveedor que recibe el texto. Para OpenRouter
            incluye el modelo elegido, porque el texto también llega al
            proveedor que lo sirve.

    Returns:
        El aviso para mostrar junto al diagnóstico.
    """
    if provider.strip().lower().startswith("openrouter"):
        notice = (
            f"El análisis con IA envía el texto del material a {provider}. "
            "Ese proveedor puede registrar o usar los prompts según su "
            "política de datos; revisala antes de analizar materiales. "
            "No uses material con datos personales de estudiantes."
        )
    else:
        notice = (
            f"El análisis con IA envía el texto del material a {provider}. "
            "No se envía el archivo, solo el texto extraído."
        )

    if truncated:
        notice += (
            " Por la extensión del material, se analizó solo una parte del "
            "texto."
        )
    return notice


# Aviso por defecto (Gemini), para quien no necesite distinguir proveedores.
AI_NOTICE = build_ai_notice(False)


class AiAnalysisResult(BaseModel):
    """Resultado del análisis semántico de un material."""

    status: AiStatus = Field(
        description="Indica si el análisis con IA se pudo completar.",
    )
    notice: str = Field(
        description="Aviso de privacidad y de alcance del análisis.",
    )
    truncated: bool = Field(
        default=False,
        description="Indica si solo se analizó una parte del material.",
    )
    observations: list[Observation] = Field(
        default_factory=list,
        description="Observaciones semánticas validadas contra el material.",
    )
