# Propuesta de Data e IA para Lumi

**Estado:** propuesta para discutir con el equipo · **Fecha:** 25/11/2026 ·
**Autor:** Jorge, área de Data

## 1. Punto de partida

Lumi ya analiza materiales y propone adaptaciones, pero:

- no guarda datos, así que no se puede saber si se usa ni si sirve;
- gasta un pedido a la IA por cada adaptación, con cupos gratuitos limitados;
- no hay una forma acordada de comprobar si las respuestas de la IA son buenas.

## 2. Qué aporta Data

| Mirada            | Pregunta                                  | Documento                                                                            |
| ----------------- | ----------------------------------------- | ------------------------------------------------------------------------------------ |
| Análisis de datos | ¿Qué medimos y qué hay que guardar?       | [Plan de medición](01-plan-de-medicion.md), [modelo de datos](02-modelo-de-datos.md) |
| Consultoría de IA | ¿Cómo funciona la IA y cómo gastar menos? | [Análisis de la IA](03-analisis-ia.md), [economía de la IA](04-economia-ia.md)       |
| Ciencia de datos  | ¿Cómo sabemos si responde bien?           | [Calidad y pruebas](05-calidad-y-pruebas.md)                                         |

**Laboratorio de Data:** Rampa es un prototipo paralelo donde se prueban ideas
antes de proponerlas para Lumi. Los resultados que vienen de ahí están señalados.

## 3. Propuestas

El esfuerzo es una estimación inicial de Data (bajo, medio o alto); la tiene que
validar cada equipo.

| #   | Propuesta                                                        | Beneficio                                                  | Esfuerzo                            | Equipo               | Prioridad |
| --- | ---------------------------------------------------------------- | ---------------------------------------------------------- | ----------------------------------- | -------------------- | --------- |
| 1   | Revisar el modelo de Gemini: el predeterminado está dado de baja | Que la IA responda                                         | Bajo                                | Backend              | Urgente   |
| 2   | Avisar cuando falla la IA y mostrar el aviso de privacidad       | Transparencia                                              | Bajo                                | Frontend             | Alta      |
| 3   | Distinguir "modelo saturado" de "cupo agotado"                   | Reintentar solo cuando conviene                            | Bajo                                | Backend              | Alta      |
| 4   | Persistir documentos, análisis y llamadas a la IA                | Empezar a medir                                            | Alto                                | Backend              | Alta      |
| 5   | Registrar qué se acepta, edita o descarta                        | Saber si las propuestas sirven                             | Medio                               | Backend y Frontend   | Alta      |
| 6   | Controlar cada respuesta de la IA antes de mostrarla             | Menos propuestas defectuosas                               | Medio                               | Backend              | Media     |
| 7   | Pedir adaptaciones por lotes                                     | Más documentos con el mismo cupo                           | Medio                               | Backend y Frontend   | Media     |
| 8   | Reutilizar respuestas de la IA mediante un hash                  | No pagar dos veces por lo mismo                            | Medio                               | Backend              | Media     |
| 9   | Probar modelos con una rúbrica común                             | Elegir con evidencia                                       | Bajo                                | Data y Accesibilidad | Media     |
| 10  | Monitorear los pedidos a la IA con Langfuse                      | Ver consumo, errores y latencia antes de tener base propia | Bajo en OpenRouter, medio en Gemini | Backend y Data       | Alta      |

La propuesta 8 necesita la base de datos de la 4. Antes de activar la 7 hay que
revisar el límite de 30 segundos de OpenRouter. La 10 requiere decidir qué datos
se envían a ese servicio.

## 4. Evidencia disponible

| Afirmación                                    | Respaldo                                                               |
| --------------------------------------------- | ---------------------------------------------------------------------- |
| Problemas actuales de Lumi (1, 2, 3)          | Revisión del código y documentación de Google                          |
| Los lotes reducen pedidos                     | Medido en el laboratorio, no en Lumi                                   |
| Los lotes pueden superar los 30 segundos      | Muestra chica del laboratorio, con Langfuse                            |
| La caché ahorra pedidos                       | Hipótesis: falta medir cuánto material se repite                       |
| Los controles detectan respuestas defectuosas | Casos vistos en el laboratorio; falta medir cuánto mejora el resultado |

## 5. Hoja de ruta

| Etapa | Contenido                                             | Resultado                |
| ----- | ----------------------------------------------------- | ------------------------ |
| 1     | Propuestas 1, 2, 3 y 10                               | IA funcionando y visible |
| 2     | Propuestas 4 y 5                                      | Primeros datos de uso    |
| 3     | Propuestas 6 y 9                                      | Calidad comprobable      |
| 4     | Propuestas 7 y 8                                      | Menor consumo            |
| 5     | Tablero y calibración de umbrales y puntaje con datos | Decisiones con evidencia |

## 6. Qué se necesita del equipo

- Confirmar proveedor, modelo y tipo de cuenta del servidor.
- Elegir base de datos y quién la implementa.
- Incluir en los términos y condiciones que las respuestas de la IA se guardan y
  reutilizan, y definir por cuánto tiempo.
- Una persona de Accesibilidad para revisar respuestas.
