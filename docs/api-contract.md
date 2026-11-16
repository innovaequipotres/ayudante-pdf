# Contrato de la API

Documento de referencia para el frontend. Describe las rutas, los modelos y los
ejemplos de respuesta del backend de **Ayudante PDF** para que se puedan armar
los mocks sin adivinar nombres ni formatos.

- **Fuente de verdad:** `GET /openapi.json` (OpenAPI 3.1.0, generado por
  FastAPI a partir de los schemas de Pydantic).
- **Documentación interactiva:** `GET /docs`.
- **Todos los nombres de campos, rutas y valores de enum están en inglés.**
- **Alcance:** issues BE-02 a BE-15 (sesiones, contenido, reglas, puntaje,
  diagnóstico, análisis con IA, adaptación y exportación).

> Cualquier cambio de nombre, tipo, valor de enum o ruta se avisa al frontend y
> se refleja primero en este documento y en `/openapi.json`.

## Contenido

1. [Alcance y estado actual](#1-alcance-y-estado-actual)
2. [Flujo de la API](#2-flujo-de-la-api)
3. [Convenciones](#3-convenciones)
4. [Glosario español → inglés](#4-glosario-español--inglés)
5. [Endpoints](#5-endpoints)
6. [Modelos](#6-modelos)
7. [Ejemplos de respuesta](#7-ejemplos-de-respuesta)
8. [Catálogo de errores](#8-catálogo-de-errores)
9. [Guía para armar mocks](#9-guía-para-armar-mocks)
10. [Tipos desde OpenAPI](#10-tipos-desde-openapi)
11. [Cambios de contrato](#11-cambios-de-contrato)

## 1. Alcance y estado actual

| Dato              | Valor                                                           |
| ----------------- | --------------------------------------------------------------- |
| Base URL local    | `http://127.0.0.1:8000`                                         |
| Prefijo de la API | `/api/v1`                                                       |
| Autenticación     | Ninguna todavía                                                 |
| Formato           | JSON UTF-8 (`application/json`); la exportación devuelve PDF    |
| OpenAPI           | `http://127.0.0.1:8000/openapi.json`                            |
| Documentación     | `http://127.0.0.1:8000/docs`                                    |
| Persistencia      | **En memoria**: se pierde al reiniciar el servidor              |
| Proveedor de IA   | Gemini por defecto; OpenRouter opcional (no afecta el contrato) |

`/openapi.json` ya incluye las 9 rutas de negocio, los modelos y los errores
declarados. **No incluye ejemplos de respuesta**: los ejemplos de este
documento se capturaron ejecutando la API real.

### Lo que todavía no forma parte del contrato

- Autenticación, usuarios y permisos.
- Persistencia en base de datos e historial entre reinicios, también para las
  adaptaciones y la exportación: `POST /api/v1/adaptations` y
  `POST /api/v1/sessions/{session_id}/export` son stateless.

## 2. Flujo de la API

```text
POST /api/v1/sessions/text   (texto pegado)
POST /api/v1/sessions/file   (PDF)
              │
              │  201 · status = "uploaded"
              ▼
POST /api/v1/sessions/{session_id}/extract
              │
              │  200 · bloques extraídos · status = "extracted"
              ▼
POST /api/v1/sessions/{session_id}/analyze?use_ai=true
              │
              │  200 · diagnóstico · status = "analyzed"
              ▼
GET  /api/v1/sessions/{session_id}/diagnosis
              │
              │  200 · diagnóstico guardado
              ▼
        Frontend / mocks

POST /api/v1/adaptations   (stateless: no usa sesión)
              │
              │  200 · Adaptation
              ▼
POST /api/v1/sessions/{session_id}/export   (stateless)
              │
              │  200 · application/pdf · la sesión no cambia de estado
              ▼
        Frontend / mocks
```

La adaptación es independiente del flujo de sesiones: recibe una barrera y
devuelve el texto reescrito, sin persistir nada. La exportación tampoco
persiste: recibe los textos finales por bloque y devuelve el PDF original con
una capa visual de reemplazo.

| Estado      | Cuándo se alcanza                                     |
| ----------- | ----------------------------------------------------- |
| `uploaded`  | Al crear la sesión.                                   |
| `extracted` | Después de `POST /extract`.                           |
| `analyzed`  | Después de `POST /analyze` (aunque la IA falle).      |
| `completed` | Reservado para una etapa posterior; hoy no se asigna. |

## 3. Convenciones

- **`snake_case`** en todos los campos.
- **Identificadores:** `session_id` es un UUID v4. Los bloques usan `b1`,
  `b2`, etc. Las observaciones usan:
  - `{rule_id}:{block_id}` → `long_paragraph:b5`
  - `{rule_id}:pagina-{page}` → `image_only_page:pagina-2`
  - `ai:{rule_id}:{block_id}` → `ai:undefined_term:b1`
- **Fechas:** ISO 8601 en UTC, con `Z` al final
  (`2026-11-12T17:14:07.570226Z`).
- **Nulos:** los campos opcionales se devuelven con `null`, no se omiten.
  La lista completa está en [Modelos](#6-modelos).
- **Enums:** se documentan abajo. El frontend debe tolerar valores nuevos sin
  romper la UI, pero los tipos generados solo conocen los actuales.
- **Orden:**
  - `Diagnosis.categories`: siempre las 6 categorías, en el orden del enum.
  - `Diagnosis.observations`: ordenadas por página y por posición del bloque en
    el documento.
  - `ExtractedContent.blocks`: orden de lectura.
- **Geometría:** `ExtractedContent.pages` y `ContentBlock.bbox` están en puntos
  PDF (72 por pulgada), con origen arriba-izquierda. El frontend debe invertir
  el eje Y para pdf.js (`top_js = page.height - bbox.bottom`).
- **Arrays vacíos:** `observations` puede ser `[]`; no es un error.
- **Sin paginación:** todas las respuestas devuelven el recurso completo.

## 4. Glosario español → inglés

| Concepto acordado  | Nombre en la API                | Notas                                                           |
| ------------------ | ------------------------------- | --------------------------------------------------------------- |
| Barrera            | `Observation`                   | Un problema detectado en un punto del material.                 |
| Análisis           | `Diagnosis`                     | Resultado completo: puntaje, nivel, categorías y observaciones. |
| Dimensión          | `category`                      | Una de las 6 categorías del enum `Category`.                    |
| Nivel              | `severity` / `level`            | Ver [las dos escalas](#las-dos-escalas-de-nivel).               |
| Origen             | `source`                        | `rule` (regla automática) o `ai` (análisis semántico).          |
| Ubicación          | `block_id` + `page` + `excerpt` | `block_id` y `page` pueden ser `null`; `excerpt` también.       |
| Descripción        | `title` + `detail`              | `title` es obligatorio; `detail` puede ser `null`.              |
| Por qué importa    | `why_it_matters`                | Texto explicativo obligatorio.                                  |
| Recomendación      | `recommendation`                | Texto explicativo obligatorio.                                  |
| Tipo de adaptación | `AdaptationType`                | `simplify`, `clarify`, `describe`, `alt_text`, `sequence`.      |
| Adaptación         | `Adaptation`                    | Texto adaptado de una barrera; no se persiste.                  |

### Las dos escalas de nivel

El glosario usa “nivel” para dos cosas distintas. No son intercambiables:

| Escala                      | Campo                     | Valores                   | Dónde se usa                        |
| --------------------------- | ------------------------- | ------------------------- | ----------------------------------- |
| Gravedad de una observación | `Observation.severity`    | `high`, `medium`, `low`   | Cada barrera detectada.             |
| Nivel del diagnóstico       | `Diagnosis.level`         | `ok`, `review`, `barrier` | Resultado general del material.     |
| Nivel por categoría         | `CategoryResult.severity` | `ok`, `review`, `barrier` | Peor nivel dentro de una categoría. |

Equivalencias:

| `Observation.severity` | Lectura en la UI | Aporte al nivel | Penalización |
| ---------------------- | ---------------- | --------------- | ------------ |
| `high`                 | Alta / barrera   | `barrier`       | 10 puntos    |
| `medium`               | Media / revisar  | `review`        | 4 puntos     |
| `low`                  | Baja / mejora    | `review`        | 1 punto      |

> En `CategoryResult`, un `suggestion_count` mayor que cero no cambia el nivel:
> las mejoras (`low`) cuentan como `review`, nunca como `barrier`.

## 5. Endpoints

| Método | Ruta                                      | Éxito | Descripción                                              |
| ------ | ----------------------------------------- | ----- | -------------------------------------------------------- |
| `POST` | `/api/v1/sessions/file`                   | `201` | Crea una sesión desde un PDF (`multipart/form-data`).    |
| `POST` | `/api/v1/sessions/text`                   | `201` | Crea una sesión desde texto pegado (`application/json`). |
| `GET`  | `/api/v1/sessions/{session_id}`           | `200` | Devuelve una sesión.                                     |
| `POST` | `/api/v1/sessions/{session_id}/extract`   | `200` | Extrae el contenido y deja la sesión en `extracted`.     |
| `GET`  | `/api/v1/sessions/{session_id}/content`   | `200` | Devuelve el contenido ya extraído.                       |
| `POST` | `/api/v1/sessions/{session_id}/analyze`   | `200` | Ejecuta reglas y, opcionalmente, IA.                     |
| `GET`  | `/api/v1/sessions/{session_id}/diagnosis` | `200` | Devuelve el diagnóstico guardado.                        |
| `POST` | `/api/v1/sessions/{session_id}/export`    | `200` | Aplica textos finales y devuelve el PDF adaptado.        |

### 5.1 `POST /api/v1/sessions/file`

- **Request:** `multipart/form-data` con el campo `file`.
- **Validaciones:** extensión `.pdf`, archivo no vacío, firma `%PDF` y tamaño
  máximo de 25 MB (`MAX_UPLOAD_MB`).
- **Response `201`:** [`SessionResponse`](#sessionresponse).
- **Errores:** `400 empty_content`, `400 invalid_pdf`, `413 file_too_large`,
  `415 unsupported_format`.

### 5.2 `POST /api/v1/sessions/text`

- **Request:** [`TextInput`](#textinput).
- **Response `201`:** [`SessionResponse`](#sessionresponse). El `filename` es
  el `title` del texto (o `null`), y `size_bytes` es el tamaño UTF-8.
- **Errores:** `400 empty_content`, `422 VALIDATION_ERROR`.

### 5.3 `GET /api/v1/sessions/{session_id}`

- **Response `200`:** [`SessionResponse`](#sessionresponse).
- **Errores:** `404 session_not_found`, `422 VALIDATION_ERROR` si el UUID no es
  válido.

### 5.4 `POST /api/v1/sessions/{session_id}/extract`

- **Response `200`:** [`ExtractedContent`](#extractedcontent).
- **Idempotencia:** si el contenido ya fue extraído, devuelve el guardado sin
  volver a procesar el material.
- **Errores:** `404 session_not_found`, `422 no_extractable_text`,
  `422 invalid_pdf`.

### 5.5 `GET /api/v1/sessions/{session_id}/content`

- **Response `200`:** [`ExtractedContent`](#extractedcontent).
- **Errores:** `404 session_not_found`, `409 content_not_extracted` si todavía
  no se llamó a `POST /extract`.

### 5.6 `POST /api/v1/sessions/{session_id}/analyze`

| Query    | Tipo   | Default | Descripción                                                     |
| -------- | ------ | ------- | --------------------------------------------------------------- |
| `use_ai` | `bool` | `true`  | Si es `true`, complementa las reglas con el análisis semántico. |

- **Response `200`:** [`Diagnosis`](#diagnosis). Un fallo de la IA **no**
  produce `5xx`: devuelve `ai_status="unavailable"` y el diagnóstico por reglas.
- **Extracción implícita:** si el contenido no fue extraído, lo extrae antes de
  analizar. Los errores de extracción se devuelven tal cual.
- **Caché de IA:**
  - `use_ai=true` y diagnóstico guardado con `ai_status="ok"`: reutiliza el
    guardado sin volver a consultar a la IA.
  - `use_ai=true` con `unavailable`, `skipped` o sin diagnóstico: consulta a la
    IA y reemplaza lo guardado.
  - `use_ai=false`: solo reglas y `ai_status="skipped"`; **no reemplaza** un
    diagnóstico completo ya guardado.
- **Errores:** `404 session_not_found`, `422 no_extractable_text`,
  `422 invalid_pdf`.

### 5.7 `GET /api/v1/sessions/{session_id}/diagnosis`

- **Response `200`:** [`Diagnosis`](#diagnosis).
- **Errores:** `404 session_not_found`, `409 session_not_analyzed` si todavía
  no se llamó a `POST /analyze`.

### 5.8 Endpoints de infraestructura

| Método | Ruta      | Response                                                                        |
| ------ | --------- | ------------------------------------------------------------------------------- |
| `GET`  | `/`       | `{"message": "¡El backend de Ayudante PDF está funcionando correctamente! 🚀"}` |
| `GET`  | `/health` | `{"status": "healthy"}`                                                         |

No forman parte del flujo de negocio, pero aparecen en `/openapi.json`.

### 5.9 `POST /api/v1/adaptations`

Genera una versión adaptada de una barrera. Es **stateless**: no recibe
`session_id` ni guarda el resultado.

- **Request:** `Content-Type: application/json` con
  [`AdaptationRequest`](#adaptationrequest).
- **Response `200`:** [`Adaptation`](#adaptation).
- **Errores:** `422 text_too_long`, `422 observation_not_adaptable`,
  `422 unknown_rule` y `422 VALIDATION_ERROR` si el body no cumple el schema.

`type` es obligatorio y manda. `rule_id` es opcional y solo enriquece el
prompt; si se envía, se valida contra el catálogo de reglas.

| `rule_id`               | `type`                                     |
| ----------------------- | ------------------------------------------ |
| `long_paragraph`        | `simplify`                                 |
| `long_sentence`         | `simplify`                                 |
| `dense_section`         | `simplify`                                 |
| `undefined_term`        | `simplify`                                 |
| `ambiguous_instruction` | `clarify`                                  |
| `visual_reference`      | `describe`                                 |
| `image_only_page`       | `describe`                                 |
| `image_without_alt`     | `alt_text`                                 |
| `unclear_sequence`      | `sequence`                                 |
| `no_headings`           | no adaptable (`observation_not_adaptable`) |
| `heading_skip`          | no adaptable (`observation_not_adaptable`) |

`adapted_text` es texto plano: no incluye HTML ni Markdown y separa los
párrafos con `\n\n`. El endpoint nunca devuelve `5xx` por un fallo de la IA:

| Caso                                                         | `source` | `ai_status`   | `adapted_text`                    |
| ------------------------------------------------------------ | -------- | ------------- | --------------------------------- |
| La IA responde                                               | `ai`     | `ok`          | texto adaptado                    |
| IA caída y `simplify` con 4+ oraciones y más de 120 palabras | `local`  | `unavailable` | texto dividido en párrafos        |
| IA caída, resto de tipos                                     | `null`   | `unavailable` | `null` + recomendación en `notes` |
| Salida vacía, idéntica al original o con HTML tras reintento | `null`   | `unavailable` | `null`                            |

El fallback local solo divide el texto en párrafos; no lo reescribe. Para
`alt_text`, `notes` siempre aclara que no se analizó la imagen.

### 5.10 `POST /api/v1/sessions/{session_id}/export`

Aplica los textos finales de uno o más bloques sobre el PDF original y devuelve
el PDF adaptado. Es **stateless**: no persiste los textos ni cambia el estado de
la sesión.

- **Request:** `Content-Type: application/json` con [`ExportRequest`](#exportrequest).
- **Response `200`:** `application/pdf` con `Content-Disposition: attachment;
filename="documento-adaptado.pdf"; filename*=UTF-8''<stem>_adaptado.pdf`.
- **Solo para sesiones PDF** con contenido extraído. El título del archivo sale
  de `SessionResponse.filename`, sin la extensión `.pdf` y saneado.
- **Errores:** `404 session_not_found`, `409 content_not_extracted`,
  `409 export_unavailable`, `422 unknown_block`, `422 block_without_bbox`,
  `422 duplicate_block_id`, `422 empty_text`, `422 text_too_long`,
  `422 invalid_pdf` y `422 VALIDATION_ERROR`.

Reglas de aplicación:

- Cada `block_id` debe existir, tener `page` y `bbox`, y no repetirse.
- Se dibuja un rectángulo blanco sobre el `bbox` (padding 0.5 pt) y encima el
  texto nuevo, envuelto al ancho del bloque.
- Se conservan los saltos de línea y los párrafos del texto enviado: `\n` corta
  la línea y una línea en blanco (`\n\n` o más) separa párrafos con un
  interlineado vacío. Los `\r\n` se normalizan a `\n`.
- Fuente `Helvetica`; `Helvetica-Bold` para `heading`. Tamaño inicial:
  `ContentBlock.font_size` o 10 pt. Interlineado 1.25×. Si no entra, se reduce
  de a 0.5 pt hasta 6 pt; si aun así no entra, se recorta con `…`.
- En bloques `image`, el texto va como leyenda en la franja inferior del `bbox`
  (hasta 30 % del alto) para no tapar la imagen.
- Las páginas sin edits y el resto de los objetos quedan intactos. El PDF de
  salida conserva la cantidad de páginas y el MediaBox de cada una.

> **Limitación:** el reemplazo es visual. El texto original sigue en la capa de
> texto del PDF, así que copiar/pegar o un lector de pantalla pueden ver ambos
> textos. La redacción real requiere PyMuPDF o cirugía de content streams y
> queda para una issue aparte.

## 6. Modelos

### `SessionResponse`

| Campo         | Tipo                    | Nulo | Descripción                                       |
| ------------- | ----------------------- | ---- | ------------------------------------------------- |
| `session_id`  | `string` (UUID)         | No   | Identificador único de la sesión.                 |
| `source_type` | `SourceType`            | No   | `pdf` o `text`.                                   |
| `filename`    | `string`                | Sí   | Nombre del PDF o título del texto.                |
| `size_bytes`  | `integer`               | Sí   | Bytes del archivo o del texto en UTF-8.           |
| `status`      | `SessionStatus`         | No   | `uploaded`, `extracted`, `analyzed`, `completed`. |
| `created_at`  | `string` (ISO 8601 UTC) | No   | Fecha de creación.                                |

### `TextInput`

| Campo   | Tipo     | Nulo | Restricciones                              |
| ------- | -------- | ---- | ------------------------------------------ |
| `title` | `string` | Sí   | Máximo 200 caracteres.                     |
| `text`  | `string` | No   | No puede estar vacío ni ser solo espacios. |

### `ExtractedContent`

| Campo         | Tipo             | Nulo | Descripción                                                         |
| ------------- | ---------------- | ---- | ------------------------------------------------------------------- |
| `session_id`  | `string` (UUID)  | No   | Sesión de origen.                                                   |
| `source_type` | `SourceType`     | No   | `pdf` o `text`.                                                     |
| `title`       | `string`         | Sí   | En texto, el título de la sesión; en PDF, el título de menor nivel. |
| `page_count`  | `integer`        | Sí   | Páginas del PDF; `null` para texto.                                 |
| `pages`       | `PageSize[]`     | No   | Tamaño de cada página del PDF; `[]` en texto pegado.                |
| `summary`     | `ContentSummary` | No   | Conteos del material.                                               |
| `blocks`      | `ContentBlock[]` | No   | Bloques en orden de lectura.                                        |

### `ContentBlock`

| Campo        | Tipo        | Nulo | Descripción                                                    |
| ------------ | ----------- | ---- | -------------------------------------------------------------- |
| `id`         | `string`    | No   | `b1`, `b2`, …                                                  |
| `type`       | `BlockType` | No   | `heading`, `paragraph`, `list`, `image`.                       |
| `page`       | `integer`   | Sí   | Página donde empieza el bloque (desde 1); `null` en texto.     |
| `text`       | `string`    | Sí   | Texto del título o párrafo.                                    |
| `level`      | `integer`   | Sí   | Nivel de título (1 a 6); solo en `heading`.                    |
| `items`      | `string[]`  | Sí   | Ítems sin viñeta ni numeración; solo en `list`.                |
| `word_count` | `integer`   | No   | Palabras del bloque; siempre `0` en imágenes.                  |
| `alt_text`   | `string`    | Sí   | Texto alternativo de la imagen. En PDFs hoy siempre es `null`. |
| `width`      | `number`    | Sí   | Ancho en puntos; solo en imágenes.                             |
| `height`     | `number`    | Sí   | Alto en puntos; solo en imágenes.                              |
| `bbox`       | `BBox`      | Sí   | Rectángulo del bloque en puntos; `null` en texto pegado.       |
| `font_size`  | `number`    | Sí   | Tamaño mediano de los caracteres en puntos; `null` en texto.   |

### `BBox`

Rectángulo de un bloque sobre la página del PDF.

| Campo    | Tipo     | Nulo | Descripción                     |
| -------- | -------- | ---- | ------------------------------- |
| `x0`     | `number` | No   | Borde izquierdo, en puntos PDF. |
| `top`    | `number` | No   | Borde superior, en puntos PDF.  |
| `x1`     | `number` | No   | Borde derecho, en puntos PDF.   |
| `bottom` | `number` | No   | Borde inferior, en puntos PDF.  |

Las coordenadas están en **puntos PDF** (72 por pulgada), con el origen
**arriba-izquierda**, igual que las devuelve `pdfplumber`. Se redondean a un
decimal. El backend no renderiza el PDF: si el frontend usa pdf.js, que trabaja
con origen abajo-izquierda, tiene que convertir el eje Y con
`top_js = page.height - bbox.bottom` (y `bottom_js = page.height - bbox.top`).

En títulos, párrafos y listas el rectángulo es la unión de las líneas que
forman el bloque. En imágenes es el rectángulo de la imagen. Puede haber
valores levemente negativos o fuera de página si el texto está rotado o
desbordado; no se recorta.

### `PageSize`

Tamaño visible de una página del PDF.

| Campo    | Tipo      | Nulo | Descripción                                |
| -------- | --------- | ---- | ------------------------------------------ |
| `page`   | `integer` | No   | Número de página, desde 1.                 |
| `width`  | `number`  | No   | Ancho visible de la página, en puntos PDF. |
| `height` | `number`  | No   | Alto visible de la página, en puntos PDF.  |

### `ContentSummary`

| Campo                | Tipo      | Nulo | Descripción                               |
| -------------------- | --------- | ---- | ----------------------------------------- |
| `word_count`         | `integer` | No   | Total de palabras; las imágenes no suman. |
| `heading_count`      | `integer` | No   | Cantidad de títulos.                      |
| `paragraph_count`    | `integer` | No   | Cantidad de párrafos.                     |
| `list_count`         | `integer` | No   | Cantidad de listas.                       |
| `image_count`        | `integer` | No   | Cantidad de imágenes.                     |
| `images_without_alt` | `integer` | No   | Imágenes sin texto alternativo.           |

### `Observation`

| Campo            | Tipo                | Nulo | Descripción                                                      |
| ---------------- | ------------------- | ---- | ---------------------------------------------------------------- |
| `id`             | `string`            | No   | Identificador estable (ver [Convenciones](#3-convenciones)).     |
| `rule_id`        | `string`            | No   | Código de la regla que la produjo.                               |
| `category`       | `Category`          | No   | Dimensión de accesibilidad.                                      |
| `severity`       | `Severity`          | No   | `high`, `medium` o `low`.                                        |
| `source`         | `ObservationSource` | No   | `rule` o `ai`.                                                   |
| `title`          | `string`            | No   | Nombre corto del problema.                                       |
| `detail`         | `string`            | Sí   | Dato puntual que explica la observación.                         |
| `why_it_matters` | `string`            | No   | Por qué afecta el acceso al material.                            |
| `recommendation` | `string`            | No   | Qué hacer para resolverlo.                                       |
| `block_id`       | `string`            | Sí   | Bloque afectado; `null` si abarca todo el material o una página. |
| `page`           | `integer`           | Sí   | Página del bloque; `null` en texto pegado.                       |
| `excerpt`        | `string`            | Sí   | Fragmento que ubica el problema; `null` si no aplica.            |

### `CategoryResult`

| Campo              | Tipo             | Nulo | Descripción                           |
| ------------------ | ---------------- | ---- | ------------------------------------- |
| `category`         | `Category`       | No   | Categoría evaluada.                   |
| `severity`         | `DiagnosisLevel` | No   | Peor nivel dentro de la categoría.    |
| `barrier_count`    | `integer`        | No   | Observaciones con severidad `high`.   |
| `review_count`     | `integer`        | No   | Observaciones con severidad `medium`. |
| `suggestion_count` | `integer`        | No   | Observaciones con severidad `low`.    |

### `Diagnosis`

| Campo          | Tipo                    | Nulo | Descripción                                               |
| -------------- | ----------------------- | ---- | --------------------------------------------------------- |
| `session_id`   | `string` (UUID)         | No   | Sesión analizada.                                         |
| `score`        | `integer`               | No   | Puntaje orientativo de 0 a 100.                           |
| `level`        | `DiagnosisLevel`        | No   | `ok`, `review` o `barrier`.                               |
| `disclaimer`   | `string`                | No   | Aviso de que el puntaje no es una certificación.          |
| `categories`   | `CategoryResult[]`      | No   | Siempre las 6 categorías, en orden.                       |
| `observations` | `Observation[]`         | No   | Puede ser `[]`.                                           |
| `created_at`   | `string` (ISO 8601 UTC) | No   | Fecha y hora del diagnóstico.                             |
| `ai_status`    | `AiStatus`              | No   | `ok`, `unavailable` o `skipped`.                          |
| `ai_notice`    | `string`                | Sí   | Aviso de privacidad; `null` cuando `ai_status="skipped"`. |
| `ai_truncated` | `boolean`               | No   | `true` si la IA analizó solo una parte del material.      |

### `AdaptationRequest`

| Campo            | Tipo             | Requerido | Restricciones                                       |
| ---------------- | ---------------- | --------- | --------------------------------------------------- |
| `type`           | `AdaptationType` | Sí        | Tipo de adaptación pedida.                          |
| `original_text`  | `string`         | Sí        | No puede quedar vacío; máximo 8.000 caracteres.     |
| `rule_id`        | `string`         | No        | Código del catálogo; enriquece el prompt.           |
| `category`       | `Category`       | No        | Dimensión de accesibilidad de la barrera.           |
| `title`          | `string`         | No        | Máximo 200 caracteres.                              |
| `detail`         | `string`         | No        | Máximo 500 caracteres.                              |
| `recommendation` | `string`         | No        | Máximo 500 caracteres.                              |
| `context_before` | `string`         | No        | Texto anterior al bloque; máximo 1.000 caracteres.  |
| `context_after`  | `string`         | No        | Texto posterior al bloque; máximo 1.000 caracteres. |

### `Adaptation`

| Campo           | Tipo                    | Nulo | Descripción                                                  |
| --------------- | ----------------------- | ---- | ------------------------------------------------------------ |
| `id`            | `string` (UUID v4)      | No   | Identificador único de la adaptación.                        |
| `type`          | `AdaptationType`        | No   | Tipo de adaptación aplicado.                                 |
| `rule_id`       | `string`                | Sí   | Regla que originó la barrera.                                |
| `original_text` | `string`                | No   | Texto recibido, normalizado.                                 |
| `adapted_text`  | `string`                | Sí   | Texto plano adaptado; `null` si no se pudo generar.          |
| `notes`         | `string`                | Sí   | Qué se hizo, limitaciones o recomendación manual (máx. 500). |
| `source`        | `AdaptationSource`      | Sí   | `ai` o `local`; `null` si no hubo adaptación.                |
| `ai_status`     | `AiStatus`              | No   | `ok` o `unavailable` (no se usa `skipped`).                  |
| `ai_notice`     | `string`                | Sí   | Aviso de privacidad y alcance del uso de la IA.              |
| `provider`      | `string`                | Sí   | Nombre visible del proveedor usado o intentado.              |
| `created_at`    | `string` (ISO 8601 UTC) | No   | Fecha de creación.                                           |

### `ExportRequest`

| Campo   | Tipo           | Requerido | Restricciones                                   |
| ------- | -------------- | --------- | ----------------------------------------------- |
| `edits` | `ExportEdit[]` | Sí        | Al menos un edit; los `block_id` no se repiten. |

### `ExportEdit`

| Campo      | Tipo     | Requerido | Restricciones                                           |
| ---------- | -------- | --------- | ------------------------------------------------------- |
| `block_id` | `string` | Sí        | Debe existir en el contenido extraído.                  |
| `text`     | `string` | Sí        | No vacío después de `strip()`; máximo 8.000 caracteres. |

### `ErrorResponse`

| Campo     | Tipo     | Nulo | Descripción                                   |
| --------- | -------- | ---- | --------------------------------------------- |
| `code`    | `string` | No   | Código estable para ramificar en el frontend. |
| `message` | `string` | No   | Mensaje legible para mostrar o registrar.     |

### Enums

| Enum                | Valores                                                                              |
| ------------------- | ------------------------------------------------------------------------------------ |
| `SourceType`        | `pdf`, `text`                                                                        |
| `SessionStatus`     | `uploaded`, `extracted`, `analyzed`, `completed`                                     |
| `BlockType`         | `heading`, `paragraph`, `list`, `image`                                              |
| `Category`          | `comprehension`, `structure`, `visual`, `representation`, `multimedia`, `navigation` |
| `Severity`          | `high`, `medium`, `low`                                                              |
| `ObservationSource` | `rule`, `ai`                                                                         |
| `DiagnosisLevel`    | `ok`, `review`, `barrier`                                                            |
| `AiStatus`          | `ok`, `unavailable`, `skipped`                                                       |
| `AdaptationType`    | `simplify`, `clarify`, `describe`, `alt_text`, `sequence`                            |
| `AdaptationSource`  | `ai`, `local`                                                                        |

### Nulabilidad resumida

Pueden ser `null`:

`SessionResponse.filename`, `SessionResponse.size_bytes`,
`ExtractedContent.title`, `ExtractedContent.page_count`, `ContentBlock.page`,
`ContentBlock.text`, `ContentBlock.level`, `ContentBlock.items`,
`ContentBlock.alt_text`, `ContentBlock.width`, `ContentBlock.height`,
`ContentBlock.bbox`, `ContentBlock.font_size`,
`Observation.detail`, `Observation.block_id`, `Observation.page`,
`Observation.excerpt`, `Diagnosis.ai_notice`, `Adaptation.rule_id`,
`Adaptation.adapted_text`, `Adaptation.notes`, `Adaptation.source`,
`Adaptation.ai_notice`, `Adaptation.provider`.

No son `null` (aunque el array esté vacío): `pages`, `categories`,
`observations`, `blocks`, `items` cuando el bloque es una lista, `summary`.

## 7. Ejemplos de respuesta

Los UUID de cada ejemplo son independientes entre sí. Se capturaron ejecutando
la API local.

### 7.1 Sesión desde texto

Request:

```http
POST /api/v1/sessions/text
Content-Type: application/json
```

```json
{
  "title": "Biología",
  "text": "# La célula\n\nLa célula es la unidad básica de la vida.\n\n- Membrana\n- Citoplasma\n\nTexto suelto."
}
```

Response `201`:

```json
{
  "session_id": "4e9d9e9e-2e96-4db2-b3c1-ef5623160c31",
  "source_type": "text",
  "filename": "Biología",
  "size_bytes": 97,
  "status": "uploaded",
  "created_at": "2026-11-12T17:14:03.355261Z"
}
```

### 7.2 Sesión desde PDF

Response `201`:

```json
{
  "session_id": "f4c9e995-efe3-450a-bc4f-56c49780f1d0",
  "source_type": "pdf",
  "filename": "TP_Geografia_Europa.pdf",
  "size_bytes": 42543,
  "status": "uploaded",
  "created_at": "2026-11-12T17:14:07.570226Z"
}
```

### 7.3 Contenido extraído de texto

Response `200` de `POST /extract` o de `GET /content`:

```json
{
  "session_id": "4e9d9e9e-2e96-4db2-b3c1-ef5623160c31",
  "source_type": "text",
  "title": "Biología",
  "page_count": null,
  "pages": [],
  "summary": {
    "word_count": 15,
    "heading_count": 1,
    "paragraph_count": 2,
    "list_count": 1,
    "image_count": 0,
    "images_without_alt": 0
  },
  "blocks": [
    {
      "id": "b1",
      "type": "heading",
      "page": null,
      "text": "La célula",
      "level": 1,
      "items": null,
      "word_count": 2,
      "alt_text": null,
      "width": null,
      "height": null,
      "bbox": null,
      "font_size": null
    },
    {
      "id": "b2",
      "type": "paragraph",
      "page": null,
      "text": "La célula es la unidad básica de la vida.",
      "level": null,
      "items": null,
      "word_count": 9,
      "alt_text": null,
      "width": null,
      "height": null,
      "bbox": null,
      "font_size": null
    },
    {
      "id": "b3",
      "type": "list",
      "page": null,
      "text": null,
      "level": null,
      "items": ["Membrana", "Citoplasma"],
      "word_count": 2,
      "alt_text": null,
      "width": null,
      "height": null,
      "bbox": null,
      "font_size": null
    },
    {
      "id": "b4",
      "type": "paragraph",
      "page": null,
      "text": "Texto suelto.",
      "level": null,
      "items": null,
      "word_count": 2,
      "alt_text": null,
      "width": null,
      "height": null,
      "bbox": null,
      "font_size": null
    }
  ]
}
```

### 7.4 Contenido extraído de PDF (abreviado)

Ejemplo del mismo PDF de 7.2. **Se omitieron los bloques `b2` a `b5` y `b7`
para abreviar**; la respuesta real los incluye todos. Sirve para ver `page`,
imágenes, `alt_text`, `width`, `height`, `pages`, `bbox`, `page_count` y
`images_without_alt`.

```json
{
  "session_id": "f4c9e995-efe3-450a-bc4f-56c49780f1d0",
  "source_type": "pdf",
  "title": null,
  "page_count": 2,
  "pages": [
    { "page": 1, "width": 595.3, "height": 841.9 },
    { "page": 2, "width": 595.3, "height": 841.9 }
  ],
  "summary": {
    "word_count": 537,
    "heading_count": 0,
    "paragraph_count": 6,
    "list_count": 0,
    "image_count": 2,
    "images_without_alt": 2
  },
  "blocks": [
    {
      "id": "b1",
      "type": "paragraph",
      "page": 1,
      "text": "TRABAJO PRÁCTICO N.º 1 — GEOGRAFÍA",
      "level": null,
      "items": null,
      "word_count": 6,
      "alt_text": null,
      "width": null,
      "height": null,
      "bbox": { "x0": 57.0, "top": 53.4, "x1": 257.4, "bottom": 63.4 },
      "font_size": 10.5
    },
    {
      "id": "b6",
      "type": "image",
      "page": 2,
      "text": null,
      "level": null,
      "items": null,
      "word_count": 0,
      "alt_text": null,
      "width": 209.8,
      "height": 141.7,
      "bbox": { "x0": 192.8, "top": 51.4, "x1": 402.5, "bottom": 193.1 },
      "font_size": null
    },
    {
      "id": "b8",
      "type": "paragraph",
      "page": 2,
      "text": "A partir de lo trabajado, elaboren una interpretación integral de la información.",
      "level": null,
      "items": null,
      "word_count": 12,
      "alt_text": null,
      "width": null,
      "height": null,
      "bbox": { "x0": 57.0, "top": 346.9, "x1": 402.7, "bottom": 356.9 },
      "font_size": 10.5
    }
  ]
}
```

> En PDFs, `alt_text` siempre es `null` porque `pdfplumber` no expone el texto
> alternativo original. Por eso `image_without_alt` puede dar falsos positivos.

### 7.5 Diagnóstico solo con reglas

Response `200` de `POST /analyze?use_ai=false` para el PDF de 7.2:

```json
{
  "session_id": "f4c9e995-efe3-450a-bc4f-56c49780f1d0",
  "score": 46,
  "level": "barrier",
  "disclaimer": "El puntaje es un indicador orientativo. No constituye una certificación formal de accesibilidad.",
  "categories": [
    {
      "category": "comprehension",
      "severity": "barrier",
      "barrier_count": 2,
      "review_count": 0,
      "suggestion_count": 0
    },
    {
      "category": "structure",
      "severity": "barrier",
      "barrier_count": 1,
      "review_count": 0,
      "suggestion_count": 0
    },
    {
      "category": "visual",
      "severity": "barrier",
      "barrier_count": 2,
      "review_count": 1,
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
      "id": "no_headings:b1",
      "rule_id": "no_headings",
      "category": "structure",
      "severity": "high",
      "source": "rule",
      "title": "El material no tiene títulos",
      "detail": "El material tiene 537 palabras y ningún título.",
      "why_it_matters": "Los títulos permiten ubicarse y saltar entre secciones; las personas que usan lector de pantalla navegan por ellos.",
      "recommendation": "Organizar el contenido en secciones y ponerles títulos.",
      "block_id": "b1",
      "page": 1,
      "excerpt": "TRABAJO PRÁCTICO N.º 1 — GEOGRAFÍA"
    },
    {
      "id": "long_paragraph:b5",
      "rule_id": "long_paragraph",
      "category": "comprehension",
      "severity": "high",
      "source": "rule",
      "title": "Párrafo muy extenso",
      "detail": "Tiene 495 palabras.",
      "why_it_matters": "Los bloques de texto largos cansan y dificultan seguir la idea, sobre todo a quienes tienen dificultades de lectura o atención.",
      "recommendation": "Dividir el párrafo en bloques más cortos, con una idea en cada uno.",
      "block_id": "b5",
      "page": 1,
      "excerpt": "Europa constituye una unidad territorial de configuración sumamente compleja cuya individualización como continente responde tanto a criterios…"
    },
    {
      "id": "long_sentence:b5",
      "rule_id": "long_sentence",
      "category": "comprehension",
      "severity": "high",
      "source": "rule",
      "title": "Oraciones muy largas",
      "detail": "10 oraciones superan las 30 palabras; la más larga tiene 79.",
      "why_it_matters": "Las oraciones extensas obligan a retener muchas ideas a la vez y se entienden con más esfuerzo.",
      "recommendation": "Reescribir con oraciones más breves, de una idea cada una.",
      "block_id": "b5",
      "page": 1,
      "excerpt": "Europa constituye una unidad territorial de configuración sumamente compleja cuya individualización como continente responde tanto a criterios…"
    },
    {
      "id": "image_only_page:pagina-2",
      "rule_id": "image_only_page",
      "category": "visual",
      "severity": "medium",
      "source": "rule",
      "title": "Página con poco texto y con imágenes",
      "detail": "La página 2 tiene 12 palabras y 2 imágenes.",
      "why_it_matters": "Si la información está solo en imágenes, no llega a quienes no pueden verlas.",
      "recommendation": "Revisar que el contenido de las imágenes también esté explicado con texto.",
      "block_id": null,
      "page": 2,
      "excerpt": null
    },
    {
      "id": "image_without_alt:b6",
      "rule_id": "image_without_alt",
      "category": "visual",
      "severity": "high",
      "source": "rule",
      "title": "Imagen sin descripción",
      "detail": "Está en la página 2. En un PDF no se puede leer el texto alternativo original: la imagen podría tenerlo y aun así marcarse.",
      "why_it_matters": "La información visual puede no estar disponible para quienes usan lectores de pantalla.",
      "recommendation": "Incorporar un texto alternativo que describa la información relevante de la imagen.",
      "block_id": "b6",
      "page": 2,
      "excerpt": null
    },
    {
      "id": "image_without_alt:b7",
      "rule_id": "image_without_alt",
      "category": "visual",
      "severity": "high",
      "source": "rule",
      "title": "Imagen sin descripción",
      "detail": "Está en la página 2. En un PDF no se puede leer el texto alternativo original: la imagen podría tenerlo y aun así marcarse.",
      "why_it_matters": "La información visual puede no estar disponible para quienes usan lectores de pantalla.",
      "recommendation": "Incorporar un texto alternativo que describa la información relevante de la imagen.",
      "block_id": "b7",
      "page": 2,
      "excerpt": null
    }
  ],
  "created_at": "2026-11-12T17:14:07.649943Z",
  "ai_status": "skipped",
  "ai_notice": null,
  "ai_truncated": false
}
```

### 7.6 Diagnóstico con IA disponible (`ai_status="ok"`)

Fragmento de una respuesta real. **Se omite `categories` para abreviar**; en la
respuesta completa vienen siempre las 6 categorías. Nótese `source: "ai"` y
`severity: "medium"`, que son fijos para las observaciones semánticas.

```json
{
  "session_id": "b284627f-eb34-461d-8d23-fbd2d5b0c478",
  "score": 96,
  "level": "review",
  "observations": [
    {
      "id": "ai:undefined_term:b1",
      "rule_id": "undefined_term",
      "category": "representation",
      "severity": "medium",
      "source": "ai",
      "title": "Término técnico sin explicar",
      "detail": "No se explica qué significa «lo indicado».",
      "why_it_matters": "Quien no conoce el término pierde el hilo del contenido y no siempre puede buscarlo mientras estudia.",
      "recommendation": "Definir el término la primera vez que aparece o incluirlo en un glosario.",
      "block_id": "b1",
      "page": null,
      "excerpt": "Resolvé el ejercicio según lo indicado en clase."
    }
  ],
  "ai_status": "ok",
  "ai_notice": "El análisis con IA envía el texto del material a Google Gemini. No se envía el archivo, solo el texto extraído.",
  "ai_truncated": false
}
```

### 7.7 Diagnóstico con IA no disponible (`ai_status="unavailable"`)

Fragmento de una respuesta real. El diagnóstico por reglas sigue completo y la
respuesta es `200`:

```json
{
  "score": 100,
  "level": "ok",
  "observations": [],
  "ai_status": "unavailable",
  "ai_notice": "El análisis con IA envía el texto del material a Google Gemini. No se envía el archivo, solo el texto extraído. No se pudo completar el análisis con IA; el diagnóstico por reglas sigue disponible.",
  "ai_truncated": false
}
```

> Con `ai_status="skipped"` (por `use_ai=false`) se cumple:
> `ai_notice: null` y `ai_truncated: false`.
>
> Con OpenRouter, `ai_notice` nombra a OpenRouter y al proveedor del modelo
> configurado. El formato exacto del aviso puede variar; no ramificar por su
> texto.

### 7.8 Error

Response `404`:

```json
{
  "code": "session_not_found",
  "message": "La sesión solicitada no existe."
}
```

### 7.9 Adaptación con IA disponible (`source="ai"`)

Response `200` de `POST /api/v1/adaptations`:

```json
{
  "id": "0f6f2f3e-9a3b-4a1e-9c3d-2b7f1a5c8d41",
  "type": "simplify",
  "rule_id": "long_paragraph",
  "original_text": "La célula es la unidad básica de la vida. Todas las células cumplen funciones esenciales. Estas funciones incluyen la nutrición y la reproducción. Además, permiten mantener el organismo.",
  "adapted_text": "La célula es la unidad básica de la vida.\n\nTodas las células cumplen funciones esenciales, como la nutrición y la reproducción.",
  "notes": "Se dividió el párrafo y se acortaron las oraciones.",
  "source": "ai",
  "ai_status": "ok",
  "ai_notice": "El análisis con IA envía el texto del material a Google Gemini. No se envía el archivo, solo el texto extraído.",
  "provider": "Google Gemini",
  "created_at": "2026-11-14T18:20:00.123456Z"
}
```

### 7.10 Adaptación con fallback local (`source="local"`)

Con la IA caída, `simplify` divide el texto sin reescribirlo:

```json
{
  "id": "4b8d1c22-5e6f-4f0a-8d3e-7c9a2b1f6e55",
  "type": "simplify",
  "rule_id": "long_paragraph",
  "original_text": "Primera oración del párrafo. Segunda oración del párrafo. Tercera oración del párrafo. Cuarta oración del párrafo.",
  "adapted_text": "Primera oración del párrafo. Segunda oración del párrafo.\n\nTercera oración del párrafo. Cuarta oración del párrafo.",
  "notes": "Se dividió el texto automáticamente sin IA. Revisá el resultado antes de aplicarlo.",
  "source": "local",
  "ai_status": "unavailable",
  "ai_notice": "El análisis con IA envía el texto del material a Google Gemini. No se envía el archivo, solo el texto extraído. No se pudo generar la adaptación; se muestra la recomendación para hacerlo a mano.",
  "provider": "Google Gemini",
  "created_at": "2026-11-14T18:21:00.654321Z"
}
```

### 7.11 Adaptación con IA no disponible (`source=null`)

Para tipos sin fallback, la respuesta sigue siendo `200` y devuelve la
recomendación para hacerlo a mano:

```json
{
  "id": "9c2e7a10-3d4b-4c5f-9e8a-1b2c3d4e5f60",
  "type": "clarify",
  "rule_id": "ambiguous_instruction",
  "original_text": "Resolvé el ejercicio según lo indicado.",
  "adapted_text": null,
  "notes": "Reescribir la consigna con un verbo claro, un solo pedido y, si hace falta, un ejemplo.",
  "source": null,
  "ai_status": "unavailable",
  "ai_notice": "El análisis con IA envía el texto del material a Google Gemini. No se envía el archivo, solo el texto extraído. No se pudo generar la adaptación; se muestra la recomendación para hacerlo a mano.",
  "provider": "Google Gemini",
  "created_at": "2026-11-14T18:22:00.111111Z"
}
```

### 7.12 Exportación del PDF adaptado

La respuesta es binaria (`application/pdf`), no JSON. Ejemplo:

```bash
curl -s -X POST "$BASE/sessions/$SESSION_ID/export" \
  -H "Content-Type: application/json" \
  -d '{"edits":[
    {"block_id":"b1","text":"La célula es la unidad básica de la vida."},
    {"block_id":"b2","text":"El núcleo contiene el material genético."}
  ]}' \
  -D headers.txt -o documento_adaptado.pdf
```

Headers esperados:

```text
HTTP/1.1 200 OK
content-type: application/pdf
content-disposition: attachment; filename="documento-adaptado.pdf"; filename*=UTF-8''documento_adaptado.pdf
```

## 8. Catálogo de errores

Todas las respuestas de error tienen la forma
[`ErrorResponse`](#errorresponse): `{ "code": "...", "message": "..." }`.

| HTTP  | `code`                      | Cuándo                                                            |
| ----- | --------------------------- | ----------------------------------------------------------------- |
| `400` | `empty_content`             | Archivo vacío, o texto vacío/solo espacios.                       |
| `400` | `invalid_pdf`               | El archivo no empieza con la firma `%PDF`.                        |
| `404` | `session_not_found`         | La sesión indicada no existe.                                     |
| `409` | `content_not_extracted`     | Se pidió el contenido antes de `POST /extract`.                   |
| `409` | `session_not_analyzed`      | Se pidió el diagnóstico antes de `POST /analyze`.                 |
| `409` | `export_unavailable`        | Se intentó exportar una sesión creada desde texto pegado.         |
| `413` | `file_too_large`            | El archivo supera `MAX_UPLOAD_MB` (25 MB por defecto).            |
| `415` | `unsupported_format`        | La extensión del archivo no es `.pdf`.                            |
| `422` | `no_extractable_text`       | El material no tiene texto (por ejemplo, un PDF escaneado).       |
| `422` | `text_too_long`             | `original_text` o el texto de un bloque supera 8.000 caracteres.  |
| `422` | `observation_not_adaptable` | La regla no se puede adaptar (`no_headings`, `heading_skip`).     |
| `422` | `unknown_rule`              | El `rule_id` no existe en el catálogo de reglas.                  |
| `422` | `invalid_pdf`               | El PDF está dañado o protegido (al extraer, analizar o exportar). |
| `422` | `unknown_block`             | Un `block_id` del export no existe en el contenido.               |
| `422` | `block_without_bbox`        | Un bloque del export no tiene coordenadas válidas en el PDF.      |
| `422` | `duplicate_block_id`        | Un `block_id` aparece más de una vez en la exportación.           |
| `422` | `empty_text`                | El texto de un bloque del export queda vacío.                     |
| `422` | `text_too_long`             | El texto de un bloque del export supera 8.000 caracteres.         |
| `422` | `VALIDATION_ERROR`          | Body, query o UUID inválido. `message` detalla el campo.          |
| `404` | `HTTP_404`                  | Ruta inexistente.                                                 |
| `405` | `HTTP_405`                  | Método no permitido para la ruta.                                 |
| `500` | `INTERNAL_ERROR`            | Error inesperado del servidor.                                    |

Mensajes actuales de los errores de aplicación:

| `code`                         | `message`                                                                                  |
| ------------------------------ | ------------------------------------------------------------------------------------------ |
| `empty_content` (file)         | `El archivo está vacío.`                                                                   |
| `empty_content` (text)         | `El texto no puede estar vacío.`                                                           |
| `invalid_pdf` (upload)         | `El archivo no es un PDF válido.`                                                          |
| `invalid_pdf` (extract/export) | `No se pudo leer el PDF. Puede estar dañado o protegido.`                                  |
| `file_too_large`               | `El archivo supera el límite de 25 MB permitido.`                                          |
| `unsupported_format`           | `Por ahora solo se aceptan archivos PDF.`                                                  |
| `session_not_found`            | `La sesión solicitada no existe.`                                                          |
| `content_not_extracted`        | `El contenido todavía no fue extraído.`                                                    |
| `session_not_analyzed`         | `La sesión todavía no fue analizada.`                                                      |
| `export_unavailable`           | `La exportación solo está disponible para sesiones creadas desde un PDF.`                  |
| `unknown_block`                | `El bloque indicado no existe en el contenido extraído.`                                   |
| `block_without_bbox`           | `El bloque indicado no tiene coordenadas válidas en el PDF.`                               |
| `duplicate_block_id`           | `El bloque indicado está repetido en la solicitud.`                                        |
| `empty_text`                   | `El texto de un bloque no puede estar vacío.`                                              |
| `text_too_long` (export)       | `El texto de un bloque supera el límite de 8.000 caracteres.`                              |
| `no_extractable_text`          | `No se encontró texto en el material. Si es un PDF escaneado, no se puede leer por ahora.` |
| `text_too_long`                | `El texto a adaptar supera el límite de 8.000 caracteres.`                                 |
| `observation_not_adaptable`    | `La barrera indicada no se puede adaptar automáticamente.`                                 |
| `unknown_rule`                 | `La regla indicada no existe en el catálogo.`                                              |

> No ramificar por `message`: usar siempre `code`. Los mensajes pueden cambiar.

## 9. Guía para armar mocks

### Flujo mínimo

```bash
BASE=http://127.0.0.1:8000/api/v1

# 1. Crear sesión desde texto
SESSION=$(curl -s -X POST "$BASE/sessions/text" \
  -H "Content-Type: application/json" \
  -d '{"title":"Biología","text":"# La célula\n\nLa célula es la unidad básica de la vida."}')

# 2. Extraer contenido
SESSION_ID=$(echo "$SESSION" | jq -r .session_id)
curl -s -X POST "$BASE/sessions/$SESSION_ID/extract" | jq

# 3. Analizar sin IA (determinista, no requiere clave)
curl -s -X POST "$BASE/sessions/$SESSION_ID/analyze?use_ai=false" | jq

# 4. Consultar el diagnóstico guardado
curl -s "$BASE/sessions/$SESSION_ID/diagnosis" | jq

# 5. Adaptar una barrera (stateless, no requiere sesión)
curl -s -X POST "$BASE/adaptations" \
  -H "Content-Type: application/json" \
  -d '{"type":"simplify","rule_id":"long_paragraph","original_text":"Primera oración. Segunda oración. Tercera oración. Cuarta oración."}' | jq
```

Para un PDF:

```bash
curl -s -X POST "$BASE/sessions/file" \
  -F "file=@documento.pdf" | jq
```

### Reglas para los mocks

1. **UUIDs válidos:** usar UUID v4 (`crypto.randomUUID()` en el navegador).
2. **Fechas:** ISO 8601 UTC con `Z`; no usar fechas locales.
3. **Categorías:** generar siempre las 6, en el orden del enum, incluso con
   conteos en cero.
4. **Observaciones:** pueden ser `[]`. Si hay varias, ordenarlas por `page` y
   luego por el orden de `blocks`.
5. **Severidad:** no mezclar escalas. Una observación nunca lleva `ok`; un
   diagnóstico nunca lleva `high`.
6. **Texto vs. PDF:**
   - Texto: `page_count=null`, `pages=[]`, `page=null` y `bbox=null` en todos
     los bloques y observaciones, `images_without_alt=0`.
   - PDF: `page` empieza en 1; `alt_text` es `null`; `width`/`height` y `bbox`
     en puntos PDF; `pages` trae el tamaño de cada página.
7. **IA:** `ai_notice` es `null` solo con `ai_status="skipped"`. El aviso real
   nombra al proveedor configurado.
8. **Errores:** siempre `{code, message}`; los `code` de aplicación van en
   `snake_case`.
9. **Estados:** una sesión recién creada es `uploaded`; no saltar a
   `analyzed` sin pasar por `extracted` en el flujo simulado.
10. **No inventar campos:** `readabilityPercentage`, `barriers` o cualquier
    nombre en español no existen en el backend.

### Migración de los tipos actuales del frontend

| Tipo actual (`frontend/src/types`)                   | Contrato nuevo                                     |
| ---------------------------------------------------- | -------------------------------------------------- |
| `DiagnosticResult.documentId`                        | `Diagnosis.session_id`                             |
| `DiagnosticResult.globalScore`                       | `Diagnosis.score`                                  |
| `DiagnosticResult.readabilityPercentage`             | **No existe** en el backend.                       |
| `DiagnosticResult.barriers[]`                        | `Diagnosis.observations[]`                         |
| `Barrier.id`                                         | `Observation.id`                                   |
| `Barrier.type`                                       | `Observation.title`                                |
| `Barrier.severity` (`Alta`/`Media`/`Baja`)           | `Observation.severity` (`high`/`medium`/`low`)     |
| `Barrier.detectedFragment`                           | `Observation.excerpt`                              |
| `Barrier.suggestion`                                 | `Observation.recommendation`                       |
| `Barrier.status` (`Pendiente`/`Aplicada`/`Ignorada`) | Estado local del frontend; el backend no lo envía. |

## 10. Tipos desde OpenAPI

Con el backend levantado:

```bash
# Desde la raíz del repositorio
npx openapi-typescript http://127.0.0.1:8000/openapi.json \
  -o frontend/src/types/api.d.ts
```

- No requiere agregar nada al backend.
- Si se prefiere fijar la versión, instalar `openapi-typescript` como
  `devDependency` en `frontend/`.
- Los tipos se generan desde `/openapi.json`, así que reflejan los schemas de
  Pydantic. Los ejemplos de este documento no se incluyen en ese archivo.
- Si el backend corre en otro puerto u host, cambiar la URL.

Verificación rápida de que `/openapi.json` está completo:

```bash
curl -s http://127.0.0.1:8000/openapi.json | jq '.paths | keys'
```

Debe listar las 9 rutas de negocio más `/` y `/health`.

## 11. Cambios de contrato

- Cualquier cambio de nombre de campo, tipo, valor de enum o ruta se avisa al
  frontend en la issue o el PR correspondiente.
- Este documento y `/openapi.json` se actualizan en el mismo cambio.
- Los cambios incompatibles no se hacen sin coordinación previa.
- `AdaptationType` y `Adaptation` ya forman parte del contrato (BE-13) y
  aparecen en `/openapi.json`.
- **BE-15:** se agrega `POST /api/v1/sessions/{session_id}/export` (respuesta
  PDF), los modelos `ExportRequest` y `ExportEdit`, y el campo aditivo
  `ContentBlock.font_size` (`number | null`). No cambia ninguna ruta ni campo
  existente.
