# Ayudante PDF — Backend

Backend de la aplicación **Ayudante PDF**, construido con **FastAPI**. Expone la API que
procesa documentos PDF y se integra con **Google Gemini**.

## Requisitos

- **Python 3.11** (ver `.python-version`)
- pip

## Instalación

Desde la carpeta `backend/`:

```bash
# 1. Crear el entorno virtual
python -m venv .venv

# 2. Activarlo
source .venv/bin/activate        # Linux / macOS
# .venv\Scripts\activate         # Windows

# 3. Instalar dependencias
pip install --upgrade pip
pip install -r requirements.txt
```

Para desarrollo y tests, instalá también las dependencias de desarrollo:

```bash
pip install -r requirements-dev.txt
```

## Variables de entorno

Copiá el archivo de ejemplo y completá los valores:

```bash
cp .env.example .env
```

El archivo `.env` está en `.gitignore` y **no debe subirse al repositorio**.

| Variable | Descripción | Default |
| --- | --- | --- |
| `GEMINI_API_KEY` | Clave de API de Google Gemini | *(vacío)* |
| `GEMINI_MODEL` | Modelo de Gemini a utilizar | `gemini-2.0-flash` |
| `MAX_UPLOAD_MB` | Tamaño máximo de PDF permitido (MB) | `10` |
| `CORS_ORIGINS` | Orígenes permitidos, separados por coma | `http://localhost:3000,http://127.0.0.1:3000,http://localhost:8000,http://127.0.0.1:8000` |

## Ejecutar el proyecto

```bash
fastapi dev app/main.py
```

El servidor queda disponible en:

- API: <http://127.0.0.1:8000>
- Documentación interactiva (Swagger UI): <http://127.0.0.1:8000/docs>
- Documentación alternativa (ReDoc): <http://127.0.0.1:8000/redoc>

## Tests

```bash
pytest
```

## Formato de errores

Todas las respuestas de error de la API usan el formato:

```json
{
  "code": "VALIDATION_ERROR",
  "message": "Descripción del error"
}
```

Los errores de aplicación se lanzan con `AppError` (definido en `app/core/exceptions.py`):

```python
from app.core.exceptions import AppError

raise AppError(code="INVALID_PDF", message="El archivo no es un PDF válido", status_code=400)
```

## Estructura

```
backend/
├── app/
│   ├── core/
│   │   ├── config.py        # Configuración y variables de entorno
│   │   └── exceptions.py    # Errores globales con formato {code, message}
│   └── main.py              # Punto de entrada de FastAPI y CORS
├── .env.example
├── requirements.txt
├── requirements-dev.txt
└── pytest.ini
```
