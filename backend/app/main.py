from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.exceptions import register_exception_handlers

app = FastAPI(
    title="Ayudante PDF Backend",
    description="Backend para el procesamiento de PDFs e integración con IA",
    version="1.0.0",
)

# Si se permite cualquier origen, no se pueden enviar credenciales (restricción del navegador).
allow_all_origins = "*" in settings.cors_origin_list

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=not allow_all_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

register_exception_handlers(app)


@app.get("/")
def read_root():
    return {"message": "¡El backend de Ayudante PDF está funcionando correctamente! 🚀"}


@app.get("/health")
def health_check():
    return {"status": "healthy"}
