"use client";

import { useState, type KeyboardEvent } from "react";
import * as Dialog from "@radix-ui/react-dialog";
import {
  ArrowLeft,
  Bookmark,
  Check,
  Download,
  Files,
  Folder,
  FolderPlus,
  LoaderCircle,
  Sparkles,
  X,
} from "lucide-react";
import type { Folder as FolderType } from "@/types";
import { Button } from "@/components/ui/Button";

export interface ExportModalProps {
  isOpen: boolean;
  onClose: () => void;
  onDownloadPdf?: () => void;
  onSaveToApp?: (name: string, folderId: string | null) => void;
  onCreateFolder?: (name: string) => FolderType | null;
  isGeneratingPdf?: boolean;
  documentName?: string;
  initialFolderId?: string | null;
  folders?: FolderType[];
  folderCounts?: Record<string, number>;
}

export default function ExportModal({
  isOpen,
  onClose,
  onDownloadPdf,
  onSaveToApp,
  onCreateFolder,
  isGeneratingPdf = false,
  documentName = "",
  initialFolderId = null,
  folders = [],
  folderCounts = {},
}: ExportModalProps) {
  const [view, setView] = useState<"options" | "save">("options");
  const [fileName, setFileName] = useState(documentName);
  const [selectedFolderId, setSelectedFolderId] = useState<string | null>(
    initialFolderId,
  );
  const [isCreatingFolder, setIsCreatingFolder] = useState(false);
  const [newFolderName, setNewFolderName] = useState("");
  const [error, setError] = useState("");

  function confirmNewFolder() {
    const cleanName = newFolderName.trim();

    if (!cleanName) {
      setError("Ingresá un nombre para la carpeta.");
      return;
    }

    const folder = onCreateFolder?.(cleanName);

    if (!folder) {
      setError("Ya existe una carpeta con ese nombre.");
      return;
    }

    setSelectedFolderId(folder.id);
    setIsCreatingFolder(false);
    setNewFolderName("");
    setError("");
  }

  function cancelNewFolder() {
    setIsCreatingFolder(false);
    setNewFolderName("");
    setError("");
  }

  function handleNewFolderKeyDown(event: KeyboardEvent<HTMLInputElement>) {
    if (event.key === "Enter") {
      event.preventDefault();
      confirmNewFolder();
    } else if (event.key === "Escape") {
      event.preventDefault();
      cancelNewFolder();
    }
  }

  function confirmSave() {
    const cleanName = fileName.trim();

    if (!cleanName) {
      setError("Ingresá un nombre para el archivo.");
      return;
    }

    if (!onSaveToApp) {
      setError("Guardar en Mis documentos no está disponible en esta vista.");
      return;
    }

    onSaveToApp(cleanName, selectedFolderId);
  }

  return (
    <Dialog.Root
      open={isOpen}
      onOpenChange={(open) => {
        if (!open) onClose();
      }}
    >
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 z-50 bg-slate-950/55" />
        <Dialog.Content className="fixed left-1/2 top-1/2 z-50 max-h-[calc(100dvh-2rem)] w-[calc(100vw-2rem)] max-w-lg -translate-x-1/2 -translate-y-1/2 overflow-y-auto rounded-xl border border-slate-200 bg-[#f7fafc] p-6 text-slate-900 shadow-2xl focus:outline-none sm:p-8">
          <div className="flex items-start justify-between gap-4">
            <div className="flex min-w-0 items-start gap-4">
              <Sparkles
                aria-hidden="true"
                className="mt-0.5 size-9 shrink-0 text-blue-600 sm:size-11"
                strokeWidth={1.8}
              />
              <div className="min-w-0">
                <Dialog.Title className="text-lg font-bold text-slate-900 sm:text-xl">
                  {view === "options"
                    ? "Tu material está listo"
                    : "Guardar en Mis documentos"}
                </Dialog.Title>
                <Dialog.Description className="mt-2 text-sm leading-6 text-slate-600 sm:text-base">
                  {view === "options"
                    ? "El análisis finalizó correctamente. Ya podés descargar el PDF o guardarlo en tu biblioteca."
                    : "Elegí el nombre del archivo y la carpeta de destino."}
                </Dialog.Description>
              </div>
            </div>

            <Dialog.Close asChild>
              <button
                type="button"
                aria-label="Cerrar ventana"
                className="grid size-9 shrink-0 place-items-center rounded-md text-slate-500 transition hover:bg-slate-100 hover:text-slate-900 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-blue-600"
              >
                <X aria-hidden="true" className="size-5" />
              </button>
            </Dialog.Close>
          </div>

          {view === "options" ? (
            <div className="mt-7 grid gap-3">
              <button
                type="button"
                onClick={onDownloadPdf}
                disabled={isGeneratingPdf}
                aria-busy={isGeneratingPdf}
                className="inline-flex min-h-12 items-center justify-center gap-3 rounded-lg bg-blue-600 px-5 py-3 text-sm font-semibold text-white transition hover:bg-blue-700 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-blue-700 disabled:cursor-not-allowed disabled:opacity-70 sm:text-base"
              >
                {isGeneratingPdf ? (
                  <LoaderCircle
                    aria-hidden="true"
                    className="size-5 animate-spin"
                  />
                ) : (
                  <Download aria-hidden="true" className="size-5" />
                )}
                {isGeneratingPdf ? "Generando PDF..." : "Descargar PDF"}
              </button>
              <button
                type="button"
                onClick={() => setView("save")}
                disabled={isGeneratingPdf || !onSaveToApp}
                className="inline-flex min-h-12 items-center justify-center gap-3 rounded-lg border border-blue-200 bg-transparent px-5 py-3 text-sm font-semibold text-blue-700 transition hover:bg-blue-50 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-blue-700 disabled:cursor-not-allowed disabled:opacity-70 sm:text-base"
              >
                <Bookmark aria-hidden="true" className="size-5" />
                Guardar en la app
              </button>
            </div>
          ) : (
            <div className="mt-6 space-y-5">
              <button
                type="button"
                onClick={() => {
                  setView("options");
                  setError("");
                }}
                className="inline-flex items-center gap-2 rounded-md px-2 py-1 text-sm font-semibold text-slate-600 transition hover:bg-[#F4F6FC] hover:text-slate-900 focus-visible:outline-2 focus-visible:outline-blue-600"
              >
                <ArrowLeft aria-hidden="true" className="size-4" />
                Volver
              </button>

              <div>
                <label
                  htmlFor="save-file-name"
                  className="mb-2 block text-sm font-semibold text-slate-700"
                >
                  Nombre del archivo
                </label>
                <input
                  id="save-file-name"
                  value={fileName}
                  onChange={(event) => {
                    setFileName(event.target.value);
                    setError("");
                  }}
                  maxLength={120}
                  autoFocus
                  className="w-full rounded-lg border border-[#C5D2E7] bg-white px-3 py-2.5 text-sm outline-none transition focus:border-primary focus:ring-2 focus:ring-blue-100"
                />
              </div>

              <div>
                <p className="mb-2 text-sm font-semibold text-slate-700">
                  Destino
                </p>
                <ul
                  role="listbox"
                  aria-label="Carpetas de destino"
                  className="max-h-52 space-y-1 overflow-y-auto rounded-lg border border-[#C5D2E7] bg-white p-2"
                >
                  <li>
                    <button
                      type="button"
                      role="option"
                      aria-selected={selectedFolderId === null}
                      onClick={() => setSelectedFolderId(null)}
                      className={`flex w-full items-center gap-3 rounded-md px-3 py-2 text-left text-sm transition ${
                        selectedFolderId === null
                          ? "bg-[#E8EDFC] text-[#14203C]"
                          : "hover:bg-[#F4F6FC]"
                      }`}
                    >
                      <Files
                        aria-hidden="true"
                        className="size-4 shrink-0 text-slate-500"
                      />
                      <span className="min-w-0 flex-1 truncate">
                        Mis documentos (sin carpeta)
                      </span>
                      <span className="shrink-0 rounded-full bg-slate-100 px-2 py-0.5 text-xs text-slate-600">
                        Raíz
                      </span>
                    </button>
                  </li>

                  {folders.map((folder) => {
                    const isSelected = selectedFolderId === folder.id;

                    return (
                      <li key={folder.id}>
                        <button
                          type="button"
                          role="option"
                          aria-selected={isSelected}
                          onClick={() => setSelectedFolderId(folder.id)}
                          className={`flex w-full items-center gap-3 rounded-md px-3 py-2 text-left text-sm transition ${
                            isSelected
                              ? "bg-[#E8EDFC] text-[#14203C]"
                              : "hover:bg-[#F4F6FC]"
                          }`}
                        >
                          <Folder
                            aria-hidden="true"
                            className="size-4 shrink-0"
                            style={{ color: folder.color }}
                          />
                          <span className="min-w-0 flex-1 truncate">
                            {folder.name}
                          </span>
                          <span className="shrink-0 rounded-full bg-slate-100 px-2 py-0.5 text-xs text-slate-600">
                            {folderCounts[folder.id] ?? 0} archivo(s)
                          </span>
                        </button>
                      </li>
                    );
                  })}
                </ul>
              </div>

              {isCreatingFolder ? (
                <div className="space-y-2 rounded-lg border border-[#C5D2E7] bg-[#F4F6FC] p-3">
                  <label
                    htmlFor="new-folder-name"
                    className="block text-sm font-semibold text-slate-700"
                  >
                    Nombre de la carpeta
                  </label>
                  <div className="flex flex-wrap gap-2">
                    <input
                      id="new-folder-name"
                      value={newFolderName}
                      onChange={(event) => {
                        setNewFolderName(event.target.value);
                        setError("");
                      }}
                      onKeyDown={handleNewFolderKeyDown}
                      maxLength={60}
                      autoFocus
                      placeholder="Ej.: Proyectos"
                      className="min-w-0 flex-1 rounded-md border border-[#C5D2E7] bg-white px-3 py-2 text-sm outline-none transition focus:border-primary focus:ring-2 focus:ring-blue-100"
                    />
                    <Button
                      type="button"
                      onClick={confirmNewFolder}
                      variant="lumi-primary"
                      className="px-3"
                    >
                      Crear
                    </Button>
                    <Button
                      type="button"
                      onClick={cancelNewFolder}
                      variant="lumi-outline"
                      className="px-3"
                    >
                      Cancelar
                    </Button>
                  </div>
                </div>
              ) : (
                <button
                  type="button"
                  onClick={() => {
                    setError("");
                    setIsCreatingFolder(true);
                  }}
                  className="inline-flex items-center gap-2 rounded-md border border-dashed border-[#C5D2E7] px-3 py-2 text-sm font-semibold text-primary transition hover:border-primary hover:bg-[#E8EDFC]"
                >
                  <FolderPlus aria-hidden="true" className="size-4" />
                  Nueva carpeta
                </button>
              )}

              {error && (
                <p role="alert" className="text-sm font-medium text-red-600">
                  {error}
                </p>
              )}

              <Button
                type="button"
                onClick={confirmSave}
                disabled={!fileName.trim()}
                variant="lumi-primary"
                className="min-h-12 w-full gap-3 sm:text-base"
              >
                <Check aria-hidden="true" className="size-5" />
                Guardar aquí
              </Button>
            </div>
          )}
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}
