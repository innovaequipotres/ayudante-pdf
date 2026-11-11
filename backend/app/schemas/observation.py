"""Modelos de las observaciones que produce el escáner de accesibilidad."""

from enum import Enum

from pydantic import BaseModel, Field


class Category(str, Enum):
    """Dimensión de accesibilidad a la que pertenece una regla."""

    COMPREHENSION = "comprehension"
    STRUCTURE = "structure"
    VISUAL = "visual"
    REPRESENTATION = "representation"
    MULTIMEDIA = "multimedia"
    NAVIGATION = "navigation"


class Severity(str, Enum):
    """Gravedad de una observación.

    ``high`` equivale a una barrera, ``medium`` a algo para revisar y ``low`` a
    una mejora sugerida. La interfaz los muestra como Alta, Media y Baja.
    """

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class ObservationSource(str, Enum):
    """Origen de la observación."""

    RULE = "rule"
    AI = "ai"


class Observation(BaseModel):
    """Problema de accesibilidad detectado en un punto del material."""

    id: str = Field(
        description=(
            "Identificador estable de la observación. Se arma con la regla y "
            "el bloque afectado."
        ),
    )
    rule_id: str = Field(description="Código de la regla que la produjo.")
    category: Category = Field(description="Dimensión de accesibilidad.")
    severity: Severity = Field(description="Gravedad de la observación.")
    source: ObservationSource = Field(
        default=ObservationSource.RULE,
        description="Origen: regla automática o análisis con IA.",
    )
    title: str = Field(description="Nombre corto del problema.")
    detail: str | None = Field(
        default=None,
        description="Dato puntual que explica la observación.",
    )
    why_it_matters: str = Field(
        description="Por qué el problema afecta el acceso al material.",
    )
    recommendation: str = Field(description="Qué hacer para resolverlo.")
    block_id: str | None = Field(
        default=None,
        description=(
            "Bloque afectado. Es nulo cuando el problema abarca todo el material."
        ),
    )
    page: int | None = Field(
        default=None,
        ge=1,
        description="Página del bloque afectado; nula en texto pegado.",
    )
    excerpt: str | None = Field(
        default=None,
        description="Fragmento del material que ubica el problema.",
    )
