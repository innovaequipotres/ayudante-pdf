# data/

Espacio de trabajo del área de **Data** de Rampa.

## Propósito

Medir y mejorar la calidad del análisis de accesibilidad que hace la app sobre los materiales educativos. Acá viven:

- **Set de evaluación**: materiales de ejemplo etiquetados a mano con sus problemas de accesibilidad, para comparar contra lo que detecta el escáner.
- **Métricas del escáner**: scripts que calculan qué tan bien detecta la app los problemas (precisión, cobertura, errores frecuentes).
- **Notebooks**: exploración y análisis de resultados.

## Estructura prevista

```
data/
├── README.md        # este archivo
├── evaluation/      # set de evaluación (etiquetas y metadatos, no PDFs pesados)
├── scripts/         # scripts de métricas
└── notebooks/       # análisis exploratorios
```

Las subcarpetas se van a crear a medida que se necesiten.

## Cuidados

- **No subir datasets pesados** al repositorio. Los archivos grandes se guardan fuera del repo y acá se documenta dónde están.
- **Privacidad y derechos de autor**: los materiales de docentes pueden tener datos personales o contenido protegido. Solo se suben materiales propios, públicos o con permiso explícito.
- **Notebooks sin outputs pesados**: limpiar las salidas antes de commitear.

## Responsable

Área de Data — Jorge.
