"use client";

import * as Dialog from "@radix-ui/react-dialog";
import { Bookmark, Download, Sparkles, X } from "lucide-react";

export interface ExportModalProps {
  isOpen: boolean;
  onClose: () => void;
  onDownloadPdf?: () => void;
  onSaveToApp?: () => void;
}

export default function ExportModal({
  isOpen,
  onClose,
  onDownloadPdf,
  onSaveToApp,
}: ExportModalProps) {
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
                  Tu material está listo
                </Dialog.Title>
                <Dialog.Description className="mt-2 text-sm leading-6 text-slate-600 sm:text-base">
                  El análisis finalizó correctamente. Ya podés descargar el PDF
                  o guardarlo en tu biblioteca.
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

          <div className="mt-7 grid gap-3">
            <button
              type="button"
              onClick={onDownloadPdf}
              className="inline-flex min-h-12 items-center justify-center gap-3 rounded-lg bg-blue-600 px-5 py-3 text-sm font-semibold text-white transition hover:bg-blue-700 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-blue-700 sm:text-base"
            >
              <Download aria-hidden="true" className="size-5" />
              Descargar PDF
            </button>
            <button
              type="button"
              onClick={onSaveToApp}
              className="inline-flex min-h-12 items-center justify-center gap-3 rounded-lg border border-blue-200 bg-transparent px-5 py-3 text-sm font-semibold text-blue-700 transition hover:bg-blue-50 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-blue-700 sm:text-base"
            >
              <Bookmark aria-hidden="true" className="size-5" />
              Guardar en la app
            </button>
          </div>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}
