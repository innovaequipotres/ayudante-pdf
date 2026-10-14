from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Ayudante PDF Backend",
    description="Backend para el procesamiento de PDFs e integración con IA",
    version="1.0.0"
)

# Configuración de CORS para permitir conexiones desde el frontend (ej. Astro, React, etc.)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción podés restringirlo a tu dominio o puerto del frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "¡El backend de Ayudante PDF está funcionando correctamente! 🚀"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}