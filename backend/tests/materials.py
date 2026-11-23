"""Textos de prueba con y sin problemas de accesibilidad pedagógica."""

from __future__ import annotations

CLEAN_TEXT = (
    "# La célula\n"
    "\n"
    "La célula es la unidad básica de la vida. "
    "Tiene membrana, citoplasma y material genético.\n"
    "\n"
    "## Partes de la célula\n"
    "\n"
    "- Membrana\n"
    "- Citoplasma\n"
    "- Núcleo\n"
    "\n"
    "Cada parte cumple una función importante. "
    "Repasar la lista ayuda a recordar el vocabulario."
)

# Sin títulos y con un párrafo y una oración demasiado extensos. Incluye una
# consigna con varias acciones para que también sirva de material del análisis
# semántico simulado.
PROBLEM_TEXT = (
    "La célula realiza funciones vitales que conviene estudiar con atención y "
    "sin apuro porque cada parte del material repite ideas importantes para "
    "comprender el tema y responder las preguntas que aparecen al final del "
    "texto y que muchas veces piden explicar comparar justificar y relacionar "
    "conceptos que no fueron definidos antes de la actividad y que además "
    "suponen que el estudiante ya conoce vocabulario técnico que nunca se "
    "explica en el documento y que tampoco aparece en un glosario ni en una "
    "nota al pie que permita aclarar dudas mientras se estudia el material. "
    "El texto continúa con más información sobre la membrana el citoplasma el "
    "núcleo y los organelos. La membrana regula el intercambio de sustancias. "
    "El citoplasma contiene los organelos. El núcleo guarda el material "
    "genético. Los organelos cumplen funciones específicas. El material no "
    "tiene títulos que ayuden a ubicar cada tema. Tampoco separa las ideas en "
    "párrafos breves. Conviene leerlo varias veces para encontrar la idea "
    "principal. Las listas de pasos no indican un orden claro. Las consignas "
    "mezclan varias acciones en una sola oración. El vocabulario técnico "
    "aparece sin una explicación cercana. La información se acumula sin "
    "pausas ni apoyos visuales. El estudiante debe inferir qué se espera de "
    "cada actividad. El documento no ofrece ejemplos ni contraejemplos. "
    "Tampoco incluye un resumen al final. La extensión dificulta recordar "
    "dónde estaba cada concepto. Conviene reorganizar el contenido antes de "
    "usarlo en clase."
)
