import type { DiagnosticResult, LumiDocument, User } from "@/types";

export const mockUser: User = {
  id: "usuario-luis-aguilar",
  fullName: "Luis Aguilar",
  role: "Docente",
  initials: "MP",
};

export const mockDocuments: LumiDocument[] = [
  {
    id: "documento-trabajo-practico",
    name: "Trabajo_Practico1.pdf",
    subject: "Matemática",
    size: "2,4 MB",
    date: "28 de octubre de 2026",
    status: "Analizado",
    originalContent:
      "Práctica de funciones\n\nEl alumno deberá resolver los siguientes ejercicios. Para obtener el resultado correcto, deberá reemplazar los valores en la fórmula y realizar las operaciones en el orden indicado.\n\nActividades\n1. Hallar la imagen de la función para x = 2.\n2. Representar la función en un sistema de ejes cartesianos.",
    modifiedContent:
      "# Práctica de funciones\n\nCada estudiante puede resolver los siguientes ejercicios. Para obtener el resultado, reemplazá los valores en la fórmula y realizá las operaciones en el orden indicado.\n\n## Actividades\n1. Hallá la imagen de la función para x = 2.\n2. Representá la función en un sistema de ejes cartesianos.",
  },
  {
    id: "documento-apunte-clase",
    name: "Apunte_Clase.pdf",
    subject: "Matemática",
    size: "1,8 MB",
    date: "25 de octubre de 2026",
    status: "En edición",
    originalContent:
      "Proporcionalidad directa\n\nDos magnitudes son directamente proporcionales cuando al multiplicar una de ellas por un número, la otra queda multiplicada por el mismo número.",
    modifiedContent:
      "Proporcionalidad directa\n\nDos magnitudes son directamente proporcionales cuando al multiplicar una de ellas por un número, la otra queda multiplicada por el mismo número.",
  },
  {
    id: "documento-guia-funciones",
    name: "Guia_Funciones.pdf",
    subject: "Matemática",
    size: "3,1 MB",
    date: "24 de octubre de 2026",
    status: "Procesando",
    originalContent:
      "Introducción a las funciones\n\nUna función relaciona cada elemento de un conjunto con un único elemento de otro conjunto.",
    modifiedContent:
      "Introducción a las funciones\n\nUna función relaciona cada elemento de un conjunto con un único elemento de otro conjunto.",
  },
];

export const mockDiagnostic: DiagnosticResult = {
  documentId: "documento-trabajo-practico",
  globalScore: 78,
  readabilityPercentage: 74,
  barriers: [
    {
      id: "barrera-claridad-consigna",
      type: "Error de claridad en el texto",
      severity: "Alta",
      detectedFragment:
        "Para obtener el resultado correcto, deberá reemplazar los valores en la fórmula y realizar las operaciones en el orden indicado.",
      suggestion:
        "Separá la consigna en pasos breves y usá verbos directos. Por ejemplo: «Reemplazá los valores en la fórmula. Después, resolvé las operaciones en el orden indicado».",
      status: "Pendiente",
    },
    {
      id: "barrera-lenguaje-inclusivo",
      type: "Uso del lenguaje inclusivo",
      severity: "Media",
      detectedFragment: "El alumno deberá resolver los siguientes ejercicios.",
      suggestion:
        "Se sugiere reemplazar términos excluyentes por un lenguaje más inclusivo: «Cada estudiante puede resolver los siguientes ejercicios».",
      status: "Pendiente",
    },
    {
      id: "barrera-jerarquia-titulos",
      type: "Falta de jerarquía en los títulos",
      severity: "Baja",
      detectedFragment: "Práctica de funciones / Actividades",
      suggestion:
        "Organizá los títulos con niveles jerárquicos para distinguir el tema principal de sus secciones.",
      status: "Aplicada",
    },
  ],
};
