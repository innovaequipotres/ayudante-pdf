# La IA en Lumi: cómo funciona y qué revisar

**Fecha:** 25/11/2026 · **Área:** Data
**Fuente:** código de `develop` (commit `8065359`) y documentación de los
proveedores. No se ejecutó la app ni se revisó la configuración del servidor.

## 1. Resumen

- El proveedor se elige con `AI_PROVIDER`: **Gemini** (por defecto) u
  **OpenRouter**. No hay cambio automático de uno a otro si el primero falla.
- El modelo de Gemini por defecto, `gemini-2.0-flash`, **fue dado de baja el
  1 de junio de 2026**. Si el servidor no define otro en `GEMINI_MODEL`, la IA no
  responde.

## 2. Dónde se usa

| Uso         | Qué hace                                    | Llamadas                                              | Si falla                                                            |
| ----------- | ------------------------------------------- | ----------------------------------------------------- | ------------------------------------------------------------------- |
| Diagnóstico | Busca 5 problemas de redacción y estructura | 1 por análisis; se reutiliza si salió bien            | Quedan solo las reglas automáticas                                  |
| Adaptación  | Reescribe una barrera, a pedido             | 1 o 2 por pedido (reintenta si la salida es inválida) | División local en párrafos (solo `simplify`) o recomendación manual |

Con OpenRouter, si el modelo rechaza el formato pedido (error 400), cada llamada
se repite una vez en otro formato.

Código: [ai_provider.py](../../backend/app/services/ai_provider.py),
[ai_analysis.py](../../backend/app/scanner/ai_analysis.py) y
[adaptation.py](../../backend/app/scanner/adaptation.py).

### Reglas de IA

`ambiguous_instruction`, `undefined_term`, `dense_section`, `visual_reference`,
`unclear_sequence`. La severidad siempre es `medium`. El backend descarta reglas
o bloques inexistentes y duplicados.

### Límites

| Límite                         | Valor                        |
| ------------------------------ | ---------------------------- |
| Texto analizado en diagnóstico | 12.000 caracteres            |
| Texto por adaptación           | 8.000 caracteres             |
| Tiempo de espera en OpenRouter | 30 segundos (configurable)   |
| Tiempo de espera en Gemini     | No se configura en el código |

## 3. Configuración

| Variable           | Valor por defecto                        |
| ------------------ | ---------------------------------------- |
| `AI_PROVIDER`      | `gemini`                                 |
| `GEMINI_MODEL`     | `gemini-2.0-flash`                       |
| `OPENROUTER_MODEL` | Vacío (obligatorio si se usa OpenRouter) |

## 4. Proveedores: condiciones consultadas el 25/11/2026

### Gemini

- Baja de `gemini-2.0-flash`: 1/6/2026. Reemplazo recomendado:
  `gemini-3.6-flash` ([bajas de modelos](https://ai.google.dev/gemini-api/docs/deprecations)).
- Con capa gratuita, entre otros: `gemini-3.8-flash`, `gemini-3.6-flash` y
  `gemini-3.5-flash-lite` ([precios](https://ai.google.dev/gemini-api/docs/pricing)).
  `gemini-2.5-flash` se da de baja el 1/12/2026.
- En el servicio gratuito, Google usa lo enviado y las respuestas para mejorar sus
  productos, puede haber revisión humana y pide no enviar información sensible ni
  personal ([términos](https://ai.google.dev/gemini-api/terms), vigentes desde el
  23/3/2026).

### OpenRouter

- Los modelos `:free` tienen un máximo de 20 pedidos por minuto y 50 por día; con
  al menos 10 USD comprados, 1.000 por día. Cifras tomadas de resultados de
  búsqueda: confirmar en [límites](https://openrouter.ai/docs/api/reference/limits).
- La política de datos depende del modelo elegido.

Con un diagnóstico y 10 adaptaciones, un documento usa al menos 11 llamadas: unos
4 documentos por día con el límite de 50.

## 5. Problemas encontrados

| #   | Problema                                                                                                                        | Impacto                                                                   | Propuesta                                                          | Prioridad |
| --- | ------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------- | ------------------------------------------------------------------ | --------- |
| 1   | Modelo por defecto dado de baja ([config.py](../../backend/app/core/config.py))                                                 | La IA puede estar sin funcionar                                           | Revisar `GEMINI_MODEL` del servidor y cambiar el valor por defecto | Alta      |
| 2   | El frontend no usa `ai_status` ni `ai_notice`                                                                                   | No avisa si falló la IA del diagnóstico ni muestra el aviso de privacidad | Mostrar ambos                                                      | Alta      |
| 3   | El aviso de Gemini no menciona el uso de datos de la capa gratuita                                                              | Se puede enviar material con datos personales                             | Ajustar el aviso en [ai.py](../../backend/app/schemas/ai.py)       | Alta      |
| 4   | Las observaciones de IA restan puntaje; los [criterios](../../docs/accessibility-criteria.md) proponen que no (D-07, pendiente) | Puntaje distinto según responda la IA                                     | Decidir en equipo                                                  | Media     |
| 5   | No se registran modelo, latencia, tokens ni tipo de error de forma consultable                                                  | No se puede medir la IA                                                   | Ver [modelo de datos](02-modelo-de-datos.md)                       | Media     |
| 6   | Un error 429 termina en "no disponible" sin distinguirse                                                                        | No se detecta que se agotó el cupo                                        | Registrar el tipo de error                                         | Media     |

## 6. Comparación con el laboratorio de Data

Rampa es el prototipo paralelo del área de Data. Allí las barreras se detectan
solo con reglas y la IA se usa para las propuestas.

| Tema                      | Laboratorio (Rampa)                     | Lumi                                       |
| ------------------------- | --------------------------------------- | ------------------------------------------ |
| Consumo                   | Por lotes en la capa gratuita           | Un pedido por adaptación                   |
| Si falla un modelo        | Prueba otro de una lista de hasta 3     | Un solo modelo                             |
| Proveedor pago            | Solo con autorización del usuario       | Depende de la clave configurada            |
| Error 429                 | Distingue saturación de cupo agotado    | No distingue                               |
| Imágenes                  | La IA recibe la imagen                  | La descripción se basa en el texto cercano |
| Control de las propuestas | Las vuelve a medir contra los criterios | Controla formato y largo                   |
| Decisiones del docente    | Se guardan, con versiones               | Quedan en el navegador                     |

El detalle está en [economía de la IA](04-economia-ia.md) y
[calidad y pruebas](05-calidad-y-pruebas.md).

## 7. Cómo probar la IA de Lumi

Para comprobar que responde, correr
[try_ai_analysis.py](../../backend/scripts/try_ai_analysis.py) sobre un material
propio o público. Para comparar modelos, usar el
[protocolo de pruebas](05-calidad-y-pruebas.md).

## 8. Pendiente de confirmar

- [ ] Proveedor y modelo configurados en el servidor.
