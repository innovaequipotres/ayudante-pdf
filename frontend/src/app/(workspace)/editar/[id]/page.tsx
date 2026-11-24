"use client";

import {
  useEffect,
  useRef,
  useState,
  type ClipboardEvent,
  type KeyboardEvent,
} from "react";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import * as Dialog from "@radix-ui/react-dialog";
import DOMPurify from "dompurify";
import html2canvas from "html2canvas";
import { jsPDF } from "jspdf";
import {
  ArrowLeft,
  CheckCircle2,
  ChevronRight,
  Download,
  Eye,
  FileText,
  Minus,
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
import { useLumiStore } from "@/store/useLumiStore";
import { USE_MOCKS } from "@/services";
import type { Barrier, LumiDocument } from "@/types";
import type { AdaptationType, Category, ExportEdit } from "@/services";

const PDF_PAGE_WIDTH = 794;
const PDF_PAGE_HEIGHT = 1123;
const RICH_TEXT_ALLOWED_TAGS = [
  "a",
  "b",
  "blockquote",
  "br",
  "caption",
  "dd",
  "div",
  "dl",
  "dt",
  "em",
  "figcaption",
  "figure",
  "h1",
  "h2",
  "h3",
  "h4",
  "hr",
  "img",
  "i",
  "li",
  "mark",
  "ol",
  "p",
  "strong",
  "sub",
  "sup",
  "table",
  "tbody",
  "td",
  "th",
  "thead",
  "tr",
  "u",
  "ul",
  "s",
  "del",
  "ins",
];
const RICH_TEXT_ALLOWED_ATTR = [
  "alt",
  "colspan",
  "height",
  "href",
  "rel",
  "rowspan",
  "src",
  "target",
  "title",
  "width",
];

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

function sanitizeDocumentHtml(dirtyHtml: string): string {
  const cleanHtml = DOMPurify.sanitize(dirtyHtml, {
    ALLOWED_TAGS: RICH_TEXT_ALLOWED_TAGS,
    ALLOWED_ATTR: RICH_TEXT_ALLOWED_ATTR,
    ALLOW_DATA_ATTR: false,
  });
  const template = document.createElement("template");

  template.innerHTML = cleanHtml;
  template.content.querySelectorAll("img").forEach((image) => {
    const source = image.getAttribute("src") ?? "";

    if (!source.startsWith("/demo-pdfs/") || source.startsWith("//")) {
      image.remove();
    }
  });

  return template.innerHTML;
}

function getPlainTextFromHtml(html: string): string {
  const template = document.createElement("template");
  template.innerHTML = sanitizeDocumentHtml(html);
  return template.content.textContent ?? "";
}

function replaceTextInHtml(
  html: string,
  fragment: string,
  replacement: string,
): string | null {
  const pattern = createFlexiblePattern(fragment);

  if (!pattern) {
    return null;
  }

  const template = document.createElement("template");
  template.innerHTML = sanitizeDocumentHtml(html);
  const walker = document.createTreeWalker(
    template.content,
    NodeFilter.SHOW_TEXT,
  );
  let node = walker.nextNode();

  while (node) {
    const text = node.textContent ?? "";
    const updatedText = text.replace(pattern, replacement);

    if (updatedText !== text) {
      node.textContent = updatedText;
      return template.innerHTML;
    }

    node = walker.nextNode();
  }

  return null;
}

function containsFlexibleText(html: string, value: string): boolean {
  const pattern = createFlexiblePattern(value);
  return pattern ? pattern.test(getPlainTextFromHtml(html)) : false;
}

const NOT_ADAPTABLE_RULES = new Set(["no_headings", "heading_skip"]);

const ADAPTATION_TYPE_BY_RULE: Record<string, AdaptationType> = {
  long_paragraph: "simplify",
  long_sentence: "simplify",
  dense_section: "simplify",
  undefined_term: "simplify",
  ambiguous_instruction: "clarify",
  image_without_alt: "alt_text",
  visual_reference: "describe",
  image_only_page: "describe",
  unclear_sequence: "sequence",
};

function getAdaptationType(barrier: Barrier): AdaptationType {
  if (barrier.ruleId && ADAPTATION_TYPE_BY_RULE[barrier.ruleId]) {
    return ADAPTATION_TYPE_BY_RULE[barrier.ruleId];
  }

  return barrier.category === "multimedia" ? "alt_text" : "simplify";
}

function canAdaptBarrier(barrier: Barrier): boolean {
  return !barrier.ruleId || !NOT_ADAPTABLE_RULES.has(barrier.ruleId);
}

function buildExportEdits(barriers: Barrier[]): ExportEdit[] {
  return barriers
    .filter(
      (b) =>
        b.status === "Aplicada" &&
        Boolean(b.blockId) &&
        b.suggestion.trim().length > 0,
    )
    .map((b) => ({
      block_id: b.blockId!,
      text: b.suggestion.trim(),
    }));
}

export default function EditarDocumentoPage() {
  const { id } = useParams<{ id: string }>();
  const document = useLumiStore((state) =>
    state.documents.find((item) => item.id === id),
  );
  const diagnostic = useLumiStore((state) =>
    state.diagnostics.find((item) => item.documentId === id),
  );
  const activeFileUrl = useLumiStore((state) => state.activeFileUrl);
  const setActiveDocument = useLumiStore((state) => state.setActiveDocument);
  const saveDocumentEdits = useLumiStore((state) => state.saveDocumentEdits);
  const currentSessionId = useLumiStore((state) => state.currentSessionId);
  const exportDocument = useLumiStore((state) => state.exportDocument);

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
          <h1 className="page-title mt-4">No encontramos este documento</h1>
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
      activeFileUrl={activeFileUrl}
      initialBarriers={diagnostic?.barriers ?? []}
      saveDocumentEdits={saveDocumentEdits}
      currentSessionId={currentSessionId}
      exportDocument={exportDocument}
    />
  );
}

function EditorWorkspace({
  document,
  activeFileUrl,
  initialBarriers,
  saveDocumentEdits,
  currentSessionId,
  exportDocument,
}: {
  document: LumiDocument;
  activeFileUrl: string | null;
  initialBarriers: Barrier[];
  saveDocumentEdits: (
    id: string,
    modifiedContent: string,
    barriers: Barrier[],
  ) => void;
  currentSessionId: string | null;
  exportDocument: (sessionId: string, edits: ExportEdit[]) => Promise<Blob>;
}) {
  const [editorInitialHtml] = useState(document.modifiedContent);
  const router = useRouter();
  const editorRef = useRef<HTMLDivElement>(null);
  const [editedContent, setEditedContent] = useState(editorInitialHtml);
  const [barriers, setBarriers] = useState(() =>
    cloneBarriers(initialBarriers),
  );
  const [savedContent, setSavedContent] = useState(editorInitialHtml);
  const [savedBarriers, setSavedBarriers] = useState(() =>
    cloneBarriers(initialBarriers),
  );
  const [undoStack, setUndoStack] = useState<EditorSnapshot[]>([]);
  const [redoStack, setRedoStack] = useState<EditorSnapshot[]>([]);
  const [editedZoom, setEditedZoom] = useState(100);
  const [isPreviewOpen, setIsPreviewOpen] = useState(false);
  const [isExportModalOpen, setIsExportModalOpen] = useState(false);
  const [isGeneratingPdf, setIsGeneratingPdf] = useState(false);
  const [pdfPreviewUrl, setPdfPreviewUrl] = useState<string | null>(null);
  const [pdfPreviewPageCount, setPdfPreviewPageCount] = useState(0);
  const [notice, setNotice] = useState("");
  const [adaptingBarrierId, setAdaptingBarrierId] = useState<string | null>(
    null,
  );
  const [savedName, setSavedName] = useState(document.name);
  const [isEditingName, setIsEditingName] = useState(false);
  const [draftName, setDraftName] = useState(document.name);
  const pdfContentRef = useRef<HTMLDivElement>(null);
  const nameInputRef = useRef<HTMLInputElement>(null);
  const nameEditCancelledRef = useRef(false);
  const adaptBarrier = useLumiStore((state) => state.adaptBarrier);
  const renameDocument = useLumiStore((state) => state.renameDocument);
  const folders = useLumiStore((state) => state.folders);
  const allDocuments = useLumiStore((state) => state.documents);
  const createFolder = useLumiStore((state) => state.createFolder);
  const saveDocumentToFolder = useLumiStore(
    (state) => state.saveDocumentToFolder,
  );

  const visibleBarriers = barriers.filter(
    (barrier) => barrier.status !== "Ignorada",
  );
  const pendingBarriers = barriers.filter(
    (barrier) => barrier.status === "Pendiente",
  );
  const totalErrors = initialBarriers.length;
  const pendingErrors = pendingBarriers.length;
  const folderCounts = folders.reduce<Record<string, number>>(
    (counts, folder) => {
      counts[folder.id] = allDocuments.filter(
        (item) => item.folderId === folder.id,
      ).length;
      return counts;
    },
    {},
  );
  const isDirty =
    editedContent !== savedContent ||
    document.name !== savedName ||
    JSON.stringify(barriers) !== JSON.stringify(savedBarriers);

  useEffect(() => {
    return () => {
      if (pdfPreviewUrl) {
        URL.revokeObjectURL(pdfPreviewUrl);
      }
    };
  }, [pdfPreviewUrl]);

  useEffect(() => {
    if (!isEditingName) {
      return;
    }

    nameInputRef.current?.focus();
    nameInputRef.current?.select();
  }, [isEditingName]);

  function startEditingName() {
    nameEditCancelledRef.current = false;
    setDraftName(document.name);
    setIsEditingName(true);
  }

  function commitNameEdit() {
    const nextName = draftName.trim();

    if (!nextName || nextName === document.name) {
      setDraftName(document.name);
      setIsEditingName(false);
      return;
    }

    renameDocument(document.id, nextName);
    setIsEditingName(false);
    setNotice("Se actualizó el nombre del documento.");
  }

  function handleNameBlur() {
    if (nameEditCancelledRef.current) {
      nameEditCancelledRef.current = false;
      setDraftName(document.name);
      setIsEditingName(false);
      return;
    }

    commitNameEdit();
  }

  function handleNameKeyDown(event: KeyboardEvent<HTMLInputElement>) {
    if (event.key === "Enter") {
      event.preventDefault();
      event.currentTarget.blur();
    } else if (event.key === "Escape") {
      event.preventDefault();
      nameEditCancelledRef.current = true;
      event.currentTarget.blur();
    }
  }

  function getCurrentEditorHtml() {
    return sanitizeDocumentHtml(editorRef.current?.innerHTML ?? editedContent);
  }

  function setEditorHtml(html: string) {
    const safeHtml = sanitizeDocumentHtml(html);

    if (editorRef.current && editorRef.current.innerHTML !== safeHtml) {
      editorRef.current.innerHTML = safeHtml;
    }

    setEditedContent(safeHtml);
    return safeHtml;
  }

  function syncEditorContentFromDom() {
    const editorHtml = editorRef.current?.innerHTML;

    if (editorHtml === undefined) {
      return editedContent;
    }

    const safeHtml = sanitizeDocumentHtml(editorHtml);

    if (editorHtml !== safeHtml && editorRef.current) {
      editorRef.current.innerHTML = safeHtml;
    }

    setEditedContent(safeHtml);
    return safeHtml;
  }

  function handleEditorPaste(event: ClipboardEvent<HTMLDivElement>) {
    event.preventDefault();

    const editor = editorRef.current;
    if (!editor) return;

    const clipboardHtml = event.clipboardData.getData("text/html");
    const clipboardText = event.clipboardData.getData("text/plain");
    const pastedHtml = clipboardHtml
      ? sanitizeDocumentHtml(clipboardHtml)
      : clipboardText
          .split(/\r?\n/)
          .map((line) => {
            const paragraph = window.document.createElement("p");
            paragraph.textContent = line;
            return paragraph.outerHTML;
          })
          .join("");
    const template = window.document.createElement("template");
    template.innerHTML = pastedHtml;

    const selection = window.getSelection();
    const range = selection?.rangeCount
      ? selection.getRangeAt(0)
      : window.document.createRange();

    if (!editor.contains(range.commonAncestorContainer)) {
      range.selectNodeContents(editor);
      range.collapse(false);
    }

    range.deleteContents();
    const lastInsertedNode = template.content.lastChild;
    range.insertNode(template.content);

    if (lastInsertedNode?.parentNode) {
      range.setStartAfter(lastInsertedNode);
    }

    range.collapse(true);
    selection?.removeAllRanges();
    selection?.addRange(range);
    syncEditorContentFromDom();
  }

  function saveSnapshot(content = getCurrentEditorHtml()) {
    setUndoStack((previous) => [
      ...previous,
      { content, barriers: cloneBarriers(barriers) },
    ]);
    setRedoStack([]);
  }

  function handleApply(barrier: Barrier, acceptedSuggestion: string) {
    if (barrier.status === "Aplicada") {
      return;
    }

    const currentContent = syncEditorContentFromDom();
    const nextContent = replaceTextInHtml(
      currentContent,
      barrier.originalText ?? barrier.detectedFragment,
      acceptedSuggestion,
    );
    const alreadyPresent = containsFlexibleText(
      currentContent,
      acceptedSuggestion,
    );

    if (nextContent === null && !alreadyPresent) {
      setNotice(
        `No se encontró el fragmento detectado en ${document.name}. No se aplicaron cambios.`,
      );
      return;
    }

    saveSnapshot(currentContent);

    if (nextContent !== null) {
      setEditorHtml(nextContent);
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

    saveSnapshot(getCurrentEditorHtml());
    setBarriers((previous) =>
      previous.map((item) =>
        item.id === barrier.id ? { ...item, status: "Ignorada" } : item,
      ),
    );
    setNotice("Se descartó la sugerencia.");
  }

  async function handleGenerateSuggestion(barrier: Barrier) {
    if (USE_MOCKS) {
      setNotice("La generación con IA requiere el backend real.");
      return;
    }

    if (!canAdaptBarrier(barrier)) {
      setNotice(
        "Esta barrera requiere un cambio de estructura, no una reescritura de texto.",
      );
      return;
    }

    const originalText = (
      barrier.originalText ?? barrier.detectedFragment
    ).trim();

    if (!originalText) {
      setNotice("No hay texto original para generar la sugerencia.");
      return;
    }

    setAdaptingBarrierId(barrier.id);
    setNotice("");

    try {
      const adaptation = await adaptBarrier({
        type: getAdaptationType(barrier),
        original_text: originalText,
        rule_id: barrier.ruleId ?? null,
        category: (barrier.category as Category | null) ?? null,
        title: barrier.title ?? null,
        detail: barrier.detail ?? null,
        recommendation: barrier.recommendation ?? null,
      });
      const adaptedText = adaptation.adapted_text?.trim();

      if (!adaptedText) {
        setNotice(
          adaptation.notes ??
            "No se pudo generar el texto adaptado. Escribilo manualmente.",
        );
        return;
      }

      setBarriers((previous) =>
        previous.map((item) =>
          item.id === barrier.id
            ? {
                ...item,
                suggestion: adaptedText,
                adaptationNotes: adaptation.notes,
              }
            : item,
        ),
      );
      setNotice(
        adaptation.source === "local"
          ? "Se generó una propuesta sin IA. Revisala antes de aplicarla."
          : "Se generó una sugerencia con IA.",
      );
    } catch (error) {
      setNotice(
        error instanceof Error
          ? error.message
          : "No se pudo generar la sugerencia.",
      );
    } finally {
      setAdaptingBarrierId(null);
    }
  }

  function handleUndo() {
    const previousSnapshot = undoStack.at(-1);

    if (!previousSnapshot) {
      return;
    }

    setRedoStack((previous) => [
      ...previous,
      { content: getCurrentEditorHtml(), barriers: cloneBarriers(barriers) },
    ]);
    setEditorHtml(previousSnapshot.content);
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
      { content: getCurrentEditorHtml(), barriers: cloneBarriers(barriers) },
    ]);
    setEditorHtml(nextSnapshot.content);
    setBarriers(cloneBarriers(nextSnapshot.barriers));
    setRedoStack((previous) => previous.slice(0, -1));
    setNotice("Se rehizo el cambio.");
  }

  function handleSaveChanges() {
    const currentContent = syncEditorContentFromDom();
    saveDocumentEdits(document.id, currentContent, cloneBarriers(barriers));
    setSavedContent(currentContent);
    setSavedBarriers(cloneBarriers(barriers));
    setSavedName(document.name);
    setNotice("Se guardaron los cambios en esta sesión.");
  }

  function handleSaveToFolder(name: string, folderId: string | null) {
    const currentContent = syncEditorContentFromDom();
    const currentBarriers = cloneBarriers(barriers);

    saveDocumentEdits(document.id, currentContent, currentBarriers);
    saveDocumentToFolder(document.id, name, folderId);
    setSavedContent(currentContent);
    setSavedBarriers(currentBarriers);
    setSavedName(name);
    setIsExportModalOpen(false);
    setNotice(`Se guardó "${name}" en Mis archivos.`);
    router.push(
      folderId
        ? `/archivos?folderId=${encodeURIComponent(folderId)}`
        : "/archivos",
    );
  }

  async function handleDownloadPDF(
    action: "download" | "preview" = "download",
  ) {
    setIsGeneratingPdf(true);
    setNotice("");

    try {
      const sessionId = currentSessionId;
      const edits = buildExportEdits(barriers);

      if (!USE_MOCKS && sessionId && edits.length > 0) {
        const pdfBlob = await exportDocument(sessionId, edits);
        const pdfUrl = URL.createObjectURL(pdfBlob);

        if (action === "download") {
          const a = window.document.createElement("a");
          a.href = pdfUrl;
          a.download = `${document.name.replace(/\.pdf$/i, "")}_adaptado.pdf`;
          a.click();
          URL.revokeObjectURL(pdfUrl);
          setIsExportModalOpen(false);
          setNotice("Se generó el PDF adaptado desde el backend.");
        } else {
          setPdfPreviewUrl(pdfUrl);
          setIsPreviewOpen(true);
        }
        return;
      }

      await generatePdfWithJsPDF(action);
    } catch (error) {
      console.error("No se pudo generar el PDF:", error);
      if (!USE_MOCKS) {
        try {
          await generatePdfWithJsPDF(action);
        } catch {
          setNotice("No se pudo generar el PDF. Volvé a intentarlo.");
        }
      } else {
        setNotice("No se pudo generar el PDF. Volvé a intentarlo.");
      }
    } finally {
      setIsGeneratingPdf(false);
    }
  }

  async function generatePdfWithJsPDF(
    action: "download" | "preview" = "download",
  ) {
    const exportContainer = pdfContentRef.current;
    if (!exportContainer) {
      throw new Error("No hay contenido disponible para exportar.");
    }

    const currentContent = syncEditorContentFromDom();
    const exportContent = exportContainer.querySelector<HTMLElement>(
      "[data-pdf-document]",
    );

    if (!exportContent) {
      throw new Error("No hay contenido disponible para exportar.");
    }

    exportContent.innerHTML = currentContent;

    const images = Array.from(exportContainer.querySelectorAll("img"));
    await Promise.all(
      images.map(
        (image) =>
          new Promise<void>((resolve) => {
            if (image.complete) {
              resolve();
            } else {
              image.addEventListener("load", () => resolve(), { once: true });
              image.addEventListener("error", () => resolve(), {
                once: true,
              });
            }
          }),
      ),
    );

    const pageCount = Math.max(
      1,
      Math.ceil(exportContainer.scrollHeight / PDF_PAGE_HEIGHT),
    );

    const pdf = new jsPDF({
      orientation: "portrait",
      unit: "mm",
      format: "a4",
    });
    const pageWidth = pdf.internal.pageSize.getWidth();
    const pageHeight = pdf.internal.pageSize.getHeight();

    for (let index = 0; index < pageCount; index += 1) {
      const canvas = await html2canvas(exportContainer, {
        scale: 2,
        useCORS: true,
        backgroundColor: "#ffffff",
        logging: false,
        x: 0,
        y: index * PDF_PAGE_HEIGHT,
        width: PDF_PAGE_WIDTH,
        height: PDF_PAGE_HEIGHT,
        windowWidth: PDF_PAGE_WIDTH,
        windowHeight: PDF_PAGE_HEIGHT,
        scrollX: 0,
        scrollY: 0,
        onclone: (clonedDocument) => {
          const clonedContent = clonedDocument.querySelector<HTMLElement>(
            "[data-pdf-document]",
          );

          clonedContent
            ?.querySelectorAll<HTMLElement>("*")
            .forEach((element) => {
              element.style.color = "#1e293b";
              element.style.fontFamily = "Georgia, serif";
              element.style.lineHeight = "1.5";

              if (element.tagName === "H1") {
                element.style.fontSize = "28px";
                element.style.fontWeight = "700";
                element.style.margin = "0 0 20px";
              } else if (element.tagName === "H2") {
                element.style.fontSize = "21px";
                element.style.fontWeight = "700";
                element.style.margin = "24px 0 12px";
              } else if (element.tagName === "H3") {
                element.style.fontSize = "17px";
                element.style.fontWeight = "700";
                element.style.margin = "20px 0 10px";
              } else if (element.tagName === "P" || element.tagName === "LI") {
                element.style.fontSize = "14px";
                element.style.margin = "0 0 12px";
              } else if (element.tagName === "UL" || element.tagName === "OL") {
                element.style.paddingLeft = "24px";
                element.style.margin = "0 0 16px";
              } else if (element.tagName === "FIGURE") {
                element.style.margin = "24px 0";
              } else if (element.tagName === "IMG") {
                element.style.display = "block";
                element.style.height = "auto";
                element.style.margin = "16px auto";
                element.style.maxWidth = "100%";
              } else if (element.tagName === "FIGCAPTION") {
                element.style.color = "#475569";
                element.style.fontSize = "12px";
                element.style.textAlign = "center";
              }
            });
        },
      });
      const image = canvas.toDataURL("image/png");

      if (index > 0) {
        pdf.addPage("a4", "portrait");
      }

      pdf.addImage(image, "PNG", 0, 0, pageWidth, pageHeight);
      canvas.width = 0;
      canvas.height = 0;
    }

    setPdfPreviewPageCount(pageCount);

    if (action === "download") {
      pdf.save(`${document.name.replace(/\.pdf$/i, "")}_adaptado.pdf`);
      setIsExportModalOpen(false);
      setNotice("Se generó el PDF del documento editado (fallback local).");
    } else {
      setPdfPreviewUrl(URL.createObjectURL(pdf.output("blob")));
      setIsPreviewOpen(true);
    }
  }

  const documentStatus = isDirty ? "Sin guardar" : document.status;

  return (
    <main className="flex min-h-[calc(100svh-5rem)] flex-col bg-slate-100 pb-14 text-slate-900 lg:h-[calc(100svh-5rem)] lg:min-h-0">
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto grid w-full max-w-7xl gap-3 px-4 py-3 sm:px-6 lg:grid-cols-[minmax(0,1fr)_auto] lg:items-center">
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
              <h1 className="page-title min-w-0 truncate">
                {isEditingName ? (
                  <input
                    ref={nameInputRef}
                    value={draftName}
                    onChange={(event) => setDraftName(event.target.value)}
                    onBlur={handleNameBlur}
                    onKeyDown={handleNameKeyDown}
                    aria-label="Nombre del documento"
                    className="page-title w-full min-w-0 rounded border border-blue-400 bg-white px-1 py-0 outline-none ring-2 ring-blue-100"
                  />
                ) : (
                  <button
                    type="button"
                    title="Hacé clic para renombrar"
                    onClick={startEditingName}
                    className="-mx-1 block max-w-full cursor-pointer truncate rounded px-1 text-left transition hover:bg-slate-100 hover:ring-1 hover:ring-slate-200 focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:outline-none"
                  >
                    {document.name}
                  </button>
                )}
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

          <div className="flex flex-wrap items-center justify-end gap-2">
            <Button
              variant="outline"
              onClick={() => void handleDownloadPDF("download")}
              disabled={isGeneratingPdf}
              className="min-h-9 px-3 py-2 text-xs sm:text-sm"
            >
              <Download aria-hidden="true" className="size-4" />
              {isGeneratingPdf ? "Generando PDF..." : "Descargar PDF"}
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

      <div className="mx-auto flex min-h-0 w-full max-w-7xl flex-1 flex-col px-2 py-2 sm:px-3 sm:py-3 lg:px-6">
        <div className="grid min-h-[70svh] flex-1 grid-cols-1 gap-3 xl:h-[calc(100svh-16rem)] xl:min-h-120 xl:grid-cols-[minmax(18rem,0.33fr)_minmax(0,0.67fr)]">
          <aside className="flex min-h-0 min-w-0 flex-col overflow-hidden rounded-md border border-slate-200 bg-white">
            <header className="border-b border-slate-200 p-3 sm:p-4">
              <div
                role="status"
                className={`flex items-start gap-2.5 rounded-md p-3 ${
                  pendingErrors === 0 ? "bg-emerald-50" : "bg-red-50"
                }`}
              >
                <span
                  className={`mt-0.5 grid size-6 shrink-0 place-items-center rounded-full text-white ${
                    pendingErrors === 0 ? "bg-emerald-600" : "bg-red-600"
                  }`}
                >
                  {pendingErrors === 0 ? (
                    <CheckCircle2 aria-hidden="true" className="size-4" />
                  ) : (
                    <span aria-hidden="true" className="text-sm font-bold">
                      !
                    </span>
                  )}
                </span>
                <div className="min-w-0">
                  <h2
                    className={`text-sm font-bold ${
                      pendingErrors === 0 ? "text-emerald-900" : "text-red-900"
                    }`}
                  >
                    {pendingErrors === 0
                      ? totalErrors === 0
                        ? "No se detectaron errores en este documento."
                        : `¡Revisaste los ${totalErrors} errores detectados!`
                      : `Se detectaron ${pendingErrors}/${totalErrors} errores que requieren revisión`}
                  </h2>
                  <p className="mt-1 text-xs leading-5 text-slate-600">
                    {pendingErrors === 0
                      ? "El documento está listo para guardar o descargar."
                      : "Revisá cada sugerencia y decidí si querés aplicarla al documento."}
                  </p>
                </div>
              </div>
              <div
                className="mt-3 flex flex-wrap gap-2"
                aria-label="Resumen por severidad"
              >
                {(["Alta", "Media", "Baja"] as const).map((severity) => {
                  const count = pendingBarriers.filter(
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
                    onGenerateSuggestion={handleGenerateSuggestion}
                    isAdapting={adaptingBarrierId === barrier.id}
                    canAdapt={canAdaptBarrier(barrier)}
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
            className="grid min-h-0 min-w-0 grid-cols-1 gap-2 xl:grid-cols-2"
          >
            <DocumentPanel title="Documento original" isPdfViewer>
              {activeFileUrl ? (
                <iframe
                  src={activeFileUrl}
                  width="100%"
                  height="100%"
                  title={`PDF original: ${document.name}`}
                  className="border-0 rounded-lg shadow-inner"
                />
              ) : (
                <div className="flex h-full flex-col items-center justify-center gap-2 px-4 text-center">
                  <p className="text-sm font-semibold text-slate-800">
                    El PDF original ya no está disponible en esta sesión.
                  </p>
                  <Link
                    href="/inicio"
                    className="text-sm font-semibold text-blue-700 underline underline-offset-2 hover:text-blue-900"
                  >
                    Volver a Inicio
                  </Link>
                </div>
              )}
            </DocumentPanel>

            <DocumentPanel
              title="Documento en edición"
              zoom={editedZoom}
              onZoomChange={setEditedZoom}
              richText
            >
              <div
                ref={editorRef}
                contentEditable={true}
                suppressContentEditableWarning={true}
                role="textbox"
                aria-label="Contenido del documento en edición"
                aria-multiline="true"
                spellCheck={true}
                onInput={syncEditorContentFromDom}
                onBlur={syncEditorContentFromDom}
                onPaste={handleEditorPaste}
                onDrop={(event) => event.preventDefault()}
                dangerouslySetInnerHTML={{ __html: editorInitialHtml }}
                className="prose prose-slate max-w-none focus:outline-none min-h-200 w-full bg-white p-8 md:p-12 shadow-lg"
                style={{ zoom: editedZoom / 100 }}
              />
            </DocumentPanel>
          </section>
        </div>
      </div>

      <div
        ref={pdfContentRef}
        aria-hidden="true"
        className="pointer-events-none fixed left-[-10000px] top-0"
        style={{
          backgroundColor: "#ffffff",
          boxSizing: "border-box",
          color: "#1e293b",
          padding: "72px",
          width: `${PDF_PAGE_WIDTH}px`,
        }}
      >
        <div
          data-pdf-document
          dangerouslySetInnerHTML={{ __html: editedContent }}
        />
      </div>

      <footer className="fixed inset-x-0 bottom-0 z-30 border-t border-slate-200 bg-white/95 shadow-[0_-8px_24px_rgba(15,23,42,0.06)] backdrop-blur">
        <div className="mx-auto flex w-full max-w-7xl flex-wrap items-center justify-between gap-2 px-4 py-2 sm:px-6">
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
              onClick={() => void handleDownloadPDF("preview")}
              disabled={isGeneratingPdf}
              className="min-h-9 px-2.5 text-xs sm:text-sm"
            >
              <Eye aria-hidden="true" className="size-4" />
              {isGeneratingPdf ? "Generando PDF..." : "Vista previa"}
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

      <Dialog.Root
        open={isPreviewOpen}
        onOpenChange={(open) => {
          setIsPreviewOpen(open);
          if (!open) setPdfPreviewUrl(null);
        }}
      >
        <Dialog.Portal>
          <Dialog.Overlay className="fixed inset-0 z-40 bg-slate-950/55" />
          <Dialog.Content className="fixed left-1/2 top-1/2 z-50 flex h-[80dvh] max-h-[90dvh] w-[calc(100vw-2rem)] max-w-4xl -translate-x-1/2 -translate-y-1/2 flex-col overflow-hidden rounded-lg border border-slate-200 bg-slate-100 p-4 shadow-2xl focus:outline-none sm:p-6">
            <header className="flex items-start justify-between gap-4">
              <div>
                <Dialog.Title className="text-lg font-bold">
                  Vista previa
                </Dialog.Title>
                <Dialog.Description className="mt-1 text-sm text-slate-600">
                  {document.name} · {pdfPreviewPageCount} páginas
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
            <iframe
              src={pdfPreviewUrl ?? undefined}
              title={`Vista previa del PDF: ${document.name}`}
              className="mt-4 min-h-0 w-full flex-1 rounded border-0 bg-white"
            />
          </Dialog.Content>
        </Dialog.Portal>
      </Dialog.Root>

      {isExportModalOpen && (
        <ExportModal
          isOpen
          onClose={() => setIsExportModalOpen(false)}
          onDownloadPdf={() => void handleDownloadPDF("download")}
          isGeneratingPdf={isGeneratingPdf}
          onSaveToApp={handleSaveToFolder}
          onCreateFolder={(name) => createFolder({ name })}
          documentName={document.name}
          initialFolderId={document.folderId}
          folders={folders}
          folderCounts={folderCounts}
        />
      )}
    </main>
  );
}

function DocumentPanel({
  title,
  zoom,
  onZoomChange,
  action,
  isPdfViewer = false,
  richText = false,
  children,
}: {
  title: string;
  zoom?: number;
  onZoomChange?: (zoom: number) => void;
  action?: React.ReactNode;
  isPdfViewer?: boolean;
  richText?: boolean;
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
          {zoom !== undefined && onZoomChange && (
            <>
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
            </>
          )}
        </div>
      </header>
      <div
        className={`min-h-0 flex-1 ${
          isPdfViewer
            ? "overflow-hidden"
            : "overflow-auto bg-slate-100/70 p-2 sm:p-3"
        }`}
      >
        {isPdfViewer || richText ? (
          children
        ) : (
          <article className="mx-auto aspect-210/297 w-full max-w-170 overflow-y-auto bg-white p-3 shadow-sm sm:p-5">
            <p
              className="whitespace-pre-wrap wrap-break-word font-serif text-slate-800"
              style={{
                fontSize: `${12 * ((zoom ?? 100) / 100)}px`,
                lineHeight: 1.55,
              }}
            >
              {children}
            </p>
          </article>
        )}
      </div>
    </section>
  );
}
