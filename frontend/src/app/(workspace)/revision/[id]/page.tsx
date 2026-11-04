"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { diffWords } from "diff";
import {
  CheckCircle2,
  ChevronLeft,
  ChevronRight,
  FileText,
  Redo2,
  RotateCcw,
  Sparkles,
  Undo2,
} from "lucide-react";
import ExportModal from "@/components/modals/ExportModal";
import { useLumiStore } from "@/store/useLumiStore";
import type { LumiDocument } from "@/types";

export default function RevisionPage() {
  const { id } = useParams<{ id: string }>();
  const routeDocument = useLumiStore((state) =>
    state.documents.find((document) => document.id === id),
  );
  const activeDocument = useLumiStore((state) => state.activeDocument);
  const setActiveDocument = useLumiStore((state) => state.setActiveDocument);
  const document =
    routeDocument ?? (activeDocument?.id === id ? activeDocument : null);

  useEffect(() => {
    setActiveDocument(id);
  }, [id, setActiveDocument]);

  if (!document) {
    return (
      <main className="grid min-h-svh place-items-center bg-slate-50 px-4 text-slate-900">
        <section className="w-full max-w-lg rounded-xl border border-slate-200 bg-white p-8 text-center shadow-sm">
          <div className="mx-auto grid size-12 place-items-center rounded-lg bg-slate-100 text-slate-600">
            <FileText aria-hidden="true" className="size-6" />
          </div>
          <h1 className="page-title mt-4">No encontramos este documento</h1>
          <p className="mt-2 text-sm leading-6 text-slate-600">
            Revisá el enlace o volvé a tus archivos para elegir otro material.
          </p>
          <Link
            href="/archivos"
            className="mt-6 inline-flex min-h-11 items-center justify-center rounded-lg bg-blue-700 px-5 py-2.5 text-sm font-semibold text-white transition hover:bg-blue-800 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-blue-700"
          >
            Volver a mis archivos
          </Link>
        </section>
      </main>
    );
  }

  return <RevisionWorkspace key={document.id} id={id} document={document} />;
}

function RevisionWorkspace({
  id,
  document,
}: {
  id: string;
  document: LumiDocument;
}) {
  const [editedContent, setEditedContent] = useState(document.modifiedContent);
  const [undoStack, setUndoStack] = useState<string[]>([]);
  const [redoStack, setRedoStack] = useState<string[]>([]);
  const [isEditing, setIsEditing] = useState(false);
  const [isModalOpen, setIsModalOpen] = useState(false);

  function handleContentChange(nextContent: string) {
    if (nextContent === editedContent) return;

    setUndoStack((previous) => [...previous, editedContent]);
    setRedoStack([]);
    setEditedContent(nextContent);
  }

  function handleUndo() {
    const previousContent = undoStack.at(-1);
    if (previousContent === undefined) return;

    setRedoStack((previous) => [...previous, editedContent]);
    setUndoStack((previous) => previous.slice(0, -1));
    setEditedContent(previousContent);
  }

  function handleRedo() {
    const nextContent = redoStack.at(-1);
    if (nextContent === undefined) return;

    setUndoStack((previous) => [...previous, editedContent]);
    setRedoStack((previous) => previous.slice(0, -1));
    setEditedContent(nextContent);
  }

  function handleReset() {
    if (editedContent === document.modifiedContent) return;

    setUndoStack((previous) => [...previous, editedContent]);
    setRedoStack([]);
    setEditedContent(document.modifiedContent);
    setIsEditing(false);
  }

  const differences = isEditing
    ? []
    : diffWords(document.originalContent, editedContent);

  return (
    <main className="flex min-h-svh flex-col bg-slate-100 text-slate-900">
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex w-full max-w-7xl flex-wrap items-center justify-between gap-4 px-4 py-4 sm:px-6">
          <div className="flex min-w-0 items-center gap-4">
            <Link
              href="/inicio"
              aria-label="LUMI, volver a inicio"
              className="inline-flex shrink-0 items-center gap-2 text-lg font-bold text-slate-900"
            >
              <Sparkles aria-hidden="true" className="size-6 text-blue-600" />
              LUMI
            </Link>
            <span className="hidden h-8 border-l border-slate-200 sm:block" />
            <div className="min-w-0">
              <h1 className="page-title min-w-0 truncate">{document.name}</h1>
              <p className="mt-0.5 text-xs text-slate-500 sm:text-sm">
                {document.size} <span aria-hidden="true">·</span> Comparador de
                documentos
              </p>
            </div>
          </div>

          <div className="flex w-full items-center justify-between gap-3 sm:w-auto sm:justify-end">
            <span className="inline-flex items-center gap-1.5 rounded-full border border-emerald-200 bg-emerald-50 px-3 py-1.5 text-xs font-semibold text-emerald-800 sm:text-sm">
              <CheckCircle2 aria-hidden="true" className="size-4" />
              Análisis completado
            </span>
            <Link
              href={`/diagnostico/${encodeURIComponent(id)}`}
              className="inline-flex min-h-10 items-center justify-center rounded-lg border border-slate-200 bg-white px-3 text-xs font-semibold text-slate-700 transition hover:bg-slate-50 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-blue-700 sm:px-4 sm:text-sm"
            >
              Ver resumen
            </Link>
          </div>
        </div>

        <div className="border-t border-slate-100">
          <div className="mx-auto flex w-full max-w-7xl items-center justify-center px-4 py-2.5 sm:px-6">
            <nav aria-label="Paginación del documento">
              <ol className="flex items-center gap-2 text-sm">
                <li>
                  <button
                    type="button"
                    aria-label="Página anterior"
                    disabled
                    className="grid size-8 place-items-center rounded-md text-slate-400 disabled:cursor-not-allowed"
                  >
                    <ChevronLeft aria-hidden="true" className="size-4" />
                  </button>
                </li>
                <li
                  aria-current="page"
                  className="min-w-16 rounded-full border border-slate-300 bg-white px-3 py-1 text-center text-xs font-semibold tabular-nums text-slate-700"
                >
                  1 / 6
                </li>
                <li>
                  <button
                    type="button"
                    aria-label="Página siguiente"
                    disabled
                    className="grid size-8 place-items-center rounded-md text-slate-400 disabled:cursor-not-allowed"
                  >
                    <ChevronRight aria-hidden="true" className="size-4" />
                  </button>
                </li>
              </ol>
            </nav>
          </div>
        </div>
      </header>

      <div className="mx-auto flex w-full max-w-7xl flex-1 flex-col px-4 py-3 sm:px-6 sm:py-4">
        <div className="grid flex-1 grid-cols-1 gap-3 xl:h-[calc(100svh-15rem)] xl:min-h-128 xl:grid-cols-2 xl:gap-4">
          <section
            aria-labelledby="original-title"
            className="flex min-h-80 min-w-0 flex-col overflow-hidden rounded-lg border border-slate-200 bg-white shadow-sm lg:min-h-0"
          >
            <div className="flex min-h-12 items-center justify-between border-b border-slate-200 px-4 sm:px-5">
              <h2 id="original-title" className="text-sm font-semibold">
                Documento original
              </h2>
              <span className="rounded-full bg-slate-100 px-2.5 py-1 text-[11px] font-medium text-slate-600">
                Solo lectura
              </span>
            </div>
            <div className="min-h-0 flex-1 overflow-y-auto bg-slate-100/70 p-3 sm:p-5">
              <article className="mx-auto min-h-full max-w-3xl rounded-sm border border-slate-200 bg-white px-5 py-7 shadow-sm sm:px-8 sm:py-10">
                <p className="whitespace-pre-wrap wrap-break-word text-sm leading-7 text-slate-700 sm:text-[15px] sm:leading-8">
                  {document.originalContent}
                </p>
              </article>
            </div>
          </section>

          <section
            aria-labelledby="modified-title"
            className="flex min-h-80 min-w-0 flex-col overflow-hidden rounded-lg border border-blue-200 bg-white shadow-sm lg:min-h-0"
          >
            <div className="flex min-h-12 items-center justify-between gap-3 border-b border-slate-200 px-4 sm:px-5">
              <h2 id="modified-title" className="text-sm font-semibold">
                Documento en edición
              </h2>
              <button
                type="button"
                onClick={() => setIsEditing((editing) => !editing)}
                className="inline-flex min-h-8 items-center rounded-md px-2.5 text-xs font-semibold text-blue-700 transition hover:bg-blue-50 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-blue-700"
              >
                {isEditing ? "Ver documento" : "Editar texto"}
              </button>
            </div>
            <div className="min-h-0 flex-1 overflow-y-auto bg-slate-100/70 p-3 sm:p-5">
              <article className="mx-auto min-h-full max-w-3xl rounded-sm border border-slate-200 bg-white px-5 py-7 shadow-sm sm:px-8 sm:py-10">
                {isEditing ? (
                  <textarea
                    aria-label="Editar texto del documento"
                    value={editedContent}
                    onChange={(event) =>
                      handleContentChange(event.currentTarget.value)
                    }
                    className="min-h-96 w-full resize-y whitespace-pre-wrap wrap-break-word border-0 bg-transparent p-0 text-sm leading-7 text-slate-700 outline-none focus-visible:ring-2 focus-visible:ring-blue-600 sm:min-h-128 sm:text-[15px] sm:leading-8"
                  />
                ) : (
                  <p className="whitespace-pre-wrap wrap-break-word text-sm leading-7 text-slate-700 sm:text-[15px] sm:leading-8">
                    {differences.map((part, index) =>
                      part.added ? (
                        <mark
                          key={`${index}-${part.value.length}`}
                          className="rounded-sm bg-emerald-100 px-0.5 text-emerald-950 decoration-emerald-400"
                        >
                          {part.value}
                        </mark>
                      ) : (
                        <span key={`${index}-${part.value.length}`}>
                          {part.value}
                        </span>
                      ),
                    )}
                  </p>
                )}
              </article>
            </div>
          </section>
        </div>
      </div>

      <footer className="sticky bottom-0 z-10 border-t border-slate-200 bg-white/95 shadow-[0_-8px_24px_rgba(15,23,42,0.06)] backdrop-blur">
        <div className="mx-auto flex w-full max-w-7xl flex-wrap items-center justify-between gap-3 px-4 py-3 sm:px-6">
          <div className="flex flex-wrap items-center gap-2">
            <button
              type="button"
              onClick={handleUndo}
              disabled={undoStack.length === 0}
              className="inline-flex min-h-10 items-center gap-2 rounded-md px-3 text-sm font-medium text-slate-700 transition hover:bg-slate-100 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-blue-700 disabled:cursor-not-allowed disabled:text-slate-400 disabled:hover:bg-transparent"
            >
              <Undo2 aria-hidden="true" className="size-4" />
              Deshacer
            </button>
            <button
              type="button"
              onClick={handleRedo}
              disabled={redoStack.length === 0}
              className="inline-flex min-h-10 items-center gap-2 rounded-md px-3 text-sm font-medium text-slate-700 transition hover:bg-slate-100 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-blue-700 disabled:cursor-not-allowed disabled:text-slate-400 disabled:hover:bg-transparent"
            >
              <Redo2 aria-hidden="true" className="size-4" />
              Rehacer
            </button>
            <span className="hidden h-6 border-l border-slate-200 sm:block" />
            <button
              type="button"
              onClick={handleReset}
              disabled={editedContent === document.modifiedContent}
              className="inline-flex min-h-10 items-center gap-2 rounded-md px-3 text-sm font-medium text-slate-600 transition hover:bg-slate-100 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-blue-700 disabled:cursor-not-allowed disabled:text-slate-400 disabled:hover:bg-transparent"
            >
              <RotateCcw aria-hidden="true" className="size-4" />
              Reiniciar
            </button>
          </div>

          <button
            type="button"
            onClick={() => setIsModalOpen(true)}
            className="inline-flex min-h-10 items-center justify-center rounded-lg bg-blue-600 px-5 py-2 text-sm font-semibold text-white transition hover:bg-blue-700 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-blue-700"
          >
            Finalizar
          </button>
        </div>
      </footer>

      <ExportModal isOpen={isModalOpen} onClose={() => setIsModalOpen(false)} />
    </main>
  );
}
