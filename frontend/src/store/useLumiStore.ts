"use client";

import { create } from "zustand";
import { mockDiagnostic, mockDocuments, mockUser } from "@/mocks/mockData";
import { DEMO_MOCKS } from "@/lib/demoMocks";
import type { Barrier, DiagnosticResult, LumiDocument } from "@/types";

interface LumiStore {
  user: typeof mockUser;
  documents: LumiDocument[];
  diagnostics: DiagnosticResult[];
  pendingUpload: File | null;
  activeDocument: LumiDocument | null;
  activeDiagnostic: DiagnosticResult | null;
  setPendingUpload: (file: File | null) => void;
  setDemoDocument: (fileName: string) => void;
  setActiveDocument: (id: string) => void;
  updateBarrierStatus: (
    barrierId: string,
    status: "Pendiente" | "Aplicada" | "Ignorada",
  ) => void;
  updateDocumentStatus: (id: string, newStatus: LumiDocument["status"]) => void;
  saveDocumentEdits: (
    id: string,
    modifiedContent: string,
    barriers: Barrier[],
  ) => void;
}

const initialActiveDocument =
  mockDocuments.find((document) => document.id === mockDiagnostic.documentId) ??
  null;

export const useLumiStore = create<LumiStore>((set) => ({
  user: mockUser,
  documents: mockDocuments,
  diagnostics: [mockDiagnostic],
  pendingUpload: null,
  activeDocument: initialActiveDocument,
  activeDiagnostic: initialActiveDocument ? mockDiagnostic : null,
  setPendingUpload: (file) => set({ pendingUpload: file }),

  setDemoDocument: (fileName) =>
    set((state) => {
      const demo = DEMO_MOCKS[fileName];

      if (!demo) {
        return state;
      }

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
        activeDocument: document,
        activeDiagnostic: diagnostic,
      };
    }),

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
}));
