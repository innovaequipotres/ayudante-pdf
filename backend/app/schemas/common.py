from pydantic import BaseModel


class ErrorResponse(BaseModel):
    """Formato estándar de las respuestas de error de la API."""

    code: str
    message: str
