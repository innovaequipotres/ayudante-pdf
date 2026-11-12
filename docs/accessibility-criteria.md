# Criterios de accesibilidad de Ayudante PDF

Documento de referencia de las reglas, umbrales y ponderaciones que usa el
escáner de accesibilidad. Define **qué se evalúa**, **con qué fuente**, **qué
queda para el MVP** y **qué falta validar**.

| Campo        | Valor                                                   |
| ------------ | ------------------------------------------------------- |
| Versión      | 0.1 (borrador para revisión)                            |
| Fecha        | 2026-11-12                                              |
| Rama / issue | `docs/be-10-criteria`                                   |
| Responsable  | Equipo de Backend                                       |
| Revisión     | Equipo de Accesibilidad (pendiente)                     |
| Estado       | Borrador. Las decisiones abiertas están en la sección 9 |

> **Aviso de alcance.** El puntaje es un indicador orientativo. No constituye
> una certificación formal de accesibilidad ni reemplaza una auditoría con
> personas usuarias y tecnologías de asistencia.

---

## 1. Resumen para la reunión

- El escáner tiene **6 reglas automáticas** y **5 reglas semánticas con IA**.
- Solo el umbral de **300 palabras** para `long_paragraph` viene de un
  documento previo del proyecto. El resto de los umbrales son **propuestas del
  equipo** y están marcados como tales.
- La mayoría de las reglas se apoya en WCAG 2.2, pero **WCAG no define
  cantidades de palabras**. Los números son heurísticas nuestras.
- Para PDF, la referencia más precisa es **PDF/UA-1 (ISO 14289-1)**, no WCAG:
  los documentos PDF son "documentos no web" y se encuadran en el capítulo 10
  de **EN 301 549**.
- La ponderación **10 / 4 / 1 con tope de 30 por regla** queda como
  **propuesta a calibrar** con el set de evaluación de `data/`.
- MVP propuesto: las **4 reglas de texto y estructura** más las **2 reglas de
  imagen con salvedades**. Las reglas de IA quedan como análisis complementario
  y no deberían afectar el puntaje del MVP.
- **No tenemos el recursero del proyecto.** Cuando esté disponible hay que
  cargar su enlace y contrastar la columna "Fuente" de cada regla.

---

## 2. Alcance

### 2.1 Qué analiza el escáner

- Materiales educativos cargados como **PDF** o **texto pegado**.
- Contenido textual: párrafos, oraciones, títulos y listas.
- Presencia, tamaño y posición de imágenes.
- Problemas semánticos que detecta la IA de forma opcional.

### 2.2 Qué no analiza (todavía)

- Contraste de color, tipografía, tamaño de fuente o interlineado.
- Orden de lectura real del PDF.
- Tablas, fórmulas, gráficos y multimedia.
- Contenido dentro de las imágenes (por ejemplo, texto incrustado).
- Navegación, foco, teclado ni la interfaz de la aplicación.
- Lectura real con lector de pantalla.

Las categorías `representation`, `multimedia` y `navigation` existen en el
modelo de datos, pero hoy no tienen reglas automáticas. Se informan siempre
para que el cliente muestre el estado completo.

### 2.3 Diferencia entre barrera, revisión y mejora

| Severidad | Etiqueta en la interfaz | Significado                  |
| --------- | ----------------------- | ---------------------------- |
| `high`    | Alta                    | Posible barrera de acceso    |
| `medium`  | Media                   | Aspecto que conviene revisar |
| `low`     | Baja                    | Mejora sugerida              |

Una observación `high` **no implica** que el material incumpla WCAG. Implica que
la heurística encontró un patrón que suele ser una barrera y que una persona
debe revisarlo.

---

## 3. Marco de referencia

| Referencia                         | Uso en este documento                                                                  |
| ---------------------------------- | -------------------------------------------------------------------------------------- |
| **WCAG 2.2** (W3C, 2023)           | Criterios de éxito de referencia. Niveles A, AA y AAA.                                 |
| **PDF/UA-1** (ISO 14289-1:2014)    | Requisitos de accesibilidad para PDF. Fuente principal de las reglas de estructura.    |
| **Matterhorn Protocol 1.1** (2021) | Lista de fallas verificables de PDF/UA. Se usa para validar, no para definir umbrales. |
| **EN 301 549 v3.2.1** (2021)       | Requisitos de accesibilidad TIC. El capítulo 10 cubre documentos no web como PDF.      |
| **ISO 24495-1:2023**               | Principios de lenguaje claro. Referencia cualitativa para legibilidad.                 |
| **UNE 153101:2018 EX**             | Lectura Fácil: pautas para redactar y validar documentos. Referencia cualitativa.      |
| **WCAG-EM 1.0** (2014)             | Metodología de evaluación. Referencia de proceso, no de ponderación.                   |
| **Recursero del proyecto**         | _Pendiente de cargar._ Se completa cuando el equipo lo comparta.                       |

### 3.1 Reglas de interpretación

1. **WCAG es para la web.** Un PDF es un documento no web: para estructura y
   etiquetado, PDF/UA-1 y EN 301 549 son la referencia correcta.
2. **Citar un criterio no equivale a certificar su cumplimiento.** Una regla
   puede inspirarse en un criterio WCAG sin que el hallazgo sea un fallo formal.
3. **Los umbrales numéricos son heurísticas** salvo que se indique una fuente
   explícita.
4. **Los niveles AAA son orientativos.** No se usan como requisito obligatorio
   del MVP.
5. **Toda decisión sin fuente normativa se marca como decisión del equipo.**

### 3.2 Niveles de WCAG citados

| Criterio                     | Nivel | Tema                     |
| ---------------------------- | ----- | ------------------------ |
| 1.1.1 Non-text Content       | A     | Texto alternativo        |
| 1.3.1 Info and Relationships | A     | Estructura y relaciones  |
| 1.4.5 Images of Text         | AA    | Imágenes de texto        |
| 2.4.6 Headings and Labels    | AA    | Títulos y etiquetas      |
| 2.4.10 Section Headings      | AAA   | Títulos de sección       |
| 3.1.3 Unusual Words          | AAA   | Palabras poco frecuentes |
| 3.1.4 Abbreviations          | AAA   | Abreviaturas             |
| 3.1.5 Reading Level          | AAA   | Nivel de lectura         |

---

## 4. Estados de validación

Cada criterio del catálogo tiene uno de estos estados:

| Estado                    | Significado                                                                    |
| ------------------------- | ------------------------------------------------------------------------------ |
| **Validado**              | Tiene una fuente normativa o del proyecto que lo respalda.                     |
| **Decisión del equipo**   | No hay norma aplicable; se adoptó un criterio propio para poder avanzar.       |
| **Propuesta a calibrar**  | Es un valor inicial que se va a ajustar con datos y revisión de Accesibilidad. |
| **Pendiente de revisión** | Requiere validación explícita del equipo de Accesibilidad.                     |

---

## 5. Catálogo de reglas automáticas

### 5.1 Resumen

| Código              | Categoría     | Qué detecta                        | Umbral actual                    | Severidad    | MVP              |
| ------------------- | ------------- | ---------------------------------- | -------------------------------- | ------------ | ---------------- |
| `long_paragraph`    | comprehension | Párrafos extensos                  | más de 150 palabras / más de 300 | media / alta | Sí               |
| `long_sentence`     | comprehension | Oraciones extensas                 | más de 30 palabras / más de 50   | media / alta | Sí               |
| `no_headings`       | structure     | Material extenso sin títulos       | más de 150 palabras / más de 400 | media / alta | Sí               |
| `heading_skip`      | structure     | Salto de más de un nivel de título | cualquier salto                  | baja         | Sí               |
| `image_without_alt` | visual        | Imágenes sin texto alternativo     | cualquier imagen sin `alt`       | alta         | Sí, con salvedad |
| `image_only_page`   | visual        | Páginas con imágenes y poco texto  | 15 palabras o menos en la página | media        | Sí, con salvedad |

Los valores viven en constantes al inicio de `backend/app/scanner/rules.py`.
Cambiar un umbral exige actualizar este documento, el test correspondiente y el
registro de cambios.

### 5.2 `long_paragraph` — Párrafo muy extenso

| Campo       | Valor                                                                                                |
| ----------- | ---------------------------------------------------------------------------------------------------- |
| Categoría   | `comprehension`                                                                                      |
| Detecta     | Un párrafo supera el umbral de palabras                                                              |
| Umbral      | más de 150 palabras → media; más de 300 → alta                                                       |
| Fuente      | 300 palabras: documento previo del proyecto. 150 palabras: decisión del equipo                       |
| Referencias | WCAG 2.2 3.1.5 Reading Level (AAA), ISO 24495-1:2023, UNE 153101:2018 EX                             |
| Estado      | 300: validado contra documento del proyecto (a confirmar en el recursero). 150: propuesta a calibrar |
| MVP         | Sí                                                                                                   |

**Por qué importa.** Los bloques de texto largos cansan y dificultan seguir la
idea, sobre todo a quienes tienen dificultades de lectura o atención.

**Recomendación.** Dividir el párrafo en bloques más cortos, con una idea en
cada uno.

**Limitaciones.**

- Cuenta palabras separadas por espacios; no distingue párrafos visualmente
  cortos pero densos.
- El umbral de 300 aparece en el documento previo del proyecto, pero ese
  documento todavía no está cargado en el repositorio.
- WCAG 3.1.5 no fija cantidades de palabras: es una referencia cualitativa.

### 5.3 `long_sentence` — Oraciones muy largas

| Campo       | Valor                                        |
| ----------- | -------------------------------------------- |
| Categoría   | `comprehension`                              |
| Detecta     | Una oración supera el umbral de palabras     |
| Umbral      | más de 30 palabras → media; más de 50 → alta |
| Fuente      | Decisión del equipo                          |
| Referencias | WCAG 2.2 3.1.5 (AAA), UNE 153101:2018 EX     |
| Estado      | Propuesta a calibrar                         |
| MVP         | Sí                                           |

**Por qué importa.** Las oraciones extensas obligan a retener muchas ideas a la
vez y se entienden con más esfuerzo.

**Recomendación.** Reescribir con oraciones más breves, de una idea cada una.

**Limitaciones.**

- La división en oraciones es una heurística: protege abreviaturas y decimales
  frecuentes, pero puede fallar con usos poco habituales de los signos.
- No mide la complejidad sintáctica, solo la cantidad de palabras.
- La lectura fácil suele recomendar oraciones más cortas que 30 palabras; el
  valor actual es conservador para evitar falsos positivos.

### 5.4 `no_headings` — El material no tiene títulos

| Campo       | Valor                                                         |
| ----------- | ------------------------------------------------------------- |
| Categoría   | `structure`                                                   |
| Detecta     | Material extenso sin ningún título detectado                  |
| Umbral      | más de 150 palabras → media; más de 400 → alta                |
| Fuente      | Decisión del equipo                                           |
| Referencias | WCAG 2.2 1.3.1 (A), 2.4.6 (AA), 2.4.10 Section Headings (AAA) |
| Estado      | Propuesta a calibrar                                          |
| MVP         | Sí                                                            |

**Por qué importa.** Los títulos permiten ubicarse y saltar entre secciones;
las personas que usan lector de pantalla navegan por ellos.

**Recomendación.** Organizar el contenido en secciones y ponerles títulos.

**Limitaciones.**

- La ausencia de títulos **no es un fallo A/AA**: 2.4.10 es AAA. La regla debe
  presentarse como recomendación de estructura, no como incumplimiento WCAG.
- Si la extracción del PDF no detecta títulos (documentos con formato plano),
  la regla puede dar un falso positivo. Es una limitación del extractor.
- No distingue títulos reales de texto en negrita o con otro tamaño.

### 5.5 `heading_skip` — Salto en la jerarquía de títulos

| Campo       | Valor                                                     |
| ----------- | --------------------------------------------------------- |
| Categoría   | `structure`                                               |
| Detecta     | Un título salta más de un nivel respecto del anterior     |
| Umbral      | cualquier salto (por ejemplo, de nivel 1 a nivel 3)       |
| Fuente      | PDF/UA-1 (ISO 14289-1) 7.4.2, test 1                      |
| Referencias | WCAG 2.2 1.3.1 (A) y 2.4.6 (AA)                           |
| Estado      | Validado para PDF/UA. Severidad baja: decisión del equipo |
| MVP         | Sí                                                        |

**Por qué importa.** Cuando se saltan niveles, la estructura se vuelve confusa
para quien navega con tecnologías de asistencia.

**Recomendación.** Usar los niveles de título en orden, sin saltear ninguno.

**Limitaciones.**

- WCAG no exige explícitamente que los niveles sean consecutivos; PDF/UA-1 sí.
  Por eso la regla es más fuerte en PDF que en texto pegado.
- Solo compara títulos consecutivos: no detecta un documento que empieza en
  nivel 2 sin haber tenido nivel 1.
- No detecta el uso de etiquetas `H` genéricas mezcladas con `H1`–`H6`
  (PDF/UA-1 7.4.4).

### 5.6 `image_without_alt` — Imagen sin descripción

| Campo       | Valor                                                                     |
| ----------- | ------------------------------------------------------------------------- |
| Categoría   | `visual`                                                                  |
| Detecta     | Una imagen no tiene texto alternativo                                     |
| Umbral      | cualquier imagen sin `alt`                                                |
| Fuente      | WCAG 2.2 1.1.1 Non-text Content (A) y PDF/UA-1 7.3, test 1                |
| Referencias | Matterhorn Protocol 1.1 (verificación de PDF/UA)                          |
| Estado      | Fuente normativa validada. Severidad alta y tratamiento en PDF: a validar |
| MVP         | Sí, con salvedad                                                          |

**Por qué importa.** La información visual puede no estar disponible para
quienes usan lectores de pantalla.

**Recomendación.** Incorporar un texto alternativo que describa la información
relevante de la imagen.

**Limitaciones y falsos positivos.**

- `pdfplumber` no expone el texto alternativo del PDF. El procesador deja
  `alt_text` en `None`, así que **toda imagen de un PDF se marca**, aunque el
  archivo original sí tenga descripción.
- La observación incluye una aclaración, pero el puntaje se ve afectado igual.
- No analiza si el texto alternativo es adecuado, solo si existe.
- **Propuesta:** para PDF, bajar la severidad a `medium` ("revisar") hasta
  contar con un extractor que lea el `Alt` real; para texto pegado, mantener
  `high`. Queda pendiente de aprobación.

### 5.7 `image_only_page` — Página con poco texto y con imágenes

| Campo       | Valor                                          |
| ----------- | ---------------------------------------------- |
| Categoría   | `visual`                                       |
| Detecta     | Una página tiene imágenes y muy poco texto     |
| Umbral      | 15 palabras o menos en la página               |
| Fuente      | Decisión del equipo                            |
| Referencias | WCAG 2.2 1.1.1 (A) y 1.4.5 Images of Text (AA) |
| Estado      | Propuesta a calibrar                           |
| MVP         | Sí, con salvedad                               |

**Por qué importa.** Si la información está solo en imágenes, no llega a
quienes no pueden verlas.

**Recomendación.** Revisar que el contenido de las imágenes también esté
explicado con texto.

**Limitaciones.**

- No es un criterio WCAG: es una heurística para detectar información que
  podría estar solo en imágenes.
- No sabe si la imagen aporta información o es decorativa.
- El umbral de 15 palabras es configurable por parámetro, pero el valor por
  defecto es el que usa el diagnóstico.

### 5.8 Reglas semánticas con IA

La IA complementa las reglas automáticas con observaciones que no se pueden
comprobar con heurísticas. Su catálogo está en
`backend/app/scanner/ai_analysis.py`.

| Código                  | Categoría      | Qué detecta                                        | Fuente              |
| ----------------------- | -------------- | -------------------------------------------------- | ------------------- |
| `ambiguous_instruction` | comprehension  | Consigna o pregunta con más de una interpretación  | Decisión del equipo |
| `undefined_term`        | representation | Término técnico usado sin definir                  | Decisión del equipo |
| `dense_section`         | comprehension  | Sección con sobrecarga de información              | Decisión del equipo |
| `visual_reference`      | visual         | Referencia a una imagen sin describir su contenido | Decisión del equipo |
| `unclear_sequence`      | structure      | Secuencia de pasos sin orden explícito             | Decisión del equipo |

**Referencias relacionadas:** WCAG 2.2 3.1.3 (AAA), 3.1.4 (AAA), 3.1.5 (AAA),
1.1.1 (A), 1.3.1 (A) y 2.4.6 (AA). Ninguna de estas reglas es un criterio WCAG
formal: son interpretaciones del equipo sobre problemas semánticos frecuentes.

**Reglas de funcionamiento:**

- La severidad es siempre `medium`; el modelo no puede cambiarla.
- La IA solo puede reportar códigos del catálogo cerrado.
- Se descartan bloques inexistentes y hallazgos duplicados.
- Si la IA falla, el diagnóstico por reglas sigue disponible.
- El texto se recorta a 12.000 caracteres y se informa `ai_truncated`.
- **Hoy estas observaciones cuentan en el puntaje igual que las reglas.** Para
  el MVP se propone mostrarlas como análisis complementario y **no incluirlas
  en la ponderación** hasta validarlas.

---

## 6. Puntaje y ponderación

### 6.1 Fórmula

```text
puntaje = max(0, 100 - Σ min(penalización_por_regla, 30))
```

- Cada observación resta según su severidad.
- Las penalizaciones se agrupan por `rule_id`.
- Cada regla resta como máximo 30 puntos.
- Un material sin observaciones obtiene 100.
- El puntaje mínimo es 0.

### 6.2 Penalizaciones

| Severidad | Nivel     | Penalización | Racional propuesto                               |
| --------- | --------- | ------------ | ------------------------------------------------ |
| `high`    | `barrier` | 10 puntos    | Una barrera concreta pesa más que varias mejoras |
| `medium`  | `review`  | 4 puntos     | Un aspecto dudoso no debería hundir el resultado |
| `low`     | `review`  | 1 punto      | Una mejora sugerida es casi informativa          |

**Ejemplo.** Un material con 2 barreras de reglas distintas y 1 observación
para revisar obtiene `100 - (10 + 10 + 4) = 76`.

**Ejemplo con tope.** Una regla con 5 barreras restaría 50, pero el tope la
limita a 30. El puntaje nunca depende de una sola regla repetida.

### 6.3 Niveles del diagnóstico

| Nivel     | Condición                                 |
| --------- | ----------------------------------------- |
| `ok`      | No hay observaciones                      |
| `review`  | Hay observaciones, pero ninguna es `high` |
| `barrier` | Al menos una observación es `high`        |

El nivel y el puntaje son independientes: un material puede tener 96 puntos y
nivel `review` si solo tiene una observación media. Esto es intencional: el
nivel indica la presencia de una barrera, no el promedio.

### 6.4 Estado de la ponderación

**Propuesta a calibrar.** No existe una norma que defina un puntaje de 0 a 100
para accesibilidad. Los valores 10 / 4 / 1 y el tope de 30 son una decisión del
equipo para poder avanzar.

Criterios para calibrar más adelante:

1. Correr el escáner sobre el set de evaluación de `data/` y comparar contra
   las etiquetas manuales.
2. Revisar si una barrera aislada debe llevar el puntaje por debajo de 90.
3. Revisar si el tope de 30 por regla esconde problemas sistémicos.
4. Decidir si las observaciones de IA deben ponderar o solo informarse.
5. Documentar cualquier cambio en este archivo y en `scoring.py`.

Mientras no se calibre, el diagnóstico mantiene el aviso
`SCORE_DISCLAIMER`: el puntaje es orientativo y no certifica accesibilidad.

---

## 7. Decisión de MVP

### 7.1 Reglas incluidas

| Regla               | MVP              | Motivo                                                          |
| ------------------- | ---------------- | --------------------------------------------------------------- |
| `long_paragraph`    | Sí               | Regla principal de legibilidad y la única con umbral previo     |
| `long_sentence`     | Sí               | Complementa la anterior y es fácil de explicar al usuario       |
| `no_headings`       | Sí               | Aporta estructura y navegación; requiere aclarar que no es A/AA |
| `heading_skip`      | Sí               | Tiene respaldo directo en PDF/UA-1                              |
| `image_without_alt` | Sí, con salvedad | Es una barrera importante, pero en PDF hoy da falsos positivos  |
| `image_only_page`   | Sí, con salvedad | Ayuda a detectar información solo visual; es heurística         |

### 7.2 Reglas fuera del MVP

| Regla / grupo    | Decisión                                                                 |
| ---------------- | ------------------------------------------------------------------------ |
| Reglas de IA     | Análisis complementario. No deberían afectar el puntaje hasta validarlas |
| `representation` | Sin reglas automáticas por ahora                                         |
| `multimedia`     | Sin reglas automáticas por ahora                                         |
| `navigation`     | Sin reglas automáticas por ahora                                         |

### 7.3 Salvedades del MVP

1. **Alt en PDF.** Mientras `pdfplumber` no lea el `Alt`, `image_without_alt`
   debe mostrar una advertencia visible y, preferentemente, severidad media
   para PDF.
2. **Títulos en PDF.** Si el extractor no detecta títulos, `no_headings` puede
   dar falsos positivos. La interfaz debe invitar a revisar el material.
3. **Puntaje.** El MVP debe mostrar el aviso de que el puntaje es orientativo.
4. **IA.** Si se activa, debe quedar claro que es un análisis adicional y que
   puede fallar sin afectar el diagnóstico por reglas.

---

## 8. Limitaciones conocidas

- **Extracción de PDF.** `pdfplumber` no expone texto alternativo ni siempre
  detecta la jerarquía real de títulos.
- **Conteo de palabras.** Se cuenta por espacios; no se normalizan contracciones,
  guiones ni palabras compuestas.
- **División de oraciones.** Es una heurística con abreviaturas y decimales
  protegidos; puede fallar en casos poco frecuentes.
- **Imágenes.** Solo se analiza presencia, tamaño y posición. No se analiza
  contraste, contenido ni si la imagen es decorativa.
- **Puntaje.** No mide conformidad WCAG ni reemplaza una auditoría.
- **IA.** Puede alucinar, se recorta a 12.000 caracteres y no debe usarse con
  datos personales de estudiantes.
- **Texto pegado.** No tiene páginas, así que las reglas que dependen de la
  página no se aplican.

---

## 9. Decisiones abiertas

| ID   | Decisión                                        | Propuesta                               | Responsable            | Estado    |
| ---- | ----------------------------------------------- | --------------------------------------- | ---------------------- | --------- |
| D-01 | Cargar el recursero del proyecto                | Agregar enlace y contrastar cada fuente | Equipo                 | Pendiente |
| D-02 | Validar umbrales de `long_paragraph`            | 300 validado; 150 a calibrar            | Accesibilidad          | Pendiente |
| D-03 | Validar umbrales de `long_sentence`             | 30 / 50, conservadores                  | Accesibilidad          | Pendiente |
| D-04 | Validar umbrales de `no_headings`               | 150 / 400                               | Accesibilidad          | Pendiente |
| D-05 | Validar umbral de `image_only_page`             | 15 palabras                             | Accesibilidad          | Pendiente |
| D-06 | Aprobar ponderación 10 / 4 / 1 y tope 30        | Mantener como propuesta inicial         | Equipo + Accesibilidad | Pendiente |
| D-07 | Definir si la IA pondera en el MVP              | No ponderar; mostrar como complemento   | Equipo                 | Pendiente |
| D-08 | Definir severidad de `image_without_alt` en PDF | `medium` para PDF, `high` para texto    | Accesibilidad          | Pendiente |
| D-09 | Definir encuadre normativo del producto         | WCAG 2.2 + PDF/UA-1 + EN 301 549        | Equipo                 | Pendiente |
| D-10 | Firmar la validación de criterios               | Completar tabla de la sección 10        | Accesibilidad          | Pendiente |

---

## 10. Registro de validación

| Rol                     | Nombre | Fecha | Estado    |
| ----------------------- | ------ | ----- | --------- |
| Equipo de Backend       |        |       | Borrador  |
| Equipo de Accesibilidad |        |       | Pendiente |
| Producto / Docencia     |        |       | Pendiente |

---

## 11. Registro de cambios

| Versión | Fecha      | Cambio                                                              |
| ------- | ---------- | ------------------------------------------------------------------- |
| 0.1     | 2026-11-12 | Borrador inicial con catálogo, fuentes, MVP y ponderación propuesta |

---

## Anexo A. Trazabilidad regla ↔ criterio

| Regla               | WCAG 2.2                             | PDF/UA-1 / ISO 14289-1 | Otra referencia         |
| ------------------- | ------------------------------------ | ---------------------- | ----------------------- |
| `long_paragraph`    | 3.1.5 Reading Level (AAA)            | —                      | ISO 24495-1, UNE 153101 |
| `long_sentence`     | 3.1.5 Reading Level (AAA)            | —                      | ISO 24495-1, UNE 153101 |
| `no_headings`       | 1.3.1 (A), 2.4.6 (AA), 2.4.10 (AAA)  | 7.4 (títulos)          | —                       |
| `heading_skip`      | 1.3.1 (A), 2.4.6 (AA)                | 7.4.2, test 1          | Matterhorn Protocol 1.1 |
| `image_without_alt` | 1.1.1 Non-text Content (A)           | 7.3, test 1            | Matterhorn Protocol 1.1 |
| `image_only_page`   | 1.1.1 (A), 1.4.5 Images of Text (AA) | —                      | —                       |

## Anexo B. Glosario

| Término           | Definición                                                                |
| ----------------- | ------------------------------------------------------------------------- |
| **Barrera**       | Observación de severidad alta. Puede impedir o dificultar el acceso.      |
| **Heurística**    | Regla práctica que aproxima un problema; no es una norma ni una garantía. |
| **Lectura Fácil** | Método de redacción y validación para facilitar la comprensión.           |
| **PDF/UA**        | Estándar de accesibilidad para PDF (ISO 14289).                           |
| **Puntaje**       | Indicador orientativo de 0 a 100; no es una certificación.                |
| **SC**            | _Success Criterion_ (criterio de éxito) de WCAG.                          |
| **WCAG**          | _Web Content Accessibility Guidelines_, del W3C.                          |

## Anexo C. Cómo cambiar un criterio

1. Abrir un issue con la regla, el umbral actual y la fuente propuesta.
2. Validar con el equipo de Accesibilidad.
3. Actualizar la constante en `backend/app/scanner/rules.py` o
   `backend/app/scanner/scoring.py`.
4. Actualizar la ficha de este documento y su registro de cambios.
5. Actualizar o agregar el test que fija el umbral.
6. Ejecutar `pytest` y revisar el impacto en el set de evaluación de `data/`.
