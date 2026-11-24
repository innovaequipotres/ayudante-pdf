export interface User {
  id: string;
  fullName: string;
  role: string;
  initials: string;
}

export interface Folder {
  id: string;
  name: string;
  color: string;
}

export interface LumiDocument {
  id: string;
  name: string;
  subject: string;
  size: string;
  date: string;
  status: "Analizado" | "En edición" | "Procesando" | "Guardado";
  folderId: string | null;
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
  title?: string;
  detail?: string | null;
  whyItMatters?: string;
  recommendation?: string;
  ruleId?: string | null;
  category?: string | null;
  blockId?: string | null;
  originalText?: string;
  adaptationNotes?: string | null;
}

export interface DiagnosticResult {
  documentId: string;
  globalScore: number;
  readabilityPercentage: number;
  barriers: Barrier[];
}
