from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException


class AppError(Exception):
    """Error de aplicación con formato de respuesta {code, message}."""

    def __init__(self, code: str, message: str, status_code: int = 400) -> None:
        self.code = code
        self.message = message
        self.status_code = status_code
        super().__init__(message)


def _error_response(status_code: int, code: str, message: str) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={"code": code, "message": message},
    )


async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    return _error_response(exc.status_code, exc.code, exc.message)


async def validation_error_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    details = []
    for error in exc.errors():
        # Se omite la primera parte de loc ("body", "query", etc.)
        location = ".".join(str(part) for part in error["loc"][1:])
        details.append(f"{location}: {error['msg']}" if location else error["msg"])

    return _error_response(
        422,
        "VALIDATION_ERROR",
        "; ".join(details) or "Datos de entrada inválidos",
    )


async def http_exception_handler(
    request: Request, exc: StarletteHTTPException
) -> JSONResponse:
    message = exc.detail if isinstance(exc.detail, str) else str(exc.detail)
    return _error_response(exc.status_code, f"HTTP_{exc.status_code}", message)


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    return _error_response(500, "INTERNAL_ERROR", "Error interno del servidor")


def register_exception_handlers(app: FastAPI) -> None:
    """Registra los manejadores globales de errores con formato {code, message}."""
    app.add_exception_handler(AppError, app_error_handler)
    app.add_exception_handler(RequestValidationError, validation_error_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(Exception, unhandled_exception_handler)
