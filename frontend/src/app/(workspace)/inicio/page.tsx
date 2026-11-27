"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useRef, useState, type ChangeEvent, type DragEvent } from "react";
import {
  ArrowRight,
  Eye,
  MoreHorizontal,
  X,
  FileText,
  UploadCloud,
  AlertCircle,
} from "lucide-react";
import * as Dialog from "@radix-ui/react-dialog";
import { Button } from "@/components/ui/Button";
import { DEMO_MOCKS } from "@/lib/demoMocks";
import { useLumiStore } from "@/store/useLumiStore";
import type { Folder, LumiDocument } from "@/types";

const MAX_FILE_SIZE = 25 * 1024 * 1024;

const STATUS_STYLES: Record<LumiDocument["status"], string> = {
  Analizado: "border-emerald-200 bg-emerald-50 text-emerald-800",
  "En edición": "border-blue-200 bg-blue-50 text-blue-800",
  Procesando: "border-amber-200 bg-amber-50 text-amber-800",
  Guardado: "border-violet-200 bg-violet-50 text-violet-800",
};

export default function InicioPage() {
  const router = useRouter();
  const inputRef = useRef<HTMLInputElement>(null);

  const documents = useLumiStore((state) => state.documents);
  const folders = useLumiStore((state) => state.folders);
  const diagnostics = useLumiStore((state) => state.diagnostics);
  const isLoading = useLumiStore((state) => state.isLoading);
  const error = useLumiStore((state) => state.error);
  const uploadAndAnalyze = useLumiStore((state) => state.uploadAndAnalyze);
  const setPendingUpload = useLumiStore((state) => state.setPendingUpload);
  const setDemoDocument = useLumiStore((state) => state.setDemoDocument);
  const clearError = useLumiStore((state) => state.clearError);

  const [localError, setLocalError] = useState("");
  const [isDragging, setIsDragging] = useState(false);

  const selectFile = async (file?: File) => {
    if (!file) return;

    if (!file.name.toLowerCase().endsWith(".pdf")) {
      setLocalError("El archivo debe tener formato PDF.");
      return;
    }

    if (file.size > MAX_FILE_SIZE) {
      setLocalError("El archivo supera el límite de 25 MB.");
      return;
    }

    const demo = DEMO_MOCKS[file.name];

    if (!demo) {
      setLocalError("");

      try {
        await uploadAndAnalyze(file);

        const sessionId =
          useLumiStore.getState().currentSessionId;

        if (sessionId) {
          router.push(`/analizando?sessionId=${sessionId}`);
        }
      } catch {
        // Error already handled in store
      }

      return;
    }

    // Demo file - use mock flow
    setLocalError("");

    const fileUrl = URL.createObjectURL(file);

    setPendingUpload(file);
    router.push("/analizando");

    window.setTimeout(() => {
      setDemoDocument(file.name, fileUrl);
      router.push(`/diagnostico/${demo.id}`);
    }, 1500);
  };

  const handleFileChange = (
    event: ChangeEvent<HTMLInputElement>,
  ) => {
    selectFile(event.currentTarget.files?.[0]);
    event.currentTarget.value = "";
  };

  const handleDragOver = (
    event: DragEvent<HTMLDivElement>,
  ) => {
    event.preventDefault();
    setIsDragging(true);
  };

  const handleDrop = (
    event: DragEvent<HTMLDivElement>,
  ) => {
    event.preventDefault();
    setIsDragging(false);
    selectFile(event.dataTransfer.files[0]);
  };

  const recentDocuments = documents.slice(0, 4);
  const displayError = localError || error;

  return (
    <main className="min-h-svh bg-[#F4F6FC] text-[#14203C]">
      <div className="mx-auto w-full max-w-7xl px-4 pb-10 pt-8 sm:px-6 sm:pt-10">

        {/* Bienvenida */}
        <section aria-labelledby="welcome-title">
          <h1
            id="welcome-title"
            className="text-2xl font-medium text-[#14203C] sm:text-3xl"
          >
            ¡Te damos la bienvenida a Lumi!
          </h1>

          <p className="mt-2 text-sm text-slate-600 sm:text-base">
            ¿Qué material querés analizar hoy?
          </p>

          {/* Zona de carga PDF */}
          <div
            onDragEnter={() => setIsDragging(true)}
            onDragOver={handleDragOver}
            onDragLeave={() => setIsDragging(false)}
            onDrop={handleDrop}
            className={`mx-auto mt-6 flex min-h-52 max-w-3xl flex-col items-center justify-center rounded-xl border border-dashed px-5 py-8 text-center transition-colors sm:min-h-64 ${
              isDragging
                ? "border-[#6360ED] bg-[#E8EDFC]"
                : "border-[#A5A3F5] bg-white"
            }`}
            aria-label="Zona para cargar un archivo PDF"
          >
            <div className="grid size-14 place-items-center rounded-full bg-[#E8EDFC]">
              <UploadCloud
                aria-hidden="true"
                className="size-7 text-primary"
              />
            </div>

            <p className="mt-4 text-sm font-semibold text-[#14203C]">
              Arrastrá tu PDF aquí o
            </p>

            <p className="mt-1 text-sm text-slate-600">
              Seleccioná el archivo desde tu dispositivo.
            </p>

            <input
              ref={inputRef}
              type="file"
              accept=".pdf,application/pdf"
              onChange={handleFileChange}
              className="sr-only"
              aria-label="Seleccionar archivo PDF"
              disabled={isLoading}
            />

            <Button
              type="button"
              variant="lumi-primary"
              onClick={() => inputRef.current?.click()}
              disabled={isLoading}
              className="mt-4 px-8"
            >
              {isLoading
                ? "Subiendo..."
                : "Seleccionar archivo"}
            </Button>

            <p className="mt-3 text-xs text-slate-600">
              PDF máximo 25 MB
            </p>

            {displayError && (
              <div
                role="alert"
                className="mt-3 flex items-center gap-2 text-sm font-medium text-red-700"
              >
                <AlertCircle
                  aria-hidden="true"
                  className="size-4 shrink-0"
                />

                {displayError}

                <button
                  type="button"
                  onClick={() => {
                    setLocalError("");
                    clearError();
                  }}
                  className="ml-2 text-red-700 underline hover:text-red-900"
                >
                  Descartar
                </button>
              </div>
            )}
          </div>
        </section>

        {/* Documentos recientes */}
        <section
          aria-labelledby="recent-documents-title"
          className="mt-10"
        >
          <div className="mb-4 flex items-center justify-between gap-4">
            <div>
              <h2
                id="recent-documents-title"
                className="text-base font-semibold text-[#14203C]"
              >
                Tus últimos documentos
              </h2>

              <p className="mt-1 text-xs text-slate-600">
                Retomá los materiales que revisaste anteriormente.
              </p>
            </div>

            <Link
              href="/archivos"
              className="inline-flex shrink-0 items-center gap-2 rounded-md text-sm font-semibold text-primary hover:underline"
            >
              Ver todos

              <ArrowRight
                aria-hidden="true"
                className="size-4"
              />
            </Link>
          </div>

          {recentDocuments.length > 0 ? (
            <div
              role="region"
              aria-label="Tabla de documentos recientes"
              tabIndex={0}
              className="overflow-x-auto rounded-lg border border-[#C5D2E7] bg-white"
            >
              <table className="w-full min-w-212.5 text-left text-sm">
                <thead className="border-b border-[#C5D2E7] bg-slate-50 text-xs text-[#14203C]">
                  <tr>
                    {["Nombre", "Tipo", "Fecha", "Ubicación", "Estado", "Barreras", "Acciones"].map((heading, index) => (
                      <th
                        key={heading}
                        scope="col"
                        className={`px-4 py-3 font-semibold ${index >= 5 ? "text-center" : ""}`}
                      >
                        {heading}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-200">
                  {recentDocuments.map((document) => {
                    const diagnostic = diagnostics.find(
                      (item) => item.documentId === document.id,
                    );
                    const folder = folders.find(
                      (item) => item.id === document.folderId,
                    );
                    const location = folder?.name ??
                      (document.folderId ? "Carpeta no disponible" : "Mis documentos");

                    return (
                      <tr key={document.id} className="transition-colors hover:bg-[#F4F6FC]">
                        <td className="px-4 py-3">
                          <Link
                            href={`/diagnostico/${document.id}`}
                            className="flex items-center gap-3 rounded-md hover:underline"
                          >
                            <span className="grid size-10 shrink-0 place-items-center rounded-lg bg-[#E8EDFC] text-[#6360ED]">
                              <FileText aria-hidden="true" className="size-5" />
                            </span>
                            <div className="min-w-0">
                              <p className="max-w-56 truncate font-medium text-[#14203C]">
                                {document.name}
                              </p>
                              <p className="mt-1 text-xs text-slate-500">{document.size}</p>
                            </div>
                          </Link>
                        </td>
                        <td className="px-4 py-3 text-xs text-slate-600">PDF</td>
                        <td className="whitespace-nowrap px-4 py-3 text-xs text-slate-600">{document.date}</td>
                        <td className="px-4 py-3 text-xs text-slate-600">{location}</td>
                        <td className="px-4 py-3">
                          <span className={`inline-flex whitespace-nowrap rounded-md border px-3 py-1 text-xs font-medium ${STATUS_STYLES[document.status]}`}>
                            {document.status}
                          </span>
                        </td>
                        <td className="px-4 py-3 text-center text-xs text-slate-600">
                          {diagnostic?.barriers.length ?? "—"}
                        </td>
                        <td className="px-4 py-3">
                          <div className="flex items-center justify-center gap-1">
                            <Link
                              href={`/diagnostico/${document.id}`}
                              aria-label={`Ver diagnóstico de ${document.name}`}
                              className="inline-flex size-10 items-center justify-center rounded-lg text-primary transition-colors hover:bg-[#E8EDFC]"
                            >
                              <Eye aria-hidden="true" className="size-5" />
                            </Link>
                            <DocumentActions
                              document={document}
                              folders={folders}
                              location={location}
                              barrierCount={diagnostic?.barriers.length}
                            />
                          </div>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          ) : (
            <p className="rounded-lg border border-[#C5D2E7] bg-white px-4 py-6 text-sm text-slate-600">
              Todavía no tenés documentos. Cargá un PDF para empezar.
            </p>
          )}
        </section>
      </div>
    </main>
  );
}

interface DocumentActionsProps {
  document: LumiDocument;
  folders: Folder[];
  location: string;
  barrierCount?: number;
}

function DocumentActions({ document, folders, location, barrierCount }: DocumentActionsProps) {
  const renameDocument = useLumiStore((state) => state.renameDocument);
  const saveDocumentToFolder = useLumiStore((state) => state.saveDocumentToFolder);
  const [open, setOpen] = useState(false);
  const [view, setView] = useState<"actions" | "rename" | "save" | "details">("actions");
  const [name, setName] = useState(document.name);
  const [folderId, setFolderId] = useState(document.folderId ?? "");
  const [notice, setNotice] = useState("");

  function handleOpenChange(nextOpen: boolean) {
    if (nextOpen) {
      setView("actions");
      setName(document.name);
      setFolderId(document.folderId ?? "");
      setNotice("");
    }
    setOpen(nextOpen);
  }

  const actionClass = "w-full rounded-lg px-3 py-2.5 text-left text-sm text-[#14203C] hover:bg-[#E8EDFC]";
  const fieldClass = "min-h-11 w-full rounded-lg border border-[#C5D2E7] bg-white px-3 py-2 text-sm text-[#14203C]";

  return (
    <Dialog.Root open={open} onOpenChange={handleOpenChange}>
      <Dialog.Trigger asChild>
        <button
          type="button"
          aria-label={`Más acciones de ${document.name}`}
          className="inline-flex size-10 items-center justify-center rounded-lg text-primary hover:bg-[#E8EDFC]"
        >
          <MoreHorizontal aria-hidden="true" className="size-5 rotate-90" />
        </button>
      </Dialog.Trigger>
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 z-50 bg-slate-950/40" />
        <Dialog.Content className="fixed left-1/2 top-1/2 z-50 max-h-[85dvh] w-[calc(100vw-2rem)] max-w-sm -translate-x-1/2 -translate-y-1/2 overflow-y-auto rounded-xl border border-[#C5D2E7] bg-white p-5 text-[#14203C] shadow-xl">
          <div className="flex items-start justify-between gap-3">
            <div className="min-w-0">
              <Dialog.Title className="text-lg font-semibold">
                {view === "rename" ? "Renombrar documento" : view === "save" ? "Guardar en otra carpeta" : view === "details" ? "Detalles del documento" : "Acciones del documento"}
              </Dialog.Title>
              <Dialog.Description className="mt-1 wrap-break-word text-sm text-slate-600">
                {document.name}
              </Dialog.Description>
            </div>
            <Dialog.Close asChild>
              <button type="button" aria-label="Cerrar acciones" className="grid size-10 shrink-0 place-items-center rounded-lg hover:bg-slate-100">
                <X aria-hidden="true" className="size-5" />
              </button>
            </Dialog.Close>
          </div>

          <div className="mt-4">
            {view === "actions" && (
              <div className="grid gap-1">
                <button type="button" className={actionClass} onClick={() => { setName(document.name); setNotice(""); setView("rename"); }}>
                  Renombrar
                </button>
                <button type="button" className={actionClass} onClick={() => { setFolderId(document.folderId ?? ""); setNotice(""); setView("save"); }}>
                  Guardar en otra carpeta
                </button>
                <button type="button" className={actionClass} onClick={() => setView("details")}>
                  Ver detalles
                </button>
                <Link href={`/diagnostico/${document.id}`} className={actionClass} onClick={() => setOpen(false)}>
                  Ver diagnóstico
                </Link>
              </div>
            )}

            {view === "rename" && (
              <form className="space-y-4" onSubmit={(event) => {
                event.preventDefault();
                const cleanName = name.trim();
                if (!cleanName) return;
                renameDocument(document.id, cleanName);
                setNotice("Nombre actualizado en esta sesión.");
                setView("actions");
              }}>
                <label className="block space-y-2 text-sm font-medium">
                  <span>Nombre del archivo</span>
                  <input className={fieldClass} value={name} onChange={(event) => setName(event.target.value)} required maxLength={120} />
                </label>
                <div className="flex flex-wrap justify-end gap-2">
                  <Button variant="lumi-outline" onClick={() => setView("actions")}>Volver</Button>
                  <Button type="submit" variant="lumi-primary" disabled={!name.trim() || name.trim() === document.name}>Guardar</Button>
                </div>
              </form>
            )}

            {view === "save" && (
              <form className="space-y-4" onSubmit={(event) => {
                event.preventDefault();
                if (folderId && !folders.some((folder) => folder.id === folderId)) return;
                saveDocumentToFolder(document.id, document.name, folderId || null);
                setNotice("Documento guardado en esta sesión.");
                setView("actions");
              }}>
                <label className="block space-y-2 text-sm font-medium">
                  <span>Carpeta de destino</span>
                  <select className={fieldClass} value={folderId} onChange={(event) => setFolderId(event.target.value)}>
                    <option value="">Mis documentos (sin carpeta)</option>
                    {folders.map((folder) => <option key={folder.id} value={folder.id}>{folder.name}</option>)}
                  </select>
                </label>
                <p className="text-xs leading-5 text-slate-600">Esta acción marca el documento como Guardado y actualiza su fecha. Los cambios se mantienen en la sesión actual.</p>
                <div className="flex flex-wrap justify-end gap-2">
                  <Button variant="lumi-outline" onClick={() => setView("actions")}>Volver</Button>
                  <Button type="submit" variant="lumi-primary" disabled={folderId === (document.folderId ?? "") || (!!folderId && !folders.some((folder) => folder.id === folderId))}>Guardar</Button>
                </div>
              </form>
            )}

            {view === "details" && (
              <div className="space-y-4">
                <dl className="grid grid-cols-[auto_1fr] gap-x-4 gap-y-3 text-sm">
                  {[
                    ["Tipo", "PDF"],
                    ["Tamaño", document.size],
                    ["Fecha", document.date],
                    ["Ubicación", location],
                    ["Estado", document.status],
                    ["Barreras", barrierCount ?? "Sin diagnóstico"],
                  ].map(([label, value]) => (
                    <div key={label} className="contents">
                      <dt className="font-medium">{label}</dt>
                      <dd className="min-w-0 wrap-break-word text-slate-600">{value}</dd>
                    </div>
                  ))}
                </dl>
                <Button variant="lumi-outline" onClick={() => setView("actions")}>Volver</Button>
              </div>
            )}
            {notice && <p role="status" className="mt-3 text-sm text-emerald-800">{notice}</p>}
          </div>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}
