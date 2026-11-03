export interface User {
  id: string;
  fullName: string;
  role: string;
  initials: string;
}

export interface LumiDocument {
  id: string;
  name: string;
  subject: string;
  size: string;
  date: string;
  status: "Analizado" | "En edición" | "Procesando";
  originalContent: string;
  modifiedContent: string;
}

export interface Barrier {
  id: string;
  type: string;
  severity: "Alta" | "Media" | "Baja";
  detectedFragment: string;
  suggestion: string;
  status: "Pendiente" | "Aplicada" | "Ignorada";
}

export interface DiagnosticResult {
  documentId: string;
  globalScore: number;
  readabilityPercentage: number;
  barriers: Barrier[];
}
