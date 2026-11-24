"use client";

import { create } from "zustand";
import {
  mockDiagnostic,
  mockDocuments,
  mockFolders,
  mockUser,
} from "@/mocks/mockData";
import { DEMO_MOCKS } from "@/lib/demoMocks";
import {
  USE_MOCKS,
  mapDiagnosisToResult,
  mapSessionToDocument,
} from "@/services";
import type { Barrier, DiagnosticResult, Folder, LumiDocument } from "@/types";
import type {
  ExportEdit,
  Adaptation,
  AdaptationRequest,
  ApiError,
} from "@/services";

interface LumiStore {
  user: typeof mockUser;
  documents: LumiDocument[];
  folders: Folder[];
  diagnostics: DiagnosticResult[];
  pendingUpload: File | null;
  activeFileUrl: string | null;
  activeDocument: LumiDocument | null;
  activeDiagnostic: DiagnosticResult | null;
  isLoading: boolean;
  error: string | null;
  currentSessionId: string | null;

  setPendingUpload: (file: File | null) => void;
  setDemoDocument: (fileName: string, fileUrl: string) => void;
  setActiveDocument: (id: string) => void;
  updateBarrierStatus: (
    barrierId: string,
    status: "Pendiente" | "Aplicada" | "Ignorada",
  ) => void;
  updateDocumentStatus: (id: string, newStatus: LumiDocument["status"]) => void;
  createFolder: (input: {
    name: string;
    color?: string;
    file?: { name: string; size: number } | null;
  }) => Folder | null;
  saveDocumentToFolder: (
    id: string,
    name: string,
    folderId: string | null,
  ) => void;
  renameDocument: (id: string, name: string) => void;
  saveDocumentEdits: (
    id: string,
    modifiedContent: string,
    barriers: Barrier[],
  ) => void;

  uploadAndAnalyze: (file: File) => Promise<void>;
  pollAnalysis: (sessionId: string) => Promise<void>;
  fetchDiagnosis: (sessionId: string) => Promise<void>;
  exportDocument: (sessionId: string, edits: ExportEdit[]) => Promise<Blob>;
  adaptBarrier: (request: AdaptationRequest) => Promise<Adaptation>;
  clearError: () => void;
  resetAnalysisState: () => void;
}

const FOLDER_COLORS = ["#8B5CF6", "#3B82F6", "#22C55E", "#F97316", "#EC4899"];

function formatStoreDate(): string {
  return new Intl.DateTimeFormat("es-AR", {
    day: "numeric",
    month: "long",
    year: "numeric",
  }).format(new Date());
}

const initialActiveDocument =
  mockDocuments.find((document) => document.id === mockDiagnostic.documentId) ??
  null;

export const useLumiStore = create<LumiStore>((set, get) => ({
  user: mockUser,
  documents: mockDocuments,
  folders: mockFolders,
  diagnostics: [mockDiagnostic],
  pendingUpload: null,
  activeFileUrl: null,
  activeDocument: initialActiveDocument,
  activeDiagnostic: initialActiveDocument ? mockDiagnostic : null,
  isLoading: false,
  error: null,
  currentSessionId: null,

  setPendingUpload: (file) => set({ pendingUpload: file }),

  setDemoDocument: (fileName, fileUrl) => {
    const demo = DEMO_MOCKS[fileName];

    if (!demo) {
      return;
    }

    const previousFileUrl = get().activeFileUrl;
    if (previousFileUrl && previousFileUrl !== fileUrl) {
      URL.revokeObjectURL(previousFileUrl);
    }

    set((state) => {
      const document: LumiDocument = {
        id: demo.id,
        name: demo.name,
        subject: fileName.includes("Biologia")
          ? "Biología"
          : fileName.includes("Geografia")
            ? "Geografía"
            : "Literatura",
        size: demo.size,
        date: "3 de noviembre de 2026",
        status: "Analizado",
        folderId: null,
        originalContent: demo.originalContent,
        modifiedContent: demo.modifiedContent,
      };
      const barriers: Barrier[] = demo.barriers.map(
        (barrier: {
          id: string;
          severity: Barrier["severity"];
          category: string;
          original: string;
          suggestion: string;
        }) => ({
          id: barrier.id,
          type: barrier.category,
          severity: barrier.severity,
          detectedFragment: barrier.original,
          suggestion: barrier.suggestion,
          status: "Pendiente",
        }),
      );
      const diagnostic: DiagnosticResult = {
        documentId: document.id,
        globalScore: 82,
        readabilityPercentage: 80,
        barriers,
      };
      const documents = state.documents.some((item) => item.id === document.id)
        ? state.documents.map((item) =>
            item.id === document.id ? document : item,
          )
        : [document, ...state.documents];
      const diagnostics = state.diagnostics.some(
        (item) => item.documentId === document.id,
      )
        ? state.diagnostics.map((item) =>
            item.documentId === document.id ? diagnostic : item,
          )
        : [...state.diagnostics, diagnostic];

      return {
        documents,
        diagnostics,
        activeFileUrl: fileUrl,
        activeDocument: document,
        activeDiagnostic: diagnostic,
      };
    });
  },

  setActiveDocument: (id) =>
    set((state) => {
      const activeDocument = state.documents.find(
        (document) => document.id === id,
      );

      if (!activeDocument) {
        return state;
      }

      return {
        activeDocument,
        activeDiagnostic:
          state.diagnostics.find(
            (diagnostic) => diagnostic.documentId === activeDocument.id,
          ) ?? null,
      };
    }),

  updateBarrierStatus: (barrierId, status) =>
    set((state) => {
      const diagnostics = state.diagnostics.map((diagnostic) => ({
        ...diagnostic,
        barriers: diagnostic.barriers.map((barrier) =>
          barrier.id === barrierId ? { ...barrier, status } : barrier,
        ),
      }));

      return {
        diagnostics,
        activeDiagnostic: state.activeDiagnostic
          ? (diagnostics.find(
              (diagnostic) =>
                diagnostic.documentId === state.activeDiagnostic?.documentId,
            ) ?? null)
          : null,
      };
    }),

  updateDocumentStatus: (id, newStatus) =>
    set((state) => {
      const documentExists = state.documents.some(
        (document) => document.id === id,
      );

      if (!documentExists) {
        return state;
      }

      const documents = state.documents.map((document) =>
        document.id === id ? { ...document, status: newStatus } : document,
      );

      return {
        documents,
        activeDocument:
          state.activeDocument?.id === id
            ? (documents.find((document) => document.id === id) ?? null)
            : state.activeDocument,
      };
    }),

  createFolder: ({ name, color, file }) => {
    const cleanName = name.trim();

    if (
      !cleanName ||
      get().folders.some(
        (folder) =>
          folder.name.trim().toLowerCase() === cleanName.toLowerCase(),
      )
    ) {
      return null;
    }

    const folder: Folder = {
      id: `carpeta-${crypto.randomUUID()}`,
      name: cleanName,
      color:
        color ?? FOLDER_COLORS[get().folders.length % FOLDER_COLORS.length],
    };
    const fileDocument: LumiDocument | null = file
      ? {
          id: `documento-${crypto.randomUUID()}`,
          name: file.name,
          subject: cleanName,
          size: `${(file.size / (1024 * 1024)).toFixed(1).replace(".", ",")} MB`,
          date: formatStoreDate(),
          status: "Analizado",
          folderId: folder.id,
          originalContent: "",
          modifiedContent: "",
        }
      : null;

    set((state) => ({
      folders: [...state.folders, folder],
      documents: fileDocument
        ? [fileDocument, ...state.documents]
        : state.documents,
    }));

    return folder;
  },

  saveDocumentToFolder: (id, name, folderId) =>
    set((state) => {
      const cleanName = name.trim();
      const documentExists = state.documents.some(
        (document) => document.id === id,
      );

      if (!cleanName || !documentExists) {
        return state;
      }

      const documents = state.documents.map((document) =>
        document.id === id
          ? {
              ...document,
              name: cleanName,
              folderId,
              status: "Guardado" as const,
              date: formatStoreDate(),
            }
          : document,
      );

      return {
        documents,
        activeDocument:
          state.activeDocument?.id === id
            ? (documents.find((document) => document.id === id) ?? null)
            : state.activeDocument,
      };
    }),

  renameDocument: (id, name) =>
    set((state) => {
      const documentExists = state.documents.some(
        (document) => document.id === id,
      );

      if (!documentExists) {
        return state;
      }

      const documents = state.documents.map((document) =>
        document.id === id ? { ...document, name } : document,
      );

      return {
        documents,
        activeDocument:
          state.activeDocument?.id === id
            ? (documents.find((document) => document.id === id) ?? null)
            : state.activeDocument,
      };
    }),

  saveDocumentEdits: (id, modifiedContent, barriers) =>
    set((state) => {
      const documentExists = state.documents.some(
        (document) => document.id === id,
      );

      if (!documentExists) {
        return state;
      }

      const documents = state.documents.map((document) =>
        document.id === id
          ? { ...document, modifiedContent, status: "En edición" as const }
          : document,
      );
      const diagnostics = state.diagnostics.map((diagnostic) =>
        diagnostic.documentId === id ? { ...diagnostic, barriers } : diagnostic,
      );

      return {
        documents,
        diagnostics,
        activeDocument:
          state.activeDocument?.id === id
            ? (documents.find((document) => document.id === id) ?? null)
            : state.activeDocument,
        activeDiagnostic:
          state.activeDiagnostic?.documentId === id
            ? (diagnostics.find((diagnostic) => diagnostic.documentId === id) ??
              null)
            : state.activeDiagnostic,
      };
    }),

  clearError: () => set({ error: null }),

  resetAnalysisState: () =>
    set({
      isLoading: false,
      error: null,
      currentSessionId: null,
      pendingUpload: null,
    }),

  uploadAndAnalyze: async (file: File) => {
    if (USE_MOCKS) {
      const fileUrl = URL.createObjectURL(file);
      get().setPendingUpload(file);
      get().setDemoDocument(file.name, fileUrl);
      return;
    }

    const fileUrl = URL.createObjectURL(file);
    const previousFileUrl = get().activeFileUrl;
    if (previousFileUrl && previousFileUrl !== fileUrl) {
      URL.revokeObjectURL(previousFileUrl);
    }

    set({
      isLoading: true,
      error: null,
      currentSessionId: null,
      pendingUpload: file,
      activeFileUrl: fileUrl,
    });

    try {
      const { api } = await import("@/services");
      const session = await api.createSessionFromFile(file);
      const document = mapSessionToDocument({
        ...session,
        filename: session.filename ?? file.name,
      });

      set((state) => {
        const documents = state.documents.some(
          (item) => item.id === document.id,
        )
          ? state.documents.map((item) =>
              item.id === document.id ? document : item,
            )
          : [document, ...state.documents];

        return {
          documents,
          activeDocument: document,
          currentSessionId: session.session_id,
          isLoading: false,
          pendingUpload: file,
          activeFileUrl: fileUrl,
        };
      });
    } catch (err) {
      if (get().activeFileUrl === fileUrl) {
        URL.revokeObjectURL(fileUrl);
      }
      const apiError = err as ApiError;
      set({
        isLoading: false,
        error: apiError.message ?? "Error al subir el archivo",
        currentSessionId: null,
        activeFileUrl: null,
      });
      throw err;
    }
  },

  pollAnalysis: async (sessionId: string) => {
    if (USE_MOCKS) {
      return;
    }

    set({ isLoading: true, error: null });

    try {
      const { api } = await import("@/services");

      await api.extractContent(sessionId);
      const diagnosis = await api.analyzeSession(sessionId, true);
      const extracted = await api.getContent(sessionId);

      const document = mapSessionToDocument(
        {
          session_id: sessionId,
          source_type: "pdf",
          filename: get().pendingUpload?.name ?? null,
          size_bytes: get().pendingUpload?.size ?? null,
          status: "analyzed",
          created_at: new Date().toISOString(),
        },
        extracted,
      );
      const diagnostic = mapDiagnosisToResult(diagnosis, extracted);

      const fileUrl = get().activeFileUrl;

      set((state) => {
        const documents = state.documents.some(
          (item) => item.id === document.id,
        )
          ? state.documents.map((item) =>
              item.id === document.id ? document : item,
            )
          : [document, ...state.documents];
        const diagnostics = state.diagnostics.some(
          (item) => item.documentId === document.id,
        )
          ? state.diagnostics.map((item) =>
              item.documentId === document.id ? diagnostic : item,
            )
          : [...state.diagnostics, diagnostic];

        return {
          documents,
          diagnostics,
          activeDocument: document,
          activeDiagnostic: diagnostic,
          activeFileUrl: fileUrl,
          isLoading: false,
          currentSessionId: sessionId,
        };
      });
    } catch (err) {
      const apiError = err as ApiError;
      set({
        isLoading: false,
        error: apiError.message ?? "Error al analizar el documento",
      });
      throw err;
    }
  },

  fetchDiagnosis: async (sessionId: string) => {
    if (USE_MOCKS) {
      return;
    }

    set({ isLoading: true, error: null });

    try {
      const { api } = await import("@/services");

      const session = await api.getSession(sessionId);
      const extracted = await api.getContent(sessionId);
      const diagnosis = await api.getDiagnosis(sessionId);

      const document = mapSessionToDocument(
        {
          ...session,
          filename: session.filename ?? get().pendingUpload?.name ?? null,
        },
        extracted,
      );
      const diagnostic = mapDiagnosisToResult(diagnosis, extracted);

      const fileUrl = get().activeFileUrl;

      set((state) => {
        const documents = state.documents.some(
          (item) => item.id === document.id,
        )
          ? state.documents.map((item) =>
              item.id === document.id ? document : item,
            )
          : [document, ...state.documents];
        const diagnostics = state.diagnostics.some(
          (item) => item.documentId === document.id,
        )
          ? state.diagnostics.map((item) =>
              item.documentId === document.id ? diagnostic : item,
            )
          : [...state.diagnostics, diagnostic];

        return {
          documents,
          diagnostics,
          activeDocument: document,
          activeDiagnostic: diagnostic,
          activeFileUrl: fileUrl,
          isLoading: false,
          currentSessionId: sessionId,
        };
      });
    } catch (err) {
      const apiError = err as ApiError;
      set({
        isLoading: false,
        error: apiError.message ?? "Error al obtener el diagnóstico",
      });
      throw err;
    }
  },

  exportDocument: async (sessionId: string, edits: ExportEdit[]) => {
    if (USE_MOCKS) {
      throw new Error("Export not available in mock mode");
    }

    const { api } = await import("@/services");
    return api.exportPdf(sessionId, edits);
  },

  adaptBarrier: async (request: AdaptationRequest) => {
    if (USE_MOCKS) {
      throw new Error("Adaptation not available in mock mode");
    }

    const { api } = await import("@/services");
    return api.adaptBarrier(request);
  },
}));
