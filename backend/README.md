# Ayudante PDF — Backend

Backend de la aplicación **Ayudante PDF**, construido con **FastAPI**. Expone la API que
procesa documentos PDF y se integra con **Google Gemini** u **OpenRouter** para el
análisis semántico con IA.

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

| Variable                     | Descripción                                     | Default                                                                                   |
| ---------------------------- | ----------------------------------------------- | ----------------------------------------------------------------------------------------- |
| `AI_PROVIDER`                | Proveedor de IA: `gemini` u `openrouter`        | `gemini`                                                                                  |
| `GEMINI_API_KEY`             | Clave de API de Google Gemini                   | _(vacío)_                                                                                 |
| `GEMINI_MODEL`               | Modelo de Gemini a utilizar                     | `gemini-2.0-flash`                                                                        |
| `OPENROUTER_API_KEY`         | Clave de API de OpenRouter                      | _(vacío)_                                                                                 |
| `OPENROUTER_MODEL`           | Modelo de OpenRouter (sin valor por defecto)    | _(vacío)_                                                                                 |
| `OPENROUTER_APP_NAME`        | Nombre enviado en el header `X-Title`           | `Ayudante PDF`                                                                            |
| `OPENROUTER_REFERER`         | URL opcional enviada en `HTTP-Referer`          | _(vacío)_                                                                                 |
| `OPENROUTER_TIMEOUT_SECONDS` | Timeout de las llamadas a OpenRouter (segundos) | `30`                                                                                      |
| `MAX_UPLOAD_MB`              | Tamaño máximo de PDF permitido (MB)             | `25`                                                                                      |
| `CORS_ORIGINS`               | Orígenes permitidos, separados por coma         | `http://localhost:3000,http://127.0.0.1:3000,http://localhost:8000,http://127.0.0.1:8000` |

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

> **Almacenamiento temporal:** por ahora las sesiones, los contenidos extraídos
> y los diagnósticos viven en memoria del proceso. Se pierden al reiniciar el
> servidor y no se comparten entre workers. Más adelante se reemplazarán por una
> base de datos.

## Reglas automáticas

`app/scanner/rules.py` analiza el contenido extraído y devuelve observaciones de
accesibilidad de texto y de imágenes. Todavía no tiene endpoint: se ejecuta con
`run_rules(content)` y lo consumirá el diagnóstico en la próxima etapa.

| Regla               | Qué detecta                            | Umbral inicial / severidad                            |
| ------------------- | -------------------------------------- | ----------------------------------------------------- |
| `long_paragraph`    | párrafos extensos                      | más de 150 palabras para revisar; más de 300, barrera |
| `long_sentence`     | oraciones extensas                     | más de 30 palabras para revisar; más de 50, barrera   |
| `no_headings`       | material extenso sin ningún título     | más de 150 palabras para revisar; más de 400, barrera |
| `heading_skip`      | salto de más de un nivel entre títulos | mejora sugerida                                       |
| `image_without_alt` | imágenes sin texto alternativo         | barrera; una observación por imagen                   |
| `image_only_page`   | páginas con imágenes y poco texto      | `IMAGE_ONLY_PAGE_MAX_WORDS` (15) palabras; revisar    |

Los umbrales son propuestas iniciales y están en constantes al inicio de
`rules.py`. Solo el de 300 palabras de `long_paragraph` viene del documento del
proyecto; el resto debe validarse con Accesibilidad. La documentación completa
de criterios corresponde a BE-10.

El umbral de `image_only_page` también se puede pasar como argumento:
`check_image_only_pages(content, max_words=10)`.

**Texto alternativo en PDFs:** `pdfplumber` no expone el texto alternativo de las
imágenes. El procesador deja `alt_text` en `None`, así que `image_without_alt`
marca todas las imágenes de un PDF aunque el archivo original sí tenga
descripción. Son posibles falsos positivos: el detalle de la observación lo
aclara y conviene revisar la imagen. Analizar el contenido o el contraste de las
imágenes queda para una etapa futura (por ejemplo con `pymupdf`, `pillow` u
`opencv-python-headless`).

Si el procesador de PDFs no detecta títulos (por ejemplo, en documentos con
formato plano), `no_headings` puede marcar un falso positivo. Es una limitación
de la extracción, no de la regla.

Para ver las observaciones de un material:

```bash
.venv/bin/python scripts/preview_rules.py --pdf documento.pdf
.venv/bin/python scripts/preview_rules.py --text "texto pegado"
```

## Puntaje del diagnóstico

`app/scanner/scoring.py` convierte las observaciones de `run_rules(content)` en
un puntaje de 0 a 100 y un nivel general. Todavía no tiene endpoint:
`build_diagnosis(session_id, observations)` arma el resultado que consumirá la
API de diagnóstico en la próxima etapa.

Cada observación resta según su severidad:

| Severidad | Nivel     | Penalización |
| --------- | --------- | ------------ |
| `high`    | `barrier` | 10 puntos    |
| `medium`  | `review`  | 4 puntos     |
| `low`     | `review`  | 1 punto      |

Las penalizaciones se agrupan por `rule_id` y cada regla resta como máximo 30
puntos, para que un problema repetido no opaque el resto del material. La
fórmula es `max(0, 100 - suma)`: un material sin observaciones obtiene 100.

El nivel general es `ok` cuando no hay hallazgos, `review` cuando hay algo para
revisar y `barrier` cuando al menos una observación es una barrera. El resultado
por categoría incluye siempre las seis categorías (`comprehension`, `structure`,
`visual`, `representation`, `multimedia`, `navigation`), con la cantidad de
barreras, observaciones para revisar y mejoras sugeridas.

El diagnóstico incluye el aviso `SCORE_DISCLAIMER`: el puntaje es orientativo y
no constituye una certificación formal de accesibilidad. La ponderación es una
propuesta inicial y debe validarse con el equipo de Accesibilidad (BE-10).

El script de previsualización muestra el puntaje y el resultado por categoría
junto con las observaciones.

## Análisis semántico con IA

`app/scanner/ai_analysis.py` complementa las reglas con observaciones
semánticas (consignas ambiguas, términos sin definir, secciones sobrecargadas,
referencias visuales sin explicar y secuencias de pasos poco claras). El
resultado se valida contra el catálogo `AI_RULES` y contra los bloques reales:
se descartan reglas inexistentes, bloques inexistentes y duplicados. La
severidad de estas observaciones siempre es `medium` y su `source` es `ai`.

El texto enviado se recorta a `AI_MAX_CHARS` (12.000 caracteres) y el resultado
indica `truncated=true` cuando se analizó solo una parte. Las instrucciones van
en el mensaje de sistema y el material en el mensaje de usuario; nunca se
mezclan. Si la IA falla, el resultado queda en `ai_status="unavailable"` y el
diagnóstico por reglas sigue disponible sin cambios.

### Proveedores

El proveedor se elige con `AI_PROVIDER`:

- `gemini` (default): usa `GEMINI_API_KEY` y `GEMINI_MODEL`. El comportamiento
  es el mismo que antes de agregar OpenRouter.
- `openrouter`: usa `OPENROUTER_API_KEY` y `OPENROUTER_MODEL`. OpenRouter
  expone una API compatible con OpenAI y puede servir el modelo con distintos
  proveedores; el texto se envía tanto a OpenRouter como al proveedor del
  modelo elegido.

`OPENROUTER_MODEL` no tiene valor por defecto a propósito: los catálogos
cambian y los modelos disponibles dependen de la cuenta. Elegí uno en
<https://openrouter.ai/models> filtrando por **structured outputs**. Los
modelos con sufijo `:free` tienen límites de uso variables; verificá los
vigentes antes de confiar en ellos para pruebas o producción.

Si `AI_PROVIDER=openrouter` y falta la clave o el modelo, el backend deja un
warning y el análisis con IA queda deshabilitado (`unavailable`); no se cae el
resto de la aplicación. Lo mismo pasa con un `AI_PROVIDER` desconocido.

OpenRouter se usa con salidas estructuradas estrictas (`json_schema`) y se exige
que el endpoint soporte todos los parámetros enviados
(`provider.require_parameters`). Si la API rechaza el `response_format` con un
400, se reintenta una sola vez con `json_object` y el esquema agregado a las
instrucciones. Los errores 401, 402 y 429, los timeouts, las respuestas vacías y
los JSON o esquemas inválidos se traducen a `AiUnavailableError`; los 429 no se
reintentan.

### Privacidad y datos de estudiantes

El aviso que acompaña al diagnóstico nombra al proveedor real. Con Gemini indica
que el texto se envía a Google Gemini; con OpenRouter indica que se envía a
OpenRouter y al proveedor del modelo elegido, e incluye el nombre del modelo.

**No uses material con datos personales de estudiantes.** Los proveedores
pueden registrar o usar los prompts según su política de datos, y los modelos
gratuitos suelen tener condiciones más permisivas con el contenido enviado.
Antes de analizar un material, revisá la política de datos del modelo elegido en
la ficha de <https://openrouter.ai/models>. Solo se envía el texto extraído
(no el archivo) y ni el material ni la clave se escriben en los logs.

### Probar el análisis

```bash
# Usa el proveedor configurado en AI_PROVIDER
.venv/bin/python scripts/try_ai_analysis.py --pdf documento.pdf

# Fuerza un proveedor y limita el texto enviado
.venv/bin/python scripts/try_ai_analysis.py --pdf documento.pdf \
  --provider openrouter --max-chars 300
```

El script imprime `ai_status`, `ai_notice`, `truncated` y, por cada observación,
`id`, `source`, `severity`, `block_id`, `excerpt` y `detail`. Nunca imprime la
clave.

## Diagnóstico

Estos endpoints ejecutan las reglas automáticas, complementan el resultado con
la IA cuando se solicita, guardan el diagnóstico en memoria y dejan la sesión
en estado `analyzed`.

| Método | Ruta                                      | Descripción                                                   |
| ------ | ----------------------------------------- | ------------------------------------------------------------- |
| `POST` | `/api/v1/sessions/{session_id}/analyze`   | Analiza la sesión. Query `use_ai` (booleano, default `true`). |
| `GET`  | `/api/v1/sessions/{session_id}/diagnosis` | Devuelve el diagnóstico guardado.                             |

`analyze` extrae el contenido si todavía no se extrajo (reutiliza la lógica de
`POST /extract`). Los errores de extracción se devuelven tal cual, por ejemplo
`422 no_extractable_text`, y el estado de la sesión no cambia.

### `use_ai`, reintentos y caché

- `use_ai=false`: solo reglas, `ai_status="skipped"` y `ai_notice=null`. No se
  consulta a la IA. Si ya hay un diagnóstico `ok` guardado, devuelve el
  resultado de reglas pero **no lo reemplaza**: el `GET` sigue devolviendo el
  diagnóstico completo con las observaciones de IA.
- `use_ai=true` (default) con un diagnóstico `ok` guardado: devuelve el
  guardado sin volver a consultar a la IA.
- `use_ai=true` con `unavailable`, `skipped` o sin diagnóstico: consulta a la
  IA y reemplaza lo guardado. Un resultado `unavailable` se reintenta en la
  próxima llamada; un `ok` ya no se vuelve a consultar.
- Si la IA falla, la respuesta sigue siendo `200` con
  `ai_status="unavailable"` y el diagnóstico por reglas completo. La IA nunca
  produce un `5xx`.

Las observaciones de reglas y de IA se unen, se ordenan por posición en el
documento y se deduplican por `id`. Las de IA tienen `source="ai"` y
`severity="medium"`; cuentan en el puntaje igual que las observaciones de
reglas.

Hay un lock por sesión: dos `analyze` simultáneos sobre la misma sesión esperan
y reutilizan el mismo resultado, así que la IA se consulta una sola vez. Se
registra un log INFO, sin el texto del material, cada vez que se consulta a la
IA.

### Estados

`uploaded` o `extracted` pasan a `analyzed` al completar el análisis, también
cuando la IA queda `unavailable`. Una sesión en `completed` nunca retrocede.

### Errores del diagnóstico

| HTTP  | `code`                 | Cuándo                                                      |
| ----- | ---------------------- | ----------------------------------------------------------- |
| `404` | `session_not_found`    | La sesión indicada no existe.                               |
| `409` | `session_not_analyzed` | Se pidió el diagnóstico antes de llamar a `POST /analyze`.  |
| `422` | `no_extractable_text`  | El material no tiene texto (por ejemplo, un PDF escaneado). |
| `422` | `invalid_pdf`          | El PDF está dañado o protegido.                             |

Ejemplos:

```bash
# Solo reglas (sin IA)
curl.exe -X POST "http://127.0.0.1:8000/api/v1/sessions/<session_id>/analyze?use_ai=false"

# Con IA (default)
curl.exe -X POST "http://127.0.0.1:8000/api/v1/sessions/<session_id>/analyze"

# Consultar el diagnóstico guardado
curl.exe "http://127.0.0.1:8000/api/v1/sessions/<session_id>/diagnosis"
```

Respuesta real de un texto de 180 palabras analizado con `use_ai=false`:

```json
{
  "session_id": "8a7277be-937e-429d-9dea-8856ac8b86d9",
  "score": 96,
  "level": "review",
  "disclaimer": "El puntaje es un indicador orientativo. No constituye una certificación formal de accesibilidad.",
  "categories": [
    {
      "category": "comprehension",
      "severity": "review",
      "barrier_count": 0,
      "review_count": 1,
      "suggestion_count": 0
    },
    {
      "category": "structure",
      "severity": "ok",
      "barrier_count": 0,
      "review_count": 0,
      "suggestion_count": 0
    },
    {
      "category": "visual",
      "severity": "ok",
      "barrier_count": 0,
      "review_count": 0,
      "suggestion_count": 0
    },
    {
      "category": "representation",
      "severity": "ok",
      "barrier_count": 0,
      "review_count": 0,
      "suggestion_count": 0
    },
    {
      "category": "multimedia",
      "severity": "ok",
      "barrier_count": 0,
      "review_count": 0,
      "suggestion_count": 0
    },
    {
      "category": "navigation",
      "severity": "ok",
      "barrier_count": 0,
      "review_count": 0,
      "suggestion_count": 0
    }
  ],
  "observations": [
    {
      "id": "long_paragraph:b2",
      "rule_id": "long_paragraph",
      "category": "comprehension",
      "severity": "medium",
      "source": "rule",
      "title": "Párrafo muy extenso",
      "detail": "Tiene 180 palabras.",
      "why_it_matters": "Los bloques de texto largos cansan y dificultan seguir la idea, sobre todo a quienes tienen dificultades de lectura o atención.",
      "recommendation": "Dividir el párrafo en bloques más cortos, con una idea en cada uno.",
      "block_id": "b2",
      "page": null,
      "excerpt": "Uno dos tres. Uno dos tres. Uno dos tres. Uno dos tres. Uno dos tres. Uno dos tres. Uno dos tres. Uno dos tres. Uno dos tres. Uno dos tres. Uno dos tres. Uno…"
    }
  ],
  "created_at": "2026-11-12T02:37:46.685329Z",
  "ai_status": "skipped",
  "ai_notice": null,
  "ai_truncated": false
}
```

Con la IA completa, `ai_status` es `"ok"`, `ai_notice` trae el aviso de
privacidad y `ai_truncated` indica si se analizó solo una parte del material.
Cuando la IA falla, `ai_status` es `"unavailable"` y `ai_notice` explica que el
diagnóstico por reglas sigue disponible.

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
│   │           ├── diagnosis.py   # Endpoints del diagnóstico
│   │           └── sessions.py    # Endpoints de sesiones
│   ├── core/
│   │   ├── config.py              # Configuración y variables de entorno
│   │   └── exceptions.py          # Errores globales con formato {code, message}
│   ├── processors/
│   │   ├── pdf_processor.py       # Extracción de bloques desde PDFs
│   │   └── text_processor.py      # Extracción de bloques desde texto plano
│   ├── scanner/
│   │   ├── ai_analysis.py         # Análisis semántico con IA y catálogo AI_RULES
│   │   ├── rules.py               # Reglas automáticas de contenido
│   │   └── scoring.py             # Puntaje, nivel y resultado por categoría
│   ├── schemas/
│   │   ├── ai.py                  # AiStatus, AiAnalysisResult y aviso de privacidad
│   │   ├── common.py              # ErrorResponse
│   │   ├── content.py             # ContentBlock, ContentSummary, ExtractedContent
│   │   ├── diagnosis.py           # Diagnosis, CategoryResult y DiagnosisLevel
│   │   ├── observation.py         # Observation, Category y Severity
│   │   └── session.py             # SourceType, SessionStatus, TextInput, SessionResponse
│   ├── services/
│   │   ├── ai_provider.py         # Selector de Gemini u OpenRouter
│   │   ├── analysis_service.py    # Diagnóstico, caché de IA y estados
│   │   ├── content_service.py     # Extracción y resumen de contenido
│   │   ├── gemini.py              # Cliente de Gemini (StructuredAI)
│   │   ├── openrouter.py          # Cliente de OpenRouter (StructuredAI)
│   │   └── session_service.py     # Lógica de sesiones (almacenamiento en memoria)
│   └── main.py                    # Punto de entrada de FastAPI, CORS y routers
├── scripts/
│   ├── inspect_pdf.py             # Bloques detectados en un PDF
│   ├── preview_rules.py           # Observaciones y puntaje por reglas
│   └── try_ai_analysis.py         # Reglas + análisis con IA sobre un PDF
├── tests/
│   ├── conftest.py
│   ├── test_ai_analysis.py
│   ├── test_ai_provider.py
│   ├── test_content.py
│   ├── test_diagnosis.py
│   ├── test_gemini.py
│   ├── test_openrouter.py
│   ├── test_pdf_processor.py
│   ├── test_rules.py
│   ├── test_scoring.py
│   ├── test_sessions.py
│   └── test_text_processor.py
├── .env.example
├── requirements.txt
├── requirements-dev.txt
└── pytest.ini
```
