# Plan de medición de Lumi

**Estado:** borrador para discutir con el equipo · **Fecha:** 25/11/2026 · **Área:** Data

## 1. Objetivo

Saber si Lumi **se usa**, si **detecta bien** las barreras de accesibilidad y si
las **propuestas de la IA le sirven** a quien adapta el material.

## 2. Situación actual

Hoy no hay datos históricos para medir:

| Dato                              | Dónde vive hoy                          | Cuándo se pierde      |
| --------------------------------- | --------------------------------------- | --------------------- |
| Sesiones, contenido y diagnóstico | Memoria del backend                     | Al reiniciar          |
| Propuestas de adaptación          | No se guardan                           | Al responder          |
| Aplicar o descartar               | Memoria del navegador                   | Al recargar la página |
| Exportaciones                     | No se registran                         | —                     |
| Usuarios                          | No hay autenticación (usuario ficticio) | —                     |

Para medir uso real hay que persistir datos: ver
[modelo de datos](02-modelo-de-datos.md).

## 3. Preguntas que queremos responder

1. ¿Cuántos materiales se analizan y cuántos llegan a exportarse?
2. ¿En qué paso se abandona o falla el proceso?
3. ¿Qué barreras aparecen más?
4. ¿Qué detecciones rechazan los usuarios, por regla y por origen?
5. ¿Se aceptan las propuestas de la IA? ¿Tal cual o editadas?
6. ¿La IA responde a tiempo y dentro de los límites del proveedor?

## 4. Métricas

La prioridad **P1** es lo mínimo para el primer tablero.

### 4.1 Uso

| Métrica                | Cálculo                                                              | Prioridad |
| ---------------------- | -------------------------------------------------------------------- | --------- |
| Documentos analizados  | Documentos con al menos un análisis, por semana                      | P1        |
| Embudo                 | Subido → analizado → con propuesta → con cambio aplicado → exportado | P1        |
| Tasa de error de carga | Cargas o extracciones fallidas / intentos, por código de error       | P1        |
| Perfil del material    | Distribución de páginas, palabras, imágenes y origen (PDF/texto)     | P2        |
| Usuarios que vuelven   | Usuarios con documentos en 2 o más semanas / usuarios activos        | P2        |

### 4.2 Aceptación de las propuestas

Una propuesta es **mostrada** cuando la app devuelve un texto adaptado.

| Métrica               | Cálculo                                                      | Prioridad |
| --------------------- | ------------------------------------------------------------ | --------- |
| Tasa de aceptación    | Propuestas aplicadas (tal cual o editadas) / mostradas       | P1        |
| Aceptación sin editar | Aplicadas tal cual / mostradas                               | P1        |
| Tasa de edición       | Aplicadas con edición / aplicadas                            | P1        |
| Tasa de descarte      | Propuestas descartadas / mostradas                           | P1        |
| Tasa de reversión     | Aplicadas y después deshechas / aplicadas                    | P2        |
| Barreras resueltas    | Observaciones aplicadas / observaciones detectadas           | P1        |
| Observación rechazada | Descartes **sin** pedir propuesta / observaciones, por regla | P2        |

Todas se abren por regla, tipo de adaptación, origen (IA o fallback local),
proveedor y modelo.

Cada decisión se cuenta según su **último estado**: una propuesta aplicada y
luego deshecha no cuenta como aceptada.

### 4.3 Calidad de la detección

**Queda para más adelante:** medir precisión y cobertura requiere un set de
materiales etiquetados a mano, que hoy no existe.

Mientras tanto, la métrica **observación rechazada** (sección 4.2) sirve como
señal indirecta: una regla que se descarta seguido puede estar detectando mal.
No indica qué barreras se están pasando por alto.

### 4.4 Funcionamiento de la IA

| Métrica                | Cálculo                                              | Prioridad |
| ---------------------- | ---------------------------------------------------- | --------- |
| Disponibilidad         | Llamadas con respuesta válida / llamadas             | P1        |
| Errores por tipo       | Límite (429), tiempo de espera, JSON inválido, otros | P1        |
| Latencia               | Percentiles 50 y 95, por tarea y modelo              | P1        |
| Llamadas por documento | Llamadas / documentos analizados                     | P1        |
| Uso de fallback local  | Propuestas locales / propuestas mostradas            | P2        |
| Material truncado      | Análisis que superan 12.000 caracteres / análisis    | P2        |
| Tokens por documento   | Tokens de entrada y salida / documentos              | P2        |
| Rechazo por controles  | Propuestas que no pasan un control / generadas       | P2        |
| Aciertos de caché      | Resueltos con caché / consultas a la caché           | P2        |

Los controles se describen en [calidad y pruebas](05-calidad-y-pruebas.md) y la
caché en [economía de la IA](04-economia-ia.md). Ninguno de los dos existe todavía
en esa forma.

## 5. Cuidados al interpretar

- El **puntaje** (0 a 100) es orientativo y su ponderación está sin calibrar. No
  usarlo como medida de éxito.
- La app **no vuelve a analizar** el material adaptado, así que hoy no existe un
  puntaje "después".
- El porcentaje de legibilidad del frontend (`readabilityPercentage`) no mide
  legibilidad: recalcula las penalizaciones sin el tope por regla.
- Aceptar una propuesta no prueba que mejore la accesibilidad. Conviene revisar
  una muestra con el área de Accesibilidad.
- No fijar metas hasta tener algunas semanas de línea base.

## 6. Etapas propuestas

| Etapa | Entregable                                                          | Depende de        |
| ----- | ------------------------------------------------------------------- | ----------------- |
| 1     | Persistencia mínima: documento, análisis, observación, llamada a IA | Backend           |
| 2     | Registro de propuestas, decisiones y exportaciones                  | Backend, Frontend |
| 3     | Primer tablero con las métricas P1                                  | Data              |

## 7. Decisiones abiertas

- ¿Qué base de datos se usa y dónde se aloja?
- ¿Cómo se identifica a un usuario sin autenticación?
- ¿Por cuánto tiempo se guardan las respuestas de la IA y cómo se informa en los
  términos y condiciones?
- ¿Hace falta guardar el texto original? ¿Para qué?
