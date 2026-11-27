# data/

Espacio de trabajo del área de **Data** de Lumi.

## Propósito

Aportar la mirada de datos e IA al producto: qué medir, qué guardar, cuánto cuesta
la IA y cómo comprobar la calidad de sus respuestas.

**Laboratorio de Data:** Rampa es un prototipo paralelo donde se prueban ideas que
alimentan las propuestas para Lumi.

## Documentos

| #   | Documento                                         | Contenido                                        |
| --- | ------------------------------------------------- | ------------------------------------------------ |
| 00  | [Propuesta](docs/00-propuesta.md)                 | Resumen, prioridades y hoja de ruta. Empezar acá |
| 01  | [Plan de medición](docs/01-plan-de-medicion.md)   | Qué evaluamos y con qué métricas                 |
| 02  | [Modelo de datos](docs/02-modelo-de-datos.md)     | Qué persistir y diagrama entidad-relación        |
| 03  | [Análisis de la IA](docs/03-analisis-ia.md)       | Funcionamiento actual, proveedores y problemas   |
| 04  | [Economía de la IA](docs/04-economia-ia.md)       | Lotes, caché por hash y cupos                    |
| 05  | [Calidad y pruebas](docs/05-calidad-y-pruebas.md) | Controles, rúbrica y protocolo de pruebas        |

## Estructura prevista

```
data/
├── README.md        # este archivo
├── docs/            # documentación de Data
├── evaluation/      # resultados de pruebas y, más adelante, materiales etiquetados
├── scripts/         # scripts de métricas
└── notebooks/       # análisis exploratorios
```

Las subcarpetas se van a crear a medida que se necesiten.

## Cuidados

- **No subir datasets pesados** al repositorio. Los archivos grandes se guardan fuera del repo y acá se documenta dónde están.
- **Privacidad y derechos de autor**: los materiales de docentes pueden tener datos personales o contenido protegido. Solo se suben materiales propios, públicos o con permiso explícito.
- **Notebooks sin outputs pesados**: limpiar las salidas antes de commitear.

## Responsable

Área de Data — Jorge Edison Fernandez - edisonjef@gmail.com
