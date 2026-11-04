"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import * as Dialog from "@radix-ui/react-dialog";
import { diffWords } from "diff";
import {
  ArrowLeft,
  CheckCircle2,
  ChevronLeft,
  ChevronRight,
  Download,
  Eye,
  FileText,
  Minus,
  Pencil,
  Plus,
  Redo2,
  Save,
  Undo2,
  X,
} from "lucide-react";
import ExportModal from "@/components/modals/ExportModal";
import { SuggestionCard } from "@/components/editor/SuggestionCard";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { downloadDocumentPdf, paginateDocumentText } from "@/lib/documentPdf";
import { useLumiStore } from "@/store/useLumiStore";
import type { Barrier, LumiDocument } from "@/types";

type EditorSnapshot = {
  content: string;
  barriers: Barrier[];
};

function cloneBarriers(barriers: Barrier[]): Barrier[] {
  return barriers.map((barrier) => ({ ...barrier }));
}

function escapeRegExp(value: string): string {
  return value.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

function createFlexiblePattern(value: string): RegExp | null {
  const normalized = value.trim();

  if (!normalized) {
    return null;
  }

  const pattern = normalized.split(/\s+/).map(escapeRegExp).join("\\s+");

  return new RegExp(pattern, "g");
}

function replaceFlexibleText(
  content: string,
  original: string,
  replacement: string,
): string | null {
  const pattern = createFlexiblePattern(original);

  if (!pattern) {
    return null;
  }

  const updatedContent = content.replace(pattern, replacement);
  return updatedContent === content ? null : updatedContent;
}

function findFlexibleRange(content: string, value: string) {
  const pattern = createFlexiblePattern(value);
  const match = pattern?.exec(content);

  return match
    ? { start: match.index, end: match.index + match[0].length }
    : null;
}

function mapOriginalRangeToEdited(
  original: string,
  edited: string,
  targetRange: { start: number; end: number },
) {
  let originalOffset = 0;
  let editedOffset = 0;
  let mappedStart: number | null = null;
  let mappedEnd: number | null = null;

  for (const part of diffWords(original, edited)) {
    const partLength = part.value.length;

    if (part.added) {
      if (
        originalOffset >= targetRange.start &&
        originalOffset <= targetRange.end
      ) {
        mappedStart = Math.min(mappedStart ?? editedOffset, editedOffset);
        mappedEnd = Math.max(
          mappedEnd ?? editedOffset,
          editedOffset + partLength,
        );
      }

      editedOffset += partLength;
      continue;
    }

    const overlapStart = Math.max(originalOffset, targetRange.start);
    const overlapEnd = Math.min(originalOffset + partLength, targetRange.end);

    if (part.removed) {
      if (overlapStart < overlapEnd) {
        mappedStart = Math.min(mappedStart ?? editedOffset, editedOffset);
        mappedEnd = Math.max(mappedEnd ?? editedOffset, editedOffset);
      }

      originalOffset += partLength;
      continue;
    }

    if (overlapStart < overlapEnd) {
      const start = editedOffset + overlapStart - originalOffset;
      const end = editedOffset + overlapEnd - originalOffset;
      mappedStart = Math.min(mappedStart ?? start, start);
      mappedEnd = Math.max(mappedEnd ?? end, end);
    }

    originalOffset += partLength;
    editedOffset += partLength;
  }

  return mappedStart === null || mappedEnd === null
    ? null
    : { start: mappedStart, end: mappedEnd };
}

function replaceDetectedFragment(
  original: string,
  edited: string,
  fragment: string,
  replacement: string,
): string | null {
  const directReplacement = replaceFlexibleText(edited, fragment, replacement);

  if (directReplacement !== null) {
    return directReplacement;
  }

  const originalRange = findFlexibleRange(original, fragment);
  const editedRange = originalRange
    ? mapOriginalRangeToEdited(original, edited, originalRange)
    : null;

  if (!editedRange) {
    return null;
  }

  const updatedContent =
    edited.slice(0, editedRange.start) +
    replacement +
    edited.slice(editedRange.end);

  return updatedContent === edited ? null : updatedContent;
}

function containsFlexibleText(content: string, value: string): boolean {
  const pattern = createFlexiblePattern(value);
  return pattern ? new RegExp(pattern.source).test(content) : false;
}

function renderOriginalHighlights(
  content: string,
  barriers: Barrier[],
): React.ReactNode[] {
  const matches: {
    start: number;
    end: number;
    text: string;
    severity: Barrier["severity"];
  }[] = [];

  for (const barrier of barriers) {
    if (barrier.status === "Ignorada") {
      continue;
    }

    const pattern = createFlexiblePattern(barrier.detectedFragment);

    if (!pattern) {
      continue;
    }

    let match: RegExpExecArray | null;

    while ((match = pattern.exec(content)) !== null) {
      matches.push({
        start: match.index,
        end: match.index + match[0].length,
        text: match[0],
        severity: barrier.severity,
      });
    }
  }

  matches.sort(
    (first, second) => first.start - second.start || second.end - first.end,
  );

  const nodes: React.ReactNode[] = [];
  let cursor = 0;

  for (const match of matches) {
    if (match.start < cursor) {
      continue;
    }

    if (match.start > cursor) {
      nodes.push(content.slice(cursor, match.start));
    }

    const tone =
      match.severity === "Alta"
        ? "bg-red-100 text-red-950"
        : match.severity === "Media"
          ? "bg-amber-100 text-amber-950"
          : "bg-emerald-100 text-emerald-950";

    nodes.push(
      <mark
        key={`${match.start}-${match.end}`}
        className={`rounded-sm px-0.5 ${tone}`}
      >
        {match.text}
      </mark>,
    );
    cursor = match.end;
  }

  if (cursor < content.length) {
    nodes.push(content.slice(cursor));
  }

  return nodes;
}

function renderEditedDiff(original: string, edited: string): React.ReactNode[] {
  return diffWords(original, edited).flatMap((part, index) => {
    if (part.removed) {
      return [];
    }

    if (part.added) {
      return [
        <mark
          key={`${index}-${part.value.length}`}
          className="rounded-sm bg-blue-100 px-0.5 text-blue-950"
        >
          {part.value}
        </mark>,
      ];
    }

    return [<span key={`${index}-${part.value.length}`}>{part.value}</span>];
  });
}

function getPdfFileName(documentName: string): string {
  const nameWithoutExtension = documentName.replace(/\.pdf$/i, "");
  return `${nameWithoutExtension}_editado.pdf`;
}

export default function EditarDocumentoPage() {
  const { id } = useParams<{ id: string }>();
  const document = useLumiStore((state) =>
    state.documents.find((item) => item.id === id),
  );
  const diagnostic = useLumiStore((state) =>
    state.diagnostics.find((item) => item.documentId === id),
  );
  const setActiveDocument = useLumiStore((state) => state.setActiveDocument);
  const saveDocumentEdits = useLumiStore((state) => state.saveDocumentEdits);

  useEffect(() => {
    setActiveDocument(id);
  }, [id, setActiveDocument]);

  if (!document) {
    return (
      <main className="grid min-h-[calc(100svh-5rem)] place-items-center bg-slate-50 px-4 text-slate-900">
        <section className="w-full max-w-lg rounded-lg border border-slate-200 bg-white p-8 text-center">
          <FileText
            aria-hidden="true"
            className="mx-auto size-10 text-slate-500"
          />
          <h1 className="mt-4 text-xl font-bold">
            No encontramos este documento
          </h1>
          <p className="mt-2 text-sm text-slate-600">
            Revisá el enlace o volvé a tus archivos para elegir otro material.
          </p>
          <Link
            href="/archivos"
            className="mt-6 inline-flex min-h-10 items-center justify-center rounded-md bg-blue-700 px-4 text-sm font-semibold text-white hover:bg-blue-800"
          >
            Volver a mis archivos
          </Link>
        </section>
      </main>
    );
  }

  return (
    <EditorWorkspace
      key={document.id}
      document={document}
      initialBarriers={diagnostic?.barriers ?? []}
      saveDocumentEdits={saveDocumentEdits}
    />
  );
}

function EditorWorkspace({
  document,
  initialBarriers,
  saveDocumentEdits,
}: {
  document: LumiDocument;
  initialBarriers: Barrier[];
  saveDocumentEdits: (
    id: string,
    modifiedContent: string,
    barriers: Barrier[],
  ) => void;
}) {
  const [editedContent, setEditedContent] = useState(document.modifiedContent);
  const [barriers, setBarriers] = useState(() =>
    cloneBarriers(initialBarriers),
  );
  const [savedContent, setSavedContent] = useState(document.modifiedContent);
  const [savedBarriers, setSavedBarriers] = useState(() =>
    cloneBarriers(initialBarriers),
  );
  const [undoStack, setUndoStack] = useState<EditorSnapshot[]>([]);
  const [redoStack, setRedoStack] = useState<EditorSnapshot[]>([]);
  const [currentPage, setCurrentPage] = useState(1);
  const [originalZoom, setOriginalZoom] = useState(100);
  const [editedZoom, setEditedZoom] = useState(100);
  const [isPreviewOpen, setIsPreviewOpen] = useState(false);
  const [isTextEditorOpen, setIsTextEditorOpen] = useState(false);
  const [isExportModalOpen, setIsExportModalOpen] = useState(false);
  const [textDraft, setTextDraft] = useState(editedContent);
  const [notice, setNotice] = useState("");

  const originalPages = paginateDocumentText(document.originalContent);
  const editedPages = paginateDocumentText(editedContent);
  const pageCount = Math.max(originalPages.length, editedPages.length);
  const activePage = Math.min(currentPage, pageCount);
  const originalPage = originalPages[activePage - 1] ?? "";
  const editedPage = editedPages[activePage - 1] ?? "";
  const visibleBarriers = barriers.filter(
    (barrier) => barrier.status !== "Ignorada",
  );
  const isDirty =
    editedContent !== savedContent ||
    JSON.stringify(barriers) !== JSON.stringify(savedBarriers);

  function saveSnapshot() {
    setUndoStack((previous) => [
      ...previous,
      { content: editedContent, barriers: cloneBarriers(barriers) },
    ]);
    setRedoStack([]);
  }

  function handleApply(barrier: Barrier, acceptedSuggestion: string) {
    if (barrier.status === "Aplicada") {
      return;
    }

    const nextContent = replaceDetectedFragment(
      document.originalContent,
      editedContent,
      barrier.detectedFragment,
      acceptedSuggestion,
    );
    const alreadyPresent = containsFlexibleText(
      editedContent,
      acceptedSuggestion,
    );

    if (nextContent === null && !alreadyPresent) {
      setNotice(
        `No se encontró el fragmento detectado en ${document.name}. No se aplicaron cambios.`,
      );
      return;
    }

    saveSnapshot();

    if (nextContent !== null) {
      setEditedContent(nextContent);
    }

    setBarriers((previous) =>
      previous.map((item) =>
        item.id === barrier.id
          ? { ...item, suggestion: acceptedSuggestion, status: "Aplicada" }
          : item,
      ),
    );
    setNotice("Se aplicó la sugerencia al documento en edición.");
  }

  function handleDismiss(barrier: Barrier) {
    if (barrier.status !== "Pendiente") {
      return;
    }

    saveSnapshot();
    setBarriers((previous) =>
      previous.map((item) =>
        item.id === barrier.id ? { ...item, status: "Ignorada" } : item,
      ),
    );
    setNotice("Se descartó la sugerencia.");
  }

  function handleTextDraftSave() {
    if (textDraft !== editedContent) {
      saveSnapshot();
      setEditedContent(textDraft);
    }

    setIsTextEditorOpen(false);
    setNotice("Se actualizó el documento en edición.");
  }

  function handleUndo() {
    const previousSnapshot = undoStack.at(-1);

    if (!previousSnapshot) {
      return;
    }

    setRedoStack((previous) => [
      ...previous,
      { content: editedContent, barriers: cloneBarriers(barriers) },
    ]);
    setEditedContent(previousSnapshot.content);
    setBarriers(cloneBarriers(previousSnapshot.barriers));
    setUndoStack((previous) => previous.slice(0, -1));
    setNotice("Se deshizo el último cambio.");
  }

  function handleRedo() {
    const nextSnapshot = redoStack.at(-1);

    if (!nextSnapshot) {
      return;
    }

    setUndoStack((previous) => [
      ...previous,
      { content: editedContent, barriers: cloneBarriers(barriers) },
    ]);
    setEditedContent(nextSnapshot.content);
    setBarriers(cloneBarriers(nextSnapshot.barriers));
    setRedoStack((previous) => previous.slice(0, -1));
    setNotice("Se rehizo el cambio.");
  }

  function handleSaveChanges() {
    saveDocumentEdits(document.id, editedContent, cloneBarriers(barriers));
    setSavedContent(editedContent);
    setSavedBarriers(cloneBarriers(barriers));
    setNotice("Se guardaron los cambios en esta sesión.");
  }

  function handleDownloadPdf() {
    downloadDocumentPdf(editedContent, getPdfFileName(document.name));
    setIsExportModalOpen(false);
    setNotice("Se generó el PDF del documento editado.");
  }

  function handleOpenTextEditor() {
    setTextDraft(editedContent);
    setIsTextEditorOpen(true);
  }

  const canGoToPreviousPage = activePage > 1;
  const canGoToNextPage = activePage < pageCount;
  const documentStatus = isDirty ? "Sin guardar" : document.status;

  return (
    <main className="flex min-h-[calc(100svh-5rem)] flex-col bg-slate-100 pb-14 text-slate-900 lg:h-[calc(100svh-5rem)] lg:min-h-0">
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto grid w-full max-w-[1900px] gap-3 px-3 py-3 sm:px-5 lg:grid-cols-[minmax(0,1fr)_auto_auto] lg:items-center">
          <div className="flex min-w-0 items-center gap-2 sm:gap-3">
            <Link
              href="/archivos"
              aria-label="Volver a mis archivos"
              className="grid size-9 shrink-0 place-items-center rounded-md text-slate-600 transition hover:bg-slate-100"
            >
              <ArrowLeft aria-hidden="true" className="size-4" />
            </Link>
            <div className="grid size-10 shrink-0 place-items-center rounded-md bg-blue-50 text-blue-700">
              <FileText aria-hidden="true" className="size-5" />
            </div>
            <div className="min-w-0">
              <h1 className="truncate text-sm font-semibold sm:text-base">
                {document.name}
              </h1>
              <p className="truncate text-xs text-slate-500">
                {document.size} <span aria-hidden="true">·</span> Última
                modificación: {document.date}
              </p>
            </div>
            <Badge
              variant={documentStatus}
              className="hidden shrink-0 sm:inline-flex"
            />
          </div>

          <nav
            aria-label="Paginación del documento"
            className="justify-self-center"
          >
            <ol className="flex items-center gap-1">
              <li>
                <Button
                  variant="ghost"
                  aria-label="Página anterior"
                  title="Página anterior"
                  disabled={!canGoToPreviousPage}
                  onClick={() => setCurrentPage(Math.max(1, activePage - 1))}
                  className="size-8 p-0"
                >
                  <ChevronLeft aria-hidden="true" className="size-4" />
                </Button>
              </li>
              <li
                aria-current="page"
                className="min-w-16 rounded-md border border-slate-300 bg-white px-3 py-1.5 text-center text-xs font-semibold tabular-nums text-slate-700"
              >
                {activePage} / {pageCount}
              </li>
              <li>
                <Button
                  variant="ghost"
                  aria-label="Página siguiente"
                  title="Página siguiente"
                  disabled={!canGoToNextPage}
                  onClick={() =>
                    setCurrentPage(Math.min(pageCount, activePage + 1))
                  }
                  className="size-8 p-0"
                >
                  <ChevronRight aria-hidden="true" className="size-4" />
                </Button>
              </li>
            </ol>
          </nav>

          <div className="flex flex-wrap items-center justify-end gap-2">
            <Button
              variant="outline"
              onClick={handleDownloadPdf}
              className="min-h-9 px-3 py-2 text-xs sm:text-sm"
            >
              <Download aria-hidden="true" className="size-4" />
              Descargar PDF
            </Button>
            <Button
              variant="primary"
              onClick={handleSaveChanges}
              disabled={!isDirty}
              className="min-h-9 px-3 py-2 text-xs sm:text-sm"
            >
              <Save aria-hidden="true" className="size-4" />
              Guardar cambios
            </Button>
          </div>
        </div>
      </header>

      <div className="mx-auto flex min-h-0 w-full max-w-[1900px] flex-1 flex-col p-2 sm:p-3">
        <div className="grid min-h-[70svh] flex-1 grid-cols-1 gap-3 lg:h-[calc(100svh-16rem)] lg:min-h-120 lg:grid-cols-[minmax(18rem,0.33fr)_minmax(0,0.67fr)]">
          <aside className="flex min-h-0 min-w-0 flex-col overflow-hidden rounded-md border border-slate-200 bg-white">
            <header className="border-b border-slate-200 p-3 sm:p-4">
              <div className="flex items-start gap-2.5 rounded-md bg-red-50 p-3">
                <span className="mt-0.5 grid size-6 shrink-0 place-items-center rounded-full bg-red-600 text-white">
                  <span aria-hidden="true" className="text-sm font-bold">
                    !
                  </span>
                </span>
                <div className="min-w-0">
                  <h2 className="text-sm font-bold text-red-900">
                    Se detectaron {barriers.length} errores que requieren
                    revisión
                  </h2>
                  <p className="mt-1 text-xs leading-5 text-slate-600">
                    Revisá cada sugerencia y decidí si querés aplicarla al
                    documento.
                  </p>
                </div>
              </div>
              <div
                className="mt-3 flex flex-wrap gap-2"
                aria-label="Resumen por severidad"
              >
                {(["Alta", "Media", "Baja"] as const).map((severity) => {
                  const count = barriers.filter(
                    (barrier) => barrier.severity === severity,
                  ).length;

                  return (
                    <Badge key={severity} variant={severity}>
                      {count} {severity.toLowerCase()}
                      {count === 1 ? "" : "s"}
                    </Badge>
                  );
                })}
              </div>
              {notice && (
                <p
                  role="status"
                  aria-live="polite"
                  className="mt-3 rounded-md border border-blue-200 bg-blue-50 p-2.5 text-xs leading-5 text-blue-900"
                >
                  {notice}
                </p>
              )}
            </header>

            <div className="min-h-0 flex-1 space-y-3 overflow-y-auto p-3">
              {visibleBarriers.length > 0 ? (
                visibleBarriers.map((barrier) => (
                  <SuggestionCard
                    key={barrier.id}
                    barrier={barrier}
                    onApply={handleApply}
                    onDismiss={handleDismiss}
                  />
                ))
              ) : (
                <p className="rounded-md border border-emerald-200 bg-emerald-50 p-4 text-sm text-emerald-900">
                  No hay sugerencias pendientes para este documento.
                </p>
              )}
            </div>
          </aside>

          <section
            aria-label="Comparación de documentos"
            className="grid min-h-0 min-w-0 grid-cols-1 gap-2 lg:grid-cols-2"
          >
            <DocumentPanel
              title="Documento original"
              zoom={originalZoom}
              onZoomChange={setOriginalZoom}
            >
              {renderOriginalHighlights(originalPage, barriers)}
            </DocumentPanel>

            <DocumentPanel
              title="Documento en edición"
              zoom={editedZoom}
              onZoomChange={setEditedZoom}
              action={
                <Button
                  variant="ghost"
                  onClick={handleOpenTextEditor}
                  className="size-8 p-0 text-blue-700"
                  aria-label="Editar texto del documento"
                  title="Editar texto"
                >
                  <Pencil aria-hidden="true" className="size-4" />
                </Button>
              }
            >
              {renderEditedDiff(originalPage, editedPage)}
            </DocumentPanel>
          </section>
        </div>
      </div>

      <footer className="fixed inset-x-0 bottom-0 z-30 border-t border-slate-200 bg-white/95 shadow-[0_-8px_24px_rgba(15,23,42,0.06)] backdrop-blur">
        <div className="mx-auto flex w-full max-w-[1900px] flex-wrap items-center justify-between gap-2 px-3 py-2 sm:px-5">
          <div className="flex flex-wrap items-center gap-1">
            <Button
              variant="ghost"
              onClick={handleUndo}
              disabled={undoStack.length === 0}
              className="min-h-9 px-2.5 text-xs sm:text-sm"
            >
              <Undo2 aria-hidden="true" className="size-4" />
              Deshacer
            </Button>
            <Button
              variant="ghost"
              onClick={handleRedo}
              disabled={redoStack.length === 0}
              className="min-h-9 px-2.5 text-xs sm:text-sm"
            >
              <Redo2 aria-hidden="true" className="size-4" />
              Rehacer
            </Button>
            <span className="mx-1 hidden h-6 border-l border-slate-200 sm:block" />
            <Button
              variant="outline"
              onClick={() => setIsPreviewOpen(true)}
              className="min-h-9 px-2.5 text-xs sm:text-sm"
            >
              <Eye aria-hidden="true" className="size-4" />
              Vista previa
            </Button>
          </div>
          <div className="flex items-center gap-2">
            <span className="hidden sm:inline">
              <Badge variant={documentStatus} />
            </span>
            <Button
              variant="primary"
              onClick={() => setIsExportModalOpen(true)}
              className="min-h-9 px-4 py-2 text-xs sm:text-sm"
            >
              Finalizar
              <ChevronRight aria-hidden="true" className="size-4" />
            </Button>
          </div>
        </div>
      </footer>

      <Dialog.Root open={isPreviewOpen} onOpenChange={setIsPreviewOpen}>
        <Dialog.Portal>
          <Dialog.Overlay className="fixed inset-0 z-40 bg-slate-950/55" />
          <Dialog.Content className="fixed left-1/2 top-1/2 z-50 flex max-h-[90dvh] w-[calc(100vw-2rem)] max-w-4xl -translate-x-1/2 -translate-y-1/2 flex-col overflow-hidden rounded-lg border border-slate-200 bg-slate-100 p-4 shadow-2xl focus:outline-none sm:p-6">
            <header className="flex items-start justify-between gap-4">
              <div>
                <Dialog.Title className="text-lg font-bold">
                  Vista previa
                </Dialog.Title>
                <Dialog.Description className="mt-1 text-sm text-slate-600">
                  {document.name} · {editedPages.length} páginas
                </Dialog.Description>
              </div>
              <Dialog.Close asChild>
                <Button
                  variant="ghost"
                  aria-label="Cerrar vista previa"
                  className="size-9 shrink-0 p-0"
                >
                  <X aria-hidden="true" className="size-4" />
                </Button>
              </Dialog.Close>
            </header>
            <div className="mt-4 min-h-0 space-y-4 overflow-y-auto">
              {editedPages.map((page, index) => (
                <article
                  key={`${index}-${page.length}`}
                  className="mx-auto aspect-210/297 w-full max-w-170 overflow-y-auto bg-white p-5 shadow-sm sm:p-8"
                >
                  <p className="whitespace-pre-wrap wrap-break-word font-serif text-sm leading-6 text-slate-800">
                    {page}
                  </p>
                  <p className="mt-4 text-right text-[10px] text-slate-400">
                    {index + 1} / {editedPages.length}
                  </p>
                </article>
              ))}
            </div>
          </Dialog.Content>
        </Dialog.Portal>
      </Dialog.Root>

      <Dialog.Root open={isTextEditorOpen} onOpenChange={setIsTextEditorOpen}>
        <Dialog.Portal>
          <Dialog.Overlay className="fixed inset-0 z-40 bg-slate-950/55" />
          <Dialog.Content className="fixed left-1/2 top-1/2 z-50 flex max-h-[90dvh] w-[calc(100vw-2rem)] max-w-3xl -translate-x-1/2 -translate-y-1/2 flex-col overflow-hidden rounded-lg border border-slate-200 bg-white p-5 shadow-2xl focus:outline-none sm:p-7">
            <header className="flex items-start justify-between gap-4">
              <div>
                <Dialog.Title className="text-lg font-bold">
                  Editar documento
                </Dialog.Title>
                <Dialog.Description className="mt-1 text-sm text-slate-600">
                  Los cambios se reflejan en el visor y se guardan al pulsar
                  “Guardar cambios”.
                </Dialog.Description>
              </div>
              <Dialog.Close asChild>
                <Button
                  variant="ghost"
                  aria-label="Cerrar editor de texto"
                  className="size-9 shrink-0 p-0"
                >
                  <X aria-hidden="true" className="size-4" />
                </Button>
              </Dialog.Close>
            </header>
            <label htmlFor="document-content" className="sr-only">
              Contenido del documento en edición
            </label>
            <textarea
              id="document-content"
              value={textDraft}
              onChange={(event) => setTextDraft(event.currentTarget.value)}
              className="mt-4 min-h-64 w-full flex-1 resize-y rounded-md border border-slate-300 p-3 font-serif text-sm leading-6 text-slate-800 outline-none focus-visible:border-blue-600 focus-visible:ring-2 focus-visible:ring-blue-100 sm:min-h-96"
            />
            <div className="mt-4 flex justify-end gap-2">
              <Button
                variant="outline"
                onClick={() => setIsTextEditorOpen(false)}
              >
                Cancelar
              </Button>
              <Button variant="primary" onClick={handleTextDraftSave}>
                <CheckCircle2 aria-hidden="true" className="size-4" />
                Aplicar texto
              </Button>
            </div>
          </Dialog.Content>
        </Dialog.Portal>
      </Dialog.Root>

      <ExportModal
        isOpen={isExportModalOpen}
        onClose={() => setIsExportModalOpen(false)}
        onDownloadPdf={handleDownloadPdf}
        onSaveToApp={() => {
          handleSaveChanges();
          setIsExportModalOpen(false);
        }}
      />
    </main>
  );
}

function DocumentPanel({
  title,
  zoom,
  onZoomChange,
  action,
  children,
}: {
  title: string;
  zoom: number;
  onZoomChange: (zoom: number) => void;
  action?: React.ReactNode;
  children: React.ReactNode;
}) {
  return (
    <section className="flex min-h-72 min-w-0 flex-col overflow-hidden rounded-md border border-slate-200 bg-white lg:min-h-0">
      <header className="flex min-h-11 items-center justify-between gap-2 border-b border-slate-200 bg-white px-2.5 sm:px-3">
        <h2 className="truncate text-xs font-semibold text-slate-700 sm:text-sm">
          {title}
        </h2>
        <div className="flex shrink-0 items-center gap-1">
          {action}
          <Button
            variant="outline"
            aria-label={`Alejar ${title.toLowerCase()}`}
            title="Alejar"
            disabled={zoom <= 70}
            onClick={() => onZoomChange(Math.max(70, zoom - 10))}
            className="size-7 p-0"
          >
            <Minus aria-hidden="true" className="size-3.5" />
          </Button>
          <span className="min-w-10 text-center text-[11px] font-medium tabular-nums text-slate-600">
            {zoom}%
          </span>
          <Button
            variant="outline"
            aria-label={`Acercar ${title.toLowerCase()}`}
            title="Acercar"
            disabled={zoom >= 150}
            onClick={() => onZoomChange(Math.min(150, zoom + 10))}
            className="size-7 p-0"
          >
            <Plus aria-hidden="true" className="size-3.5" />
          </Button>
        </div>
      </header>
      <div className="min-h-0 flex-1 overflow-auto bg-slate-100/70 p-2 sm:p-3">
        <article className="mx-auto aspect-210/297 w-full max-w-170 overflow-y-auto bg-white p-3 shadow-sm sm:p-5">
          <p
            className="whitespace-pre-wrap wrap-break-word font-serif text-slate-800"
            style={{
              fontSize: `${12 * (zoom / 100)}px`,
              lineHeight: 1.55,
            }}
          >
            {children}
          </p>
        </article>
      </div>
    </section>
  );
}
