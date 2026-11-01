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

| Variable         | Descripción                             | Default                                                                                   |
| ---------------- | --------------------------------------- | ----------------------------------------------------------------------------------------- |
| `GEMINI_API_KEY` | Clave de API de Google Gemini           | _(vacío)_                                                                                 |
| `GEMINI_MODEL`   | Modelo de Gemini a utilizar             | `gemini-2.0-flash`                                                                        |
| `MAX_UPLOAD_MB`  | Tamaño máximo de PDF permitido (MB)     | `25`                                                                                      |
| `CORS_ORIGINS`   | Orígenes permitidos, separados por coma | `http://localhost:3000,http://127.0.0.1:3000,http://localhost:8000,http://127.0.0.1:8000` |

## Ejecutar el proyecto

```bash
fastapi dev app/main.py
```

El servidor queda disponible en:

- API: <http://127.0.0.1:8000>
- Documentación interactiva (Swagger UI): <http://127.0.0.1:8000/docs>
- Documentación alternativa (ReDoc): <http://127.0.0.1:8000/redoc>

## Endpoints de sesiones

Todas las rutas están bajo el prefijo `/api/v1`. Una **sesión** representa un
material educativo cargado (un PDF o un texto pegado) sobre el que luego se
trabajará en las siguientes etapas.

| Método | Ruta                            | Descripción                                                                 |
| ------ | ------------------------------- | --------------------------------------------------------------------------- |
| `POST` | `/api/v1/sessions/file`         | Crea una sesión desde un archivo PDF (`multipart/form-data`, campo `file`). |
| `POST` | `/api/v1/sessions/text`         | Crea una sesión desde un texto pegado (`application/json`).                 |
| `GET`  | `/api/v1/sessions/{session_id}` | Devuelve una sesión por su identificador.                                   |

Cuerpo esperado para `POST /api/v1/sessions/text`:

```json
{
  "title": "Título opcional (máximo 200 caracteres)",
  "text": "Contenido del texto"
}
```

Toda sesión nueva queda en estado `uploaded`. Los estados posibles son
`uploaded`, `extracted`, `analyzed` y `completed` (los últimos se usan en
issues posteriores).

Errores propios de estos endpoints:

| HTTP  | `code`               | Cuándo                                      |
| ----- | -------------------- | ------------------------------------------- |
| `400` | `empty_content`      | Archivo vacío, o texto vacío/solo espacios. |
| `400` | `invalid_pdf`        | El archivo no empieza con la firma `%PDF`.  |
| `404` | `session_not_found`  | La sesión indicada no existe.               |
| `413` | `file_too_large`     | El archivo supera `MAX_UPLOAD_MB`.          |
| `415` | `unsupported_format` | La extensión del archivo no es `.pdf`.      |

Ejemplos:

```bash
# PDF
curl -X POST http://127.0.0.1:8000/api/v1/sessions/file \
  -F "file=@documento.pdf"

# Texto
curl -X POST http://127.0.0.1:8000/api/v1/sessions/text \
  -H "Content-Type: application/json" \
  -d '{"title": "Biología", "text": "La célula es la unidad básica de la vida."}'

# Consultar sesión
curl http://127.0.0.1:8000/api/v1/sessions/<session_id>
```

## Endpoints de contenido

Una vez creada la sesión, estos endpoints extraen y consultan sus bloques de
contenido (títulos, párrafos, listas e imágenes).

| Método | Ruta                                    | Descripción                                             |
| ------ | --------------------------------------- | ------------------------------------------------------- |
| `POST` | `/api/v1/sessions/{session_id}/extract` | Extrae el contenido y marca la sesión como `extracted`. |
| `GET`  | `/api/v1/sessions/{session_id}/content` | Devuelve el contenido ya extraído.                      |

El primer `POST` procesa el material. Si se repite, devuelve el contenido
guardado sin volver a procesarlo. Un `GET` antes de la extracción responde
`409 content_not_extracted`.

Errores propios de estos endpoints:

| HTTP  | `code`                  | Cuándo                                                      |
| ----- | ----------------------- | ----------------------------------------------------------- |
| `404` | `session_not_found`     | La sesión indicada no existe.                               |
| `409` | `content_not_extracted` | Todavía no se llamó a `POST /extract`.                      |
| `422` | `no_extractable_text`   | El material no tiene texto (por ejemplo, un PDF escaneado). |
| `422` | `invalid_pdf`           | El PDF está dañado o protegido.                             |

Ejemplos:

```bash
# Extraer contenido
curl -X POST http://127.0.0.1:8000/api/v1/sessions/<session_id>/extract

# Consultar contenido extraído
curl http://127.0.0.1:8000/api/v1/sessions/<session_id>/content
```

> **Almacenamiento temporal:** por ahora las sesiones y los contenidos extraídos
> viven en memoria del proceso. Se pierden al reiniciar el servidor y no se
> comparten entre workers. Más adelante se reemplazarán por una base de datos.
> proceso. Se pierden al reiniciar el servidor y no se comparten entre workers.
> Más adelante se reemplazarán por una base de datos.

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

raise AppError(code="invalid_pdf", message="El archivo no es un PDF válido.", status_code=400)
```

## Estructura

```
backend/
├── app/
│   ├── api/
│   │   └── v1/
│   │       └── endpoints/
│   │           ├── content.py     # Endpoints de contenido
│   │           └── sessions.py    # Endpoints de sesiones
│   ├── core/
│   │   ├── config.py              # Configuración y variables de entorno
│   │   └── exceptions.py          # Errores globales con formato {code, message}
│   ├── processors/
│   │   ├── pdf_processor.py       # Extracción de bloques desde PDFs
│   │   └── text_processor.py      # Extracción de bloques desde texto plano
│   ├── schemas/
│   │   ├── common.py              # ErrorResponse
│   │   ├── content.py             # ContentBlock, ContentSummary, ExtractedContent
│   │   └── session.py             # SourceType, SessionStatus, TextInput, SessionResponse
│   ├── services/
│   │   ├── content_service.py     # Extracción y resumen de contenido
│   │   └── session_service.py     # Lógica de sesiones (almacenamiento en memoria)
│   └── main.py                    # Punto de entrada de FastAPI, CORS y routers
├── tests/
│   ├── conftest.py
│   ├── test_content.py
│   ├── test_pdf_processor.py
│   ├── test_sessions.py
│   └── test_text_processor.py
├── .env.example
├── requirements.txt
├── requirements-dev.txt
└── pytest.ini
```
