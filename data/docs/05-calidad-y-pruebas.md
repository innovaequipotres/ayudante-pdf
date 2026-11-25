# Calidad de las respuestas de la IA y pruebas

**Estado:** propuesta · **Fecha:** 25/11/2026 · **Área:** Data

## 1. Tres capas

| Capa                  | Cuándo                           | Quién                | Responde              |
| --------------------- | -------------------------------- | -------------------- | --------------------- |
| Controles automáticos | Antes de mostrar cada respuesta  | El sistema           | ¿Se puede mostrar?    |
| Pruebas con revisión  | Antes de cambiar modelo o prompt | Data y Accesibilidad | ¿Qué opción es mejor? |
| Aceptación en uso     | Con usuarios                     | Data                 | ¿Le sirve al docente? |

## 2. Controles automáticos

### 2.1 Lo que Lumi ya controla

| Tarea       | Control                                                                                                                     |
| ----------- | --------------------------------------------------------------------------------------------------------------------------- |
| Diagnóstico | JSON válido, regla del catálogo, bloque existente, sin duplicados                                                           |
| Adaptación  | JSON válido, texto no vacío, sin HTML, largo máximo, distinto del original; descripción alternativa de hasta 250 caracteres |

### 2.2 Lo que proponemos agregar

| Control               | Cómo                                                                                               | Si falla                                    |
| --------------------- | -------------------------------------------------------------------------------------------------- | ------------------------------------------- |
| Texto contaminado     | Detectar otros alfabetos, razonamiento en inglés o frases repetidas                                | Pedir de nuevo una vez                      |
| La propuesta resuelve | Volver a aplicar las reglas automáticas: debe mejorar la que originó la barrera y no empeorar otra | Pedir de nuevo; si falla, dejar el original |
| Datos conservados     | Comparar números, fechas y nombres                                                                 | Marcar para revisar                         |
| Términos ausentes     | Listar términos del original que no aparecen                                                       | Marcar para revisar                         |

"Términos ausentes" marca también sinónimos válidos: es un aviso, no un rechazo.
Las reglas automáticas no comprueban el sentido del texto.

### 2.3 Qué se observó en el laboratorio

| Hallazgo (guía de 30 páginas, 21/10/2026)   | Resultado                    |
| ------------------------------------------- | ---------------------------- |
| Explicaciones de imágenes con texto extraño | 11 de 42, con un solo modelo |
| Textos adaptados con texto extraño          | 0 de 103                     |

En Rampa se agregó un filtro que descarta esas respuestas y las vuelve a pedir.
Además, controla las propuestas de texto contra sus criterios y guarda el
historial de versiones.

También se comparó un modelo gratuito por lotes con uno pago de a un pedido: el
75 % y el 98 % de los textos, respectivamente, perdieron algún término. Es solo un
indicio: se midió con un material y cambiaron a la vez el modelo y la forma de
pedir.

## 3. Pruebas antes de tener usuarios

No requiere materiales etiquetados.

### 3.1 Protocolo

1. Elegir 5 materiales propios o públicos, sin datos personales.
2. Fijar una muestra de 30 barreras, de distintas reglas.
3. Generar las propuestas con cada modelo candidato, con el mismo prompt.
4. Registrar pedidos, errores, tiempo y controles superados.
5. Dos personas puntúan sin saber qué modelo respondió.
6. Repetir 3 veces una parte de la muestra para ver cuánto varía.

### 3.2 Rúbrica

| Criterio  | 1                            | 2                    | 3                    |
| --------- | ---------------------------- | -------------------- | -------------------- |
| Fidelidad | Inventa o pierde información | Pierde un matiz      | Conserva todo        |
| Claridad  | Igual o peor que el original | Algo más clara       | Claramente más clara |
| Barrera   | No la resuelve               | La resuelve en parte | La resuelve          |
| Uso       | No sirve                     | Sirve con cambios    | Sirve tal cual       |

### 3.3 Cómo decidir

- Se descarta el modelo que invente información.
- Entre los restantes, comparar el promedio por criterio y por tipo de adaptación.
- A igual calidad, elegir el que consuma menos y responda antes.
- La primera ronda es la línea base; recién después se fijan metas.

Con 30 casos se detectan diferencias grandes, no mejoras pequeñas.

### 3.4 Registro

Una fila por respuesta en un CSV dentro de `data/evaluation/`:

`fecha`, `material`, `bloque`, `regla`, `modelo`, `version_prompt`,
`controles_ok`, `segundos`, `revisor`, `fidelidad`, `claridad`, `barrera`, `uso`,
`comentario`.

## 4. Con usuarios

- Aceptación, edición y descarte por regla, tipo y modelo: ver el
  [plan de medición](01-plan-de-medicion.md).
- Revisar cada mes una muestra de propuestas aceptadas con Accesibilidad: aceptar
  no garantiza que sean correctas.
- Los cambios de modelo o prompt se comparan contra la versión anterior.

## 5. Observabilidad

Guardar de cada pedido: tarea, modelo, versión del prompt, resultado, error,
tiempo y tokens ([modelo de datos](02-modelo-de-datos.md)).

### 5.1 Lo probado en el laboratorio

Se usó **Langfuse** conectado desde OpenRouter con la función _Broadcast_, sin
cambiar código. En las pruebas de octubre de 2026 registró 106 pedidos, con lo
enviado, lo respondido, el proveedor de cada intento, los tokens y la latencia.

| Tarea                    | Pedidos | Latencia p50 | Latencia p95 |
| ------------------------ | ------- | ------------ | ------------ |
| Lote de textos           | 32      | 9,9 s        | 31,0 s       |
| Lote de imágenes         | 13      | 12,7 s       | 43,8 s       |
| Ver propuesta (un texto) | 6       | 7,5 s        | 10,5 s       |

`p50` es el tiempo que no supera la mitad de los pedidos y `p95`, el que no supera
el 95 %. Son muestras chicas, de pruebas de desarrollo: sirven como indicio.

Lecciones:

- Nombrar cada pedido por tarea desde el principio: 45 quedaron sin identificar.
- Mirar qué modelo responde: uno de los modelos configurados no registró tokens en
  ese período, sin causa identificada.
- Hubo pedidos sin respuesta, visibles en el registro.
- El costo figura en cero porque se usaron modelos gratuitos.

### 5.2 Cómo aplicarlo en Lumi

| Proveedor  | Conexión con Langfuse                                                 |
| ---------- | --------------------------------------------------------------------- |
| OpenRouter | _Broadcast_, sin código                                               |
| Gemini     | Instrumentar el backend con `GoogleGenAIInstrumentor` (OpenInference) |

| Función de Langfuse    | Uso propuesto                                 | Estado   |
| ---------------------- | --------------------------------------------- | -------- |
| Tracing y tableros     | Pedidos, tokens, errores y latencia por tarea | Probado  |
| Sessions               | Agrupar el consumo por documento              | A probar |
| Scores                 | Registrar si se aceptó, editó o descartó      | A probar |
| Human annotation       | Puntuar respuestas con la rúbrica             | A probar |
| Datasets y Experiments | Comparar modelos con los mismos casos         | A probar |
| Prompts                | Versionar los prompts                         | A probar |

Langfuse se usaría para **ver y depurar**. Las métricas del producto se guardan en
la base propia (`LLAMADA_IA` en el [modelo de datos](02-modelo-de-datos.md)).

El plan gratuito, consultado el 25/11/2026, incluye 50.000 unidades por mes, 30
días de acceso a los datos, 2 usuarios y no ofrece borrado automático
([precios](https://langfuse.com/pricing)).

Gemini ofrece registros de pedidos en Google AI Studio solo para proyectos pagos
([documentación](https://ai.google.dev/gemini-api/docs/logs-datasets)).

### 5.3 Privacidad

Langfuse es un tercero. Antes de usarlo hay que decidir si recibe el contenido o
solo las métricas, e informarlo. En OpenRouter, el _Privacy Mode_ excluye los
textos enviados y respondidos, pero mantiene el consumo y otros datos del pedido
([documentación](https://openrouter.ai/docs/guides/features/broadcast/langfuse)).
