"use client";

import { create } from "zustand";
import { mockDiagnostic, mockDocuments, mockUser } from "@/mocks/mockData";
import type { DiagnosticResult, LumiDocument } from "@/types";

interface LumiStore {
  user: typeof mockUser;
  documents: LumiDocument[];
  diagnostics: DiagnosticResult[];
  activeDocument: LumiDocument | null;
  activeDiagnostic: DiagnosticResult | null;
  setActiveDocument: (id: string) => void;
  updateBarrierStatus: (
    barrierId: string,
    status: "Pendiente" | "Aplicada" | "Ignorada",
  ) => void;
  updateDocumentStatus: (id: string, newStatus: LumiDocument["status"]) => void;
}

const initialActiveDocument =
  mockDocuments.find((document) => document.id === mockDiagnostic.documentId) ??
  null;

export const useLumiStore = create<LumiStore>((set) => ({
  user: mockUser,
  documents: mockDocuments,
  diagnostics: [mockDiagnostic],
  activeDocument: initialActiveDocument,
  activeDiagnostic: initialActiveDocument ? mockDiagnostic : null,

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
}));
