
"use client";

import { useState, type ReactNode } from "react";
import {
  ArrowLeft,
  Check,
  CheckCircle2,
  ChevronDown,
  ChevronUp,
  CircleAlert,
  FileText,
  History,
  Lightbulb,
  Pencil,
  RotateCcw,
  RotateCw,
  Save,
  Sparkles,
  X,
} from "lucide-react";

type Category = "claridad" | "organizacion" | "estructura";
type SuggestionStatus = "pending" | "applied" | "dismissed";

type Suggestion = {
  id: number;
  title: string;
  category: Category;
  original: string;
  replacement: string;
  explanation: string;
  status: SuggestionStatus;
};

type EditorSnapshot = {
  content: string;
  suggestions: Suggestion[];
};

type Tab = "documento" | "cambios";

const INITIAL_CONTENT = `Guía para preparar una respuesta

Para responder la consigna, leé atentamente el material y pensá qué información es importante.

Escribí una respuesta con palabras claras. Si una oración tiene muchas ideas, separala para que sea más fácil comprenderla.

Antes de entregar, revisá que tu respuesta incluya todos los puntos pedidos y presente las ideas en orden.`;

const INITIAL_SUGGESTIONS: Suggestion[] = [
  {
    id: 1,
    title: "Simplificar el lenguaje",
    category: "claridad",
    original:
      "Para responder la consigna, leé atentamente el material y pensá qué información es importante.",
    replacement:
      "Leé la consigna. Después, leé el material y elegí la información más importante.",
    explanation:
      "La propuesta divide la indicación en pasos breves y directos para facilitar su comprensión.",
    status: "pending",
  },
  {
    id: 2,
    title: "Dividir instrucciones largas",
    category: "organizacion",
    original:
      "Escribí una respuesta con palabras claras. Si una oración tiene muchas ideas, separala para que sea más fácil comprenderla.",
    replacement:
      "Escribí una respuesta clara. Usá una idea por oración. Si una oración es muy larga, dividila en dos o más oraciones.",
    explanation:
      "Las instrucciones breves ayudan a identificar qué hacer y en qué orden.",
    status: "pending",
  },
  {
    id: 3,
    title: "Mejorar la estructura",
    category: "estructura",
    original:
      "Antes de entregar, revisá que tu respuesta incluya todos los puntos pedidos y presente las ideas en orden.",
    replacement:
      "Antes de entregar, revisá que tu respuesta:\n• Incluya todos los puntos pedidos.\n• Presente las ideas en orden.\n• Sea clara y fácil de entender.",
    explanation:
      "La lista permite comprobar cada requisito por separado antes de entregar la respuesta.",
    status: "pending",
  },
];

const CATEGORY_LABELS: Record<Category, string> = {
  claridad: "Claridad",
  organizacion: "Organización",
  estructura: "Estructura",
};

const CATEGORY_STYLES: Record<Category, string> = {
  claridad: "border-red-200 bg-red-50 text-red-800",
  organizacion: "border-amber-200 bg-amber-50 text-amber-800",
  estructura: "border-emerald-200 bg-emerald-50 text-emerald-800",
};

function cloneSuggestions(suggestions: Suggestion[]): Suggestion[] {
  return suggestions.map((suggestion) => ({ ...suggestion }));
}

/**
 * Escapa los caracteres especiales para buscar texto literal.
 */
function escapeRegExp(value: string): string {
  return value.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

/**
 * Busca el texto ignorando diferencias de espacios y saltos de línea.
 */
function createFlexiblePattern(original: string): RegExp {
  const normalized = original.trim();

  const pattern = normalized
    .split(/\s+/)
    .map(escapeRegExp)
    .join("\\s+");

  return new RegExp(pattern, "g");
}

function replaceFlexibleText(
  content: string,
  original: string,
  replacement: string,
): string | null {
  if (!original.trim()) {
    return null;
  }

  const pattern = createFlexiblePattern(original);
  const updatedContent = content.replace(pattern, replacement);

  if (updatedContent === content) {
    return null;
  }

  return updatedContent;
}

function renderHighlightedContent(
  content: string,
  suggestions: Suggestion[],
): ReactNode[] {
  const matches: {
    start: number;
    end: number;
    text: string;
    category: Category;
    status: SuggestionStatus;
  }[] = [];

  for (const suggestion of suggestions) {
    if (suggestion.status === "dismissed") {
      continue;
    }

    const target =
      suggestion.status === "applied"
        ? suggestion.replacement
        : suggestion.original;

    if (!target.trim()) {
      continue;
    }

    const pattern = createFlexiblePattern(target);
    let match: RegExpExecArray | null;

    while ((match = pattern.exec(content)) !== null) {
      matches.push({
        start: match.index,
        end: match.index + match[0].length,
        text: match[0],
        category: suggestion.category,
        status: suggestion.status,
      });

      if (match[0].length === 0) {
        pattern.lastIndex++;
      }
    }
  }

  matches.sort((a, b) => a.start - b.start || b.end - a.end);

  const nonOverlappingMatches: typeof matches = [];
  let lastEnd = 0;

  for (const match of matches) {
    if (match.start < lastEnd) {
      continue;
    }

    nonOverlappingMatches.push(match);
    lastEnd = match.end;
  }

  const nodes: ReactNode[] = [];
  let cursor = 0;

  for (const match of nonOverlappingMatches) {
    if (match.start > cursor) {
      nodes.push(content.slice(cursor, match.start));
    }

    const highlightClass =
      match.status === "applied"
        ? "bg-emerald-200 text-emerald-950"
        : match.category === "claridad"
          ? "bg-red-100 text-red-950"
          : match.category === "organizacion"
            ? "bg-amber-100 text-amber-950"
            : "bg-emerald-100 text-emerald-950";

    nodes.push(
      <mark
        key={`${match.start}-${match.end}`}
        className={`rounded px-0.5 ${highlightClass}`}
        title={
          match.status === "applied"
            ? "Adaptación aplicada"
            : `Para revisar: ${CATEGORY_LABELS[match.category]}`
        }
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

export default function EditarDocumentoPage() {
  const [originalContent] = useState(INITIAL_CONTENT);
  const [content, setContent] = useState(INITIAL_CONTENT);
  const [suggestions, setSuggestions] = useState<Suggestion[]>(
    () => cloneSuggestions(INITIAL_SUGGESTIONS),
  );

  const [activeTab, setActiveTab] = useState<Tab>("documento");
  const [notice, setNotice] = useState("");
  const [editingId, setEditingId] = useState<number | null>(null);
  const [editedProposal, setEditedProposal] = useState("");

  const [undoStack, setUndoStack] = useState<EditorSnapshot[]>([]);
  const [redoStack, setRedoStack] = useState<EditorSnapshot[]>([]);

  function saveSnapshot(): void {
    setUndoStack((previous) => [
      ...previous,
      {
        content,
        suggestions: cloneSuggestions(suggestions),
      },
    ]);

    setRedoStack([]);
  }

  function updateSuggestionStatus(
    id: number,
    status: SuggestionStatus,
  ): void {
    setSuggestions((previous) =>
      previous.map((suggestion) =>
        suggestion.id === id
          ? { ...suggestion, status }
          : suggestion,
      ),
    );
  }

  function handleApply(suggestion: Suggestion): void {
    setNotice("");

    if (suggestion.status === "applied") {
      setNotice("Esta propuesta ya fue aplicada.");
      return;
    }

    /*
     * Primero se intenta reemplazar el texto original.
     * Si no aparece, se comprueba si la propuesta ya está en el documento.
     * Esto evita que la aplicación falle por espacios o saltos de línea.
     */
    const updatedContent = replaceFlexibleText(
      content,
      suggestion.original,
      suggestion.replacement,
    );

    if (updatedContent === null) {
      const replacementAlreadyExists = new RegExp(
        createFlexiblePattern(suggestion.replacement).source,
      ).test(content);

      if (replacementAlreadyExists) {
        saveSnapshot();
        updateSuggestionStatus(suggestion.id, "applied");
        setNotice("La propuesta ya estaba en el documento y quedó marcada como aplicada.");
        return;
      }

      setNotice(
        "No se encontró el texto original ni la propuesta en el documento. Revisá el contenido antes de aplicar este cambio.",
      );
      return;
    }

    saveSnapshot();
    setContent(updatedContent);
    updateSuggestionStatus(suggestion.id, "applied");
    setNotice(`Se aplicó la propuesta: ${suggestion.title}.`);
  }

  function handleDismiss(suggestion: Suggestion): void {
    saveSnapshot();
    updateSuggestionStatus(suggestion.id, "dismissed");
    setNotice(`Se descartó la propuesta: ${suggestion.title}.`);
  }

  function handleStartEditing(suggestion: Suggestion): void {
    setEditingId(suggestion.id);
    setEditedProposal(suggestion.replacement);
    setNotice("");
  }

  function handleCancelEditing(): void {
    setEditingId(null);
    setEditedProposal("");
  }

  function handleSaveProposal(suggestion: Suggestion): void {
    const trimmedProposal = editedProposal.trim();

    if (!trimmedProposal) {
      setNotice("La propuesta no puede quedar vacía.");
      return;
    }

    saveSnapshot();

    setSuggestions((previous) =>
      previous.map((item) =>
        item.id === suggestion.id
          ? { ...item, replacement: trimmedProposal }
          : item,
      ),
    );

    setEditingId(null);
    setEditedProposal("");
    setNotice("La propuesta se actualizó. Podés revisarla antes de aplicarla.");
  }

  function handleUndo(): void {
    if (undoStack.length === 0) {
      setNotice("No hay cambios para deshacer.");
      return;
    }

    const previousSnapshot = undoStack[undoStack.length - 1];

    setRedoStack((previous) => [
      ...previous,
      {
        content,
        suggestions: cloneSuggestions(suggestions),
      },
    ]);

    setContent(previousSnapshot.content);
    setSuggestions(cloneSuggestions(previousSnapshot.suggestions));
    setUndoStack((previous) => previous.slice(0, -1));
    setNotice("Se deshizo el último cambio.");
  }

  function handleRedo(): void {
    if (redoStack.length === 0) {
      setNotice("No hay cambios para rehacer.");
      return;
    }

    const nextSnapshot = redoStack[redoStack.length - 1];

    setUndoStack((previous) => [
      ...previous,
      {
        content,
        suggestions: cloneSuggestions(suggestions),
      },
    ]);

    setContent(nextSnapshot.content);
    setSuggestions(cloneSuggestions(nextSnapshot.suggestions));
    setRedoStack((previous) => previous.slice(0, -1));
    setNotice("Se rehizo el cambio.");
  }

  function handleRestoreOriginal(): void {
    if (
      content === originalContent &&
      suggestions.every(
        (suggestion, index) =>
          suggestion.status === INITIAL_SUGGESTIONS[index].status &&
          suggestion.replacement === INITIAL_SUGGESTIONS[index].replacement,
      )
    ) {
      setNotice("El documento ya está en su estado original.");
      return;
    }

    saveSnapshot();
    setContent(originalContent);
    setSuggestions(cloneSuggestions(INITIAL_SUGGESTIONS));
    setEditingId(null);
    setEditedProposal("");
    setNotice("Se restauró el documento original.");
  }

  const pendingCount = suggestions.filter(
    (suggestion) => suggestion.status === "pending",
  ).length;

  const appliedCount = suggestions.filter(
    (suggestion) => suggestion.status === "applied",
  ).length;

  const dismissedCount = suggestions.filter(
    (suggestion) => suggestion.status === "dismissed",
  ).length;

  return (
    <main className="min-h-screen bg-slate-50 text-slate-900">
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex max-w-[1500px] flex-wrap items-center justify-between gap-4 px-4 py-4 sm:px-6">
          <div className="flex items-center gap-3">
            <button
              type="button"
              onClick={() => window.history.back()}
              className="rounded-lg p-2 text-slate-600 transition hover:bg-slate-100"
              aria-label="Volver"
              title="Volver"
            >
              <ArrowLeft size={20} />
            </button>

            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-emerald-100 text-emerald-700">
              <FileText size={22} />
            </div>

            <div>
              <h1 className="text-lg font-bold sm:text-xl">
                Editar documento
              </h1>
              <p className="text-xs text-slate-500 sm:text-sm">
                Revisión de accesibilidad · Documento de demostración
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2 rounded-full border border-amber-200 bg-amber-50 px-3 py-2 text-xs font-medium text-amber-800 sm:text-sm">
            <CircleAlert size={16} />
            Edición temporal
          </div>
        </div>
      </header>

      <div className="mx-auto max-w-[1500px] px-4 py-5 sm:px-6">
        <div className="mb-5 rounded-xl border border-blue-200 bg-blue-50 p-4 text-sm leading-6 text-blue-950">
          <div className="flex items-start gap-3">
            <Lightbulb className="mt-0.5 shrink-0 text-blue-700" size={20} />
            <div>
              <p className="font-semibold">Revisá cada adaptación antes de aplicarla</p>
              <p className="mt-1">
                Las sugerencias son demostrativas. La conexión con un servicio
                de inteligencia artificial y el guardado en el servidor no
                están implementados en esta pantalla. Vos decidís qué cambios
                aceptar.
              </p>
            </div>
          </div>
        </div>

        <div className="mb-5 flex flex-wrap items-center justify-between gap-3">
          <div
            className="inline-flex rounded-xl border border-slate-200 bg-white p-1"
            role="tablist"
            aria-label="Vistas del editor"
          >
            <button
              type="button"
              role="tab"
              aria-selected={activeTab === "documento"}
              onClick={() => setActiveTab("documento")}
              className={`rounded-lg px-4 py-2 text-sm font-semibold transition ${
                activeTab === "documento"
                  ? "bg-emerald-600 text-white shadow-sm"
                  : "text-slate-600 hover:bg-slate-100"
              }`}
            >
              Vista de documento
            </button>

            <button
              type="button"
              role="tab"
              aria-selected={activeTab === "cambios"}
              onClick={() => setActiveTab("cambios")}
              className={`rounded-lg px-4 py-2 text-sm font-semibold transition ${
                activeTab === "cambios"
                  ? "bg-emerald-600 text-white shadow-sm"
                  : "text-slate-600 hover:bg-slate-100"
              }`}
            >
              Vista de cambios
            </button>
          </div>

          <div className="flex flex-wrap gap-2 text-xs sm:text-sm">
            <span className="rounded-full bg-amber-100 px-3 py-1.5 font-medium text-amber-800">
              {pendingCount} pendientes
            </span>
            <span className="rounded-full bg-emerald-100 px-3 py-1.5 font-medium text-emerald-800">
              {appliedCount} aplicadas
            </span>
            <span className="rounded-full bg-slate-200 px-3 py-1.5 font-medium text-slate-700">
              {dismissedCount} descartadas
            </span>
          </div>
        </div>

        {notice && (
          <div
            role="status"
            aria-live="polite"
            className="mb-5 flex items-start gap-3 rounded-xl border border-slate-200 bg-white p-4 text-sm text-slate-700"
          >
            <CheckCircle2
              className="mt-0.5 shrink-0 text-emerald-600"
              size={19}
            />
            <p className="flex-1">{notice}</p>
            <button
              type="button"
              onClick={() => setNotice("")}
              className="rounded p-1 text-slate-500 hover:bg-slate-100"
              aria-label="Cerrar aviso"
            >
              <X size={16} />
            </button>
          </div>
        )}

        <div className="grid items-start gap-5 xl:grid-cols-[minmax(0,1fr)_390px]">
          <section className="min-w-0 overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">
            <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-200 px-5 py-4">
              <div>
                <h2 className="font-semibold">
                  {activeTab === "documento"
                    ? "Documento de trabajo"
                    : "Resumen de cambios"}
                </h2>
                <p className="mt-1 text-sm text-slate-500">
                  {activeTab === "documento"
                    ? "Los fragmentos resaltados corresponden a las sugerencias."
                    : "Consultá qué propuestas fueron aceptadas o descartadas."}
                </p>
              </div>

              {activeTab === "documento" && (
                <div className="flex flex-wrap gap-2 text-xs">
                  <span className="inline-flex items-center gap-1.5">
                    <span className="h-3 w-3 rounded-sm bg-red-200" />
                    Claridad
                  </span>
                  <span className="inline-flex items-center gap-1.5">
                    <span className="h-3 w-3 rounded-sm bg-amber-200" />
                    Organización
                  </span>
                  <span className="inline-flex items-center gap-1.5">
                    <span className="h-3 w-3 rounded-sm bg-emerald-200" />
                    Estructura
                  </span>
                </div>
              )}
            </div>

            {activeTab === "documento" ? (
              <article className="min-h-[420px] p-5 sm:p-8">
                <div className="mx-auto max-w-3xl">
                  <div className="mb-5 flex items-center gap-2 text-xs font-medium uppercase tracking-wider text-slate-400">
                    <FileText size={15} />
                    Vista previa del contenido
                  </div>

                  <div className="whitespace-pre-wrap break-words text-base leading-8 text-slate-800">
                    {renderHighlightedContent(content, suggestions)}
                  </div>
                </div>
              </article>
            ) : (
              <div className="min-h-[420px] p-5 sm:p-8">
                <div className="space-y-4">
                  {suggestions.map((suggestion) => (
                    <div
                      key={suggestion.id}
                      className="rounded-xl border border-slate-200 p-4"
                    >
                      <div className="flex flex-wrap items-start justify-between gap-3">
                        <div>
                          <h3 className="font-semibold">{suggestion.title}</h3>
                          <p className="mt-1 text-sm text-slate-500">
                            {CATEGORY_LABELS[suggestion.category]}
                          </p>
                        </div>

                        <span
                          className={`rounded-full px-3 py-1 text-xs font-semibold ${
                            suggestion.status === "applied"
                              ? "bg-emerald-100 text-emerald-800"
                              : suggestion.status === "dismissed"
                                ? "bg-slate-200 text-slate-700"
                                : "bg-amber-100 text-amber-800"
                          }`}
                        >
                          {suggestion.status === "applied"
                            ? "Aplicada"
                            : suggestion.status === "dismissed"
                              ? "Descartada"
                              : "Pendiente"}
                        </span>
                      </div>

                      <p className="mt-3 text-sm leading-6 text-slate-600">
                        {suggestion.explanation}
                      </p>

                      <div className="mt-4 grid gap-3 md:grid-cols-2">
                        <div className="rounded-lg bg-slate-50 p-3">
                          <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-slate-500">
                            Texto original
                          </p>
                          <p className="whitespace-pre-wrap text-sm leading-6">
                            {suggestion.original}
                          </p>
                        </div>

                        <div className="rounded-lg bg-emerald-50 p-3">
                          <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-emerald-800">
                            Propuesta
                          </p>
                          <p className="whitespace-pre-wrap text-sm leading-6 text-emerald-950">
                            {suggestion.replacement}
                          </p>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </section>

          <aside className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">
            <div className="border-b border-slate-200 px-5 py-4">
              <div className="flex items-center gap-2">
                <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-violet-100 text-violet-700">
                  <Sparkles size={19} />
                </div>
                <div>
                  <h2 className="font-semibold">Sugerencias de la IA</h2>
                  <p className="text-xs text-slate-500">
                    Propuestas de demostración
                  </p>
                </div>
              </div>
            </div>

            <div className="space-y-4 p-4">
              {suggestions.map((suggestion) => (
                <article
                  key={suggestion.id}
                  className={`rounded-xl border p-4 ${
                    suggestion.status === "applied"
                      ? "border-emerald-200 bg-emerald-50/50"
                      : suggestion.status === "dismissed"
                        ? "border-slate-200 bg-slate-50 opacity-80"
                        : "border-slate-200 bg-white"
                  }`}
                >
                  <div className="flex items-start justify-between gap-2">
                    <h3 className="text-sm font-semibold leading-5">
                      {suggestion.title}
                    </h3>

                    {suggestion.status === "applied" ? (
                      <CheckCircle2
                        size={19}
                        className="shrink-0 text-emerald-600"
                      />
                    ) : suggestion.status === "dismissed" ? (
                      <X
                        size={18}
                        className="shrink-0 text-slate-400"
                      />
                    ) : (
                      <span
                        className={`shrink-0 rounded-full border px-2 py-1 text-[10px] font-semibold ${CATEGORY_STYLES[suggestion.category]}`}
                      >
                        {CATEGORY_LABELS[suggestion.category]}
                      </span>
                    )}
                  </div>

                  <p className="mt-3 text-xs leading-5 text-slate-600">
                    {suggestion.explanation}
                  </p>

                  {editingId === suggestion.id ? (
                    <div className="mt-4 space-y-3">
                      <label
                        htmlFor={`proposal-${suggestion.id}`}
                        className="block text-xs font-semibold text-slate-700"
                      >
                        Editar propuesta
                      </label>

                      <textarea
                        id={`proposal-${suggestion.id}`}
                        value={editedProposal}
                        onChange={(event) =>
                          setEditedProposal(event.target.value)
                        }
                        rows={6}
                        className="w-full rounded-lg border border-slate-300 bg-white p-3 text-sm leading-6 outline-none focus:border-emerald-500 focus:ring-2 focus:ring-emerald-100"
                      />

                      <div className="flex flex-wrap gap-2">
                        <button
                          type="button"
                          onClick={() => handleSaveProposal(suggestion)}
                          className="inline-flex items-center gap-1.5 rounded-lg bg-emerald-600 px-3 py-2 text-xs font-semibold text-white hover:bg-emerald-700"
                        >
                          <Save size={14} />
                          Guardar propuesta
                        </button>

                        <button
                          type="button"
                          onClick={handleCancelEditing}
                          className="rounded-lg border border-slate-300 px-3 py-2 text-xs font-semibold text-slate-700 hover:bg-slate-50"
                        >
                          Cancelar
                        </button>
                      </div>
                    </div>
                  ) : (
                    <>
                      <div className="mt-4 rounded-lg border border-slate-200 bg-slate-50 p-3">
                        <p className="mb-2 text-xs font-semibold text-slate-500">
                          Propuesta de adaptación
                        </p>
                        <p className="whitespace-pre-wrap text-sm leading-6 text-slate-800">
                          {suggestion.replacement}
                        </p>
                      </div>

                      <div className="mt-3 flex flex-wrap gap-2">
                        {suggestion.status !== "applied" && (
                          <button
                            type="button"
                            onClick={() => handleApply(suggestion)}
                            className="inline-flex items-center justify-center gap-1.5 rounded-lg bg-emerald-600 px-3 py-2 text-xs font-semibold text-white transition hover:bg-emerald-700 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:ring-offset-2"
                          >
                            <Check size={14} />
                            Aplicar
                          </button>
                        )}

                        <button
                          type="button"
                          onClick={() => handleStartEditing(suggestion)}
                          className="inline-flex items-center justify-center gap-1.5 rounded-lg border border-slate-300 px-3 py-2 text-xs font-semibold text-slate-700 transition hover:bg-slate-50"
                        >
                          <Pencil size={14} />
                          Editar propuesta
                        </button>

                        {suggestion.status === "pending" && (
                          <button
                            type="button"
                            onClick={() => handleDismiss(suggestion)}
                            className="inline-flex items-center justify-center gap-1 rounded-lg px-2 py-2 text-xs font-medium text-slate-500 hover:bg-slate-100 hover:text-slate-800"
                          >
                            <X size={14} />
                            Descartar
                          </button>
                        )}

                        {suggestion.status === "dismissed" && (
                          <button
                            type="button"
                            onClick={() =>
                              updateSuggestionStatus(
                                suggestion.id,
                                "pending",
                              )
                            }
                            className="inline-flex items-center gap-1 rounded-lg px-2 py-2 text-xs font-medium text-slate-600 hover:bg-slate-100"
                          >
                            Revisar de nuevo
                          </button>
                        )}
                      </div>
                    </>
                  )}
                </article>
              ))}

              <div className="rounded-xl border border-violet-200 bg-violet-50 p-3">
                <div className="flex items-start gap-2">
                  <Lightbulb
                    size={17}
                    className="mt-0.5 shrink-0 text-violet-700"
                  />
                  <p className="text-xs leading-5 text-violet-950">
                    Las propuestas son orientativas. Revisá cada adaptación y
                    decidí si responde a las necesidades de tu material.
                  </p>
                </div>
              </div>
            </div>
          </aside>
        </div>

        <footer className="mt-5 rounded-2xl border border-slate-200 bg-white p-4 shadow-sm sm:px-5">
          <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
            <div>
              <p className="font-semibold">Acciones del documento</p>
              <p className="mt-1 text-xs text-slate-500">
                Los cambios se mantienen en esta pantalla mientras no la
                recargues. Todavía no se guardan en el servidor.
              </p>
            </div>

            <div className="flex flex-wrap gap-2">
              <button
                type="button"
                onClick={handleUndo}
                disabled={undoStack.length === 0}
                className="inline-flex items-center gap-2 rounded-lg border border-slate-300 px-3 py-2.5 text-sm font-medium text-slate-700 transition hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-40"
              >
                <RotateCcw size={16} />
                Deshacer
              </button>

              <button
                type="button"
                onClick={handleRedo}
                disabled={redoStack.length === 0}
                className="inline-flex items-center gap-2 rounded-lg border border-slate-300 px-3 py-2.5 text-sm font-medium text-slate-700 transition hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-40"
              >
                <RotateCw size={16} />
                Rehacer
              </button>

              <button
                type="button"
                onClick={handleRestoreOriginal}
                className="inline-flex items-center gap-2 rounded-lg border border-slate-300 px-3 py-2.5 text-sm font-semibold text-slate-700 transition hover:bg-slate-50"
              >
                <History size={16} />
                Volver al original
              </button>
            </div>
          </div>
        </footer>
      </div>
    </main>
  );
}
