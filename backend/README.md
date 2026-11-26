# Ayudante PDF — Backend

Backend de la aplicación **Ayudante PDF**, construido con **FastAPI**. Expone la API que
procesa documentos PDF y se integra con **Google Gemini** u **OpenRouter** para el
análisis semántico con IA.

El contrato de la API para el frontend (rutas, modelos, ejemplos de respuesta y
guía para mocks) está en [`docs/api-contract.md`](../docs/api-contract.md). La
fuente de verdad es `/openapi.json`.

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
| `DATABASE_URL`               | URL de conexión de la app (driver psycopg 3)    | _(sin valor por defecto)_                                                                 |
| `DATABASE_URL_UNPOOLED`      | URL directa de Neon para Alembic (producción)   | _(vacío; Alembic usa `DATABASE_URL`)_                                                     |
| `TEST_DATABASE_URL`          | URL de la base de tests (`_test` al final)      | _(sin valor por defecto)_                                                                 |
| `POSTGRES_USER`              | Usuario de PostgreSQL en Docker                 | _(obligatorio en `.env`)_                                                                 |
| `POSTGRES_PASSWORD`          | Clave de PostgreSQL en Docker                   | _(obligatorio en `.env`)_                                                                 |
| `POSTGRES_DB`                | Nombre de la base de desarrollo                 | _(obligatorio en `.env`)_                                                                 |
| `POSTGRES_PORT`              | Puerto local publicado por Docker               | `5433` en `.env.example` (fallback Compose: `5432`)                                       |

## Base de datos (PostgreSQL)

El desarrollo local usa PostgreSQL 18 en Docker. Producción usa una base de
Neon desde Render; el `.env` local **nunca** apunta a Neon. El esquema se
versiona con Alembic y se aplica con `alembic upgrade head`.

```bash
cp .env.example .env   # cambiá POSTGRES_PASSWORD antes de usar el proyecto
docker compose up -d --wait
alembic upgrade head
pytest
```

`docker compose down` conserva los datos porque usa un volumen nombrado;
`docker compose down -v` lo borra. La base de tests es `<POSTGRES_DB>_test` y
se crea con `docker/initdb/01-create-test-db.sh` la primera vez que se
inicializa el volumen. Si el volumen ya existía, creala a mano:

```bash
docker compose exec db sh -c 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" \
  -c "CREATE DATABASE \"${POSTGRES_DB}_test\" OWNER \"$POSTGRES_USER\";"'
```

`DATABASE_URL`, `DATABASE_URL_UNPOOLED` y `TEST_DATABASE_URL` deben usar
`postgresql+psycopg://` (psycopg 3). Mantené las credenciales de las URLs
sincronizadas con `POSTGRES_USER`, `POSTGRES_PASSWORD` y `POSTGRES_PORT`. El
ejemplo usa el puerto `5433` para no chocar con un PostgreSQL local en `5432`;
si cambiás `POSTGRES_PORT`, actualizá también el puerto de ambas URLs.

En local, `DATABASE_URL` apunta a Docker y `DATABASE_URL_UNPOOLED` queda vacía:
Alembic usa `DATABASE_URL`. En Render, `DATABASE_URL` es la URL _pooled_ de
Neon (host con `-pooler`) y `DATABASE_URL_UNPOOLED` es la _directa_ (sin
`-pooler`), que Alembic usa para migrar. Ver
[Deploy en Render + Neon](#deploy-en-render--neon).

Las migraciones viven en `alembic/`. Para crear una nueva revisión:

```bash
alembic revision -m "descripcion"
alembic upgrade head
```

### Modelos y tablas

`alembic upgrade head` crea las tablas de documentos y análisis:

| Tabla                | Qué guarda                                                                             |
| -------------------- | -------------------------------------------------------------------------------------- |
| `folders`            | Carpetas por dueño, con `parent_id` opcional para anidarlas.                           |
| `documents`          | Material cargado: dueño, carpeta opcional, `source_type`, nombre, tamaño y estado.     |
| `document_files`     | Contenido original 1:1: `content` (BYTEA) para PDF o `content_text` para texto pegado. |
| `extracted_contents` | Contenido estructurado 1:1 en un `payload` JSONB.                                      |
| `diagnoses`          | Diagnóstico 1:1 en un `payload` JSONB, con `score`, `level` y `ai_status`.             |

Todas las tablas llevan `owner_id` desde el inicio. Los estados y tipos
(`source_type`, `status`, `level`, `ai_status`) se guardan como texto con
restricciones `CHECK`; no se crean tipos `ENUM` nativos de PostgreSQL.

El nombre de una carpeta no se repite dentro del mismo nivel y dueño. La
comparación es case-insensitive e incluye las raíces (`parent_id NULL`), que
usan un índice único parcial distinto del de las carpetas anidadas.

Esta issue agrega el esquema, pero la API todavía sigue usando el
almacenamiento en memoria: la integración de sesiones y documentos con la base
queda para una issue posterior.

### Usuario demo

El seed es manual e idempotente: si el email ya existe, no duplica el usuario.

```bash
.venv/bin/python scripts/seed_user.py \
  --email demo@ejemplo.com \
  --password "clave-demo" \
  --first-name Demo \
  --last-name Usuario
```

También acepta `SEED_USER_EMAIL`, `SEED_USER_PASSWORD`,
`SEED_USER_FIRST_NAME`, `SEED_USER_LAST_NAME` y `SEED_USER_PHONE` como
variables de entorno. No guardes credenciales reales en el repositorio.

## Deploy en Render + Neon

Producción usa el backend en Render y PostgreSQL de Neon. El desarrollo local
sigue usando el Postgres de Docker; `backend/.env` nunca apunta a Neon.

### Variables de entorno en Render

| Variable                | Valor                                                                     |
| ----------------------- | ------------------------------------------------------------------------- |
| `DATABASE_URL`          | URL **pooled** de Neon (host con `-pooler`), con `postgresql+psycopg://`. |
| `DATABASE_URL_UNPOOLED` | URL **directa** de Neon (sin `-pooler`), para Alembic.                    |
| `JWT_SECRET`            | Secreto propio de producción.                                             |
| `AI_PROVIDER` y claves  | Según el proveedor elegido.                                               |
| `CORS_ORIGINS`          | Dominio del frontend productivo.                                          |
| `MAX_UPLOAD_MB`         | Tamaño máximo de PDF.                                                     |

No subir estas credenciales al repo. Si una URL se filtra, rotar la password
en Neon y actualizar la variable en Render.

### Configuración del servicio

- **Branch:** `develop` (con Auto-Deploy en Off). Si el servicio está vinculado
  a otra rama, usar esa.
- **Auto-Deploy:** Off. Los merges a `develop` no tocan producción.
- **Root Directory:** `backend`
- **Build Command:** `pip install -r requirements.txt`
- **Start Command:** `alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- **Health Check Path:** `/health`

El Start Command aplica las migraciones antes de levantar la app. Es
idempotente y también corre cuando Render despierta el servicio.

### Deploy manual

1. Mergear a `develop` el bloque ya probado.
2. En Render: **Manual Deploy → Deploy latest commit**.
3. Esperar el build y el arranque (incluye `alembic upgrade head`).
4. Verificar `https://<servicio>.onrender.com/health`.
5. Probar registro/login y el flujo que corresponda.
6. Si algo falla, **Manual Deploy** del commit anterior.

### Migraciones manuales

Desde `backend/`, con una URL temporal (no guardarla en `.env`):

```bash
read -rsp "Neon URL directa: " NEON_URL; echo
DATABASE_URL_UNPOOLED="$NEON_URL" .venv/bin/alembic upgrade head
DATABASE_URL_UNPOOLED="$NEON_URL" .venv/bin/alembic current
unset NEON_URL
```

Si la base ya tenía tablas creadas fuera de Alembic, no fuerces el `upgrade`:
revisá `alembic current` y consultá antes de hacer `stamp`.

### Servicio dormido

Render free duerme el servicio tras unos 15 minutos sin tráfico. La primera
request puede tardar 30–60 segundos. Abrí `/health` para despertarlo y esperá
la respuesta antes de usar la app. Neon también suspende el compute: la
primera consulta puede tardar unos segundos.

> **Persistencia pendiente:** BE-17 creó las tablas para documentos, contenido
> extraído y diagnósticos, pero la API todavía no las usa: las sesiones siguen
> en memoria. La integración con la base queda para una issue aparte.

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

En PDFs, `GET /content` devuelve `pages` (tamaño de cada página) y un `bbox`
por bloque, ambos en puntos PDF (72 por pulgada) con origen arriba-izquierda.
En texto pegado, `pages=[]` y `bbox=null`. El backend no renderiza el PDF: el
frontend convierte a coordenadas de pdf.js con
`top_js = page.height - bbox.bottom`.

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

> **Almacenamiento temporal:** las sesiones, los contenidos extraídos y los
> diagnósticos siguen viviendo en memoria del proceso. Se pierden al reiniciar
> el servidor y no se comparten entre workers. BE-25 conecta Neon y persiste
> `users`, pero la persistencia de estas entidades queda para una issue aparte.

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
proyecto; el resto son decisiones del equipo a calibrar con Accesibilidad. Cada
regla tiene un campo `reference` con su fuente y el detalle completo está en
[`docs/accessibility-criteria.md`](../docs/accessibility-criteria.md).

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
propuesta inicial a calibrar con el set de evaluación; el detalle y las
decisiones abiertas están en
[`docs/accessibility-criteria.md`](../docs/accessibility-criteria.md).

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

## Adaptación de barreras

`POST /api/v1/adaptations` recibe una barrera y devuelve una versión adaptada
del texto. Es **stateless**: no usa sesiones ni guarda el resultado. Usa el
proveedor configurado en `AI_PROVIDER`.

| Método | Ruta                  | Descripción                                    |
| ------ | --------------------- | ---------------------------------------------- |
| `POST` | `/api/v1/adaptations` | Genera `adapted_text` a partir de una barrera. |

```bash
curl -s -X POST http://127.0.0.1:8000/api/v1/adaptations \
  -H "Content-Type: application/json" \
  -d '{
    "type": "simplify",
    "rule_id": "long_paragraph",
    "original_text": "Texto de prueba con varias oraciones. Esta es la segunda. Esta es la tercera. Esta es la cuarta.",
    "title": "Párrafo muy extenso",
    "recommendation": "Dividir el párrafo en bloques más cortos."
  }' | jq
```

- `type`: `simplify`, `clarify`, `describe`, `alt_text` o `sequence`.
- `original_text`: obligatorio, máximo 8.000 caracteres.
- `rule_id` es opcional y solo enriquece el prompt. `no_headings` y
  `heading_skip` se rechazan con `422 observation_not_adaptable`.
- Si la IA falla, la respuesta sigue siendo `200`: `simplify` con 4+ oraciones
  y más de 120 palabras se divide en párrafos (`source="local"`); el resto
  devuelve `adapted_text=null` y la recomendación en `notes`.
- `alt_text` no analiza la imagen: describe con el texto cercano y lo aclara en
  `notes`. Si supera 250 caracteres, se reintenta y después se recorta.

## Exportación del PDF adaptado

`POST /api/v1/sessions/{session_id}/export` recibe los textos finales por bloque
y devuelve el PDF original con una capa visual de reemplazo. Es **stateless**:
no guarda los textos ni cambia el estado de la sesión.

| Método | Ruta                                   | Descripción                                       |
| ------ | -------------------------------------- | ------------------------------------------------- |
| `POST` | `/api/v1/sessions/{session_id}/export` | Devuelve `application/pdf` con los textos nuevos. |

```bash
curl -s -X POST http://127.0.0.1:8000/api/v1/sessions/<session_id>/export \
  -H "Content-Type: application/json" \
  -d '{"edits":[{"block_id":"b1","text":"Texto final del bloque."}]}' \
  -D headers.txt -o documento_adaptado.pdf
```

- Solo funciona con sesiones PDF que ya tengan el contenido extraído.
- Cada `block_id` debe existir, tener `page` y `bbox`, y no repetirse.
- El texto se dibuja con `Helvetica` (o `Helvetica-Bold` en títulos) y usa
  `ContentBlock.font_size` como tamaño inicial. Si no entra, se reduce hasta
  6 pt y después se recorta con `…`.
- En imágenes, el texto va como leyenda en la franja inferior del bloque.
- La respuesta incluye `Content-Disposition` con fallback
  `filename="documento-adaptado.pdf"` y `filename*` UTF-8.
- Errores: `404 session_not_found`, `409 content_not_extracted`,
  `409 export_unavailable`, `422 unknown_block`, `422 block_without_bbox`,
  `422 duplicate_block_id`, `422 empty_text`, `422 text_too_long` y
  `422 invalid_pdf`.

> **Limitación:** el texto original sigue en la capa de texto del PDF. El
> reemplazo es visual, así que copiar/pegar o un lector de pantalla pueden ver
> ambos textos. La redacción real queda para una issue aparte.

## Tests

```bash
pytest
```

Los tests de base de datos usan `TEST_DATABASE_URL` y fallan de forma explícita
si apunta a la misma base que `DATABASE_URL` o si el nombre de la base no
termina en `_test`.

La suite aplica `alembic upgrade head` sobre `TEST_DATABASE_URL` una vez por
sesión, así que no hace falta migrar la base de tests a mano. Cada test corre
dentro de una transacción que se revierte al terminar: los `commit()` del test
no dejan datos entre pruebas.

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
│   │           ├── adaptations.py # Endpoint de adaptación de barreras
│   │           ├── auth.py        # Registro, login y datos del usuario
│   │           ├── content.py     # Endpoints de contenido
│   │           ├── diagnosis.py   # Endpoints del diagnóstico
│   │           ├── export.py      # Exportación del PDF adaptado
│   │           └── sessions.py    # Endpoints de sesiones
│   ├── core/
│   │   ├── config.py              # Configuración y variables de entorno
│   │   ├── database.py            # Engine, sesión y Base de SQLAlchemy
│   │   └── exceptions.py          # Errores globales con formato {code, message}
│   ├── models/
│   │   ├── diagnosis.py           # DiagnosisRecord (payload JSONB, score, level, ai_status)
│   │   ├── document.py            # Document (dueño, carpeta, PDF/texto, estado)
│   │   ├── document_file.py       # DocumentFile (BYTEA o texto pegado)
│   │   ├── extracted_content.py   # ExtractedContentRecord (payload JSONB)
│   │   ├── folder.py              # Folder (carpetas anidadas y unicidad por nivel)
│   │   └── user.py                # User
│   ├── processors/
│   │   ├── pdf_processor.py       # Extracción de bloques desde PDFs
│   │   └── text_processor.py      # Extracción de bloques desde texto plano
│   ├── scanner/
│   │   ├── adaptation.py          # Motor de adaptación con IA y fallback local
│   │   ├── ai_analysis.py         # Análisis semántico con IA y catálogo AI_RULES
│   │   ├── rules.py               # Reglas automáticas de contenido
│   │   └── scoring.py             # Puntaje, nivel y resultado por categoría
│   ├── schemas/
│   │   ├── adaptation.py          # AdaptationType, AdaptationRequest y Adaptation
│   │   ├── ai.py                  # AiStatus, AiAnalysisResult y aviso de privacidad
│   │   ├── common.py              # ErrorResponse
│   │   ├── content.py             # ContentBlock, ContentSummary, ExtractedContent
│   │   ├── diagnosis.py           # Diagnosis, CategoryResult y DiagnosisLevel
│   │   ├── export.py              # ExportRequest y ExportEdit
│   │   ├── observation.py         # Observation, Category y Severity
│   │   └── session.py             # SourceType, SessionStatus, TextInput, SessionResponse
│   ├── services/
│   │   ├── ai_provider.py         # Selector de Gemini u OpenRouter
│   │   ├── analysis_service.py    # Diagnóstico, caché de IA y estados
│   │   ├── content_service.py     # Extracción y resumen de contenido
│   │   ├── export_service.py      # Capa de reemplazo y fusión del PDF
│   │   ├── gemini.py              # Cliente de Gemini (StructuredAI)
│   │   ├── openrouter.py          # Cliente de OpenRouter (StructuredAI)
│   │   └── session_service.py     # Lógica de sesiones (almacenamiento en memoria)
│   └── main.py                    # Punto de entrada de FastAPI, CORS y routers
├── scripts/
│   ├── inspect_pdf.py             # Bloques detectados en un PDF
│   ├── preview_rules.py           # Observaciones y puntaje por reglas
│   ├── seed_user.py               # Seed manual e idempotente del usuario demo
│   └── try_ai_analysis.py         # Reglas + análisis con IA sobre un PDF
├── tests/
│   ├── conftest.py                # Fixtures de DB, migraciones y cliente
│   ├── test_adaptation.py
│   ├── test_adaptations_api.py
│   ├── test_ai_analysis.py
│   ├── test_ai_provider.py
│   ├── test_content.py
│   ├── test_database.py
│   ├── test_diagnosis.py
│   ├── test_documents.py          # Documentos PDF/texto, JSONB y cascadas
│   ├── test_export.py
│   ├── test_export_api.py
│   ├── test_folders.py            # Unicidad de carpetas por nivel y dueño
│   ├── test_gemini.py
│   ├── test_migrations.py         # Tablas, enums como texto y versión
│   ├── test_openrouter.py
│   ├── test_pdf_processor.py
│   ├── test_rules.py
│   ├── test_scoring.py
│   ├── test_seed_user.py          # Seed demo idempotente
│   ├── test_sessions.py
│   └── test_text_processor.py
├── alembic/
│   ├── env.py                     # Toma DATABASE_URL y Base.metadata
│   └── versions/
│       ├── *_baseline.py          # Revisión baseline vacía
│       ├── *_create_users_table.py
│       └── *_create_folders_documents_contents_and_diagnoses.py
├── docker/
│   └── initdb/
│       └── 01-create-test-db.sh   # Crea la base _test al inicializar el volumen
├── alembic.ini
├── docker-compose.yml
├── .env.example
├── .gitattributes
├── requirements.txt
├── requirements-dev.txt
└── pytest.ini
```
