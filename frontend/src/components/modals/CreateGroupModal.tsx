"use client";

import { useRef, useState, type ChangeEvent, type FormEvent } from "react";
import * as Dialog from "@radix-ui/react-dialog";
import { FileText, Upload, X } from "lucide-react";
import { Button } from "@/components/ui/Button";

const GROUP_COLORS = [
  { name: "Violeta", value: "#8B5CF6" },
  { name: "Azul", value: "#3B82F6" },
  { name: "Verde", value: "#22C55E" },
  { name: "Amarillo", value: "#EAB308" },
  { name: "Naranja", value: "#F97316" },
  { name: "Rosa", value: "#EC4899" },
  { name: "Rojo", value: "#EF4444" },
];

export interface NewGroup {
  name: string;
  color: string;
  file: File | null;
}

interface CreateGroupModalProps {
  isOpen: boolean;
  onClose: () => void;
  onCreate: (group: NewGroup) => void;
  showOrganizationOptions?: boolean;
}

export default function CreateGroupModal({
  isOpen,
  onClose,
  onCreate,
  showOrganizationOptions = false,
}: CreateGroupModalProps) {
  const [name, setName] = useState("");
  const [color, setColor] = useState(GROUP_COLORS[0].value);
  const [file, setFile] = useState<File | null>(null);
  const [error, setError] = useState("");
  const nameInputRef = useRef<HTMLInputElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  function resetForm() {
    setName("");
    setColor(GROUP_COLORS[0].value);
    setFile(null);
    setError("");
    if (fileInputRef.current) fileInputRef.current.value = "";
  }

  function handleClose() {
    resetForm();
    onClose();
  }

  function handleFileChange(event: ChangeEvent<HTMLInputElement>) {
    const selectedFile = event.target.files?.[0];
    if (!selectedFile) return;

    if (selectedFile.type !== "application/pdf") {
      setError("Seleccioná un archivo PDF.");
      event.target.value = "";
      setFile(null);
      return;
    }

    if (selectedFile.size > 10 * 1024 * 1024) {
      setError("El PDF no puede superar los 10 MB.");
      event.target.value = "";
      setFile(null);
      return;
    }

    setError("");
    setFile(selectedFile);
  }

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const cleanName = name.trim();

    if (!cleanName) {
      setError("Ingresá un nombre para la carpeta.");
      return;
    }

    onCreate({
      name: cleanName,
      color: showOrganizationOptions ? color : GROUP_COLORS[0].value,
      file: showOrganizationOptions ? file : null,
    });
    resetForm();
  }

  return (
    <Dialog.Root open={isOpen} onOpenChange={(open) => { if (!open) handleClose(); }}>
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 z-50 bg-slate-950/60 backdrop-blur-[2px]" />
        <Dialog.Content
          className="fixed left-1/2 top-1/2 z-50 max-h-[calc(100dvh-2rem)] w-[calc(100vw-2rem)] max-w-[500px] -translate-x-1/2 -translate-y-1/2 overflow-y-auto rounded-3xl border border-[#C5D2E7] bg-white p-5 text-[#14203C] shadow-2xl sm:p-6"
          onOpenAutoFocus={(event) => {
            event.preventDefault();
            nameInputRef.current?.focus();
          }}
        >
          <div className="flex items-start justify-between gap-3">
            <div className="min-w-0">
              <Dialog.Title className="text-base font-semibold">
                Crear carpeta
              </Dialog.Title>
              <Dialog.Description className="mt-1 text-sm text-slate-600">
                Organizá tus archivos por materia o curso.
              </Dialog.Description>
            </div>
            <Dialog.Close asChild>
              <button type="button" aria-label="Cerrar ventana" className="grid size-9 shrink-0 place-items-center rounded-md text-slate-600 hover:bg-slate-100">
                <X aria-hidden="true" className="size-4" />
              </button>
            </Dialog.Close>
          </div>

          <form onSubmit={handleSubmit} className="mt-5 space-y-5">
            <div>
              <label htmlFor="group-name" className="mb-2 block text-sm font-semibold">
                Nombre de la carpeta
              </label>
              <input
                ref={nameInputRef}
                id="group-name"
                type="text"
                value={name}
                onChange={(event) => { setName(event.target.value); setError(""); }}
                placeholder="Ej: Matemática - Álgebra"
                maxLength={60}
                required
                className="min-h-11 w-full rounded-lg border border-[#C5D2E7] bg-white px-3 py-2 text-sm placeholder:text-slate-500 focus-visible:border-primary"
              />
            </div>

            {showOrganizationOptions && (
              <>
                <fieldset>
                  <legend className="mb-3 text-sm font-semibold">Elegí un color</legend>
                  <div className="flex flex-wrap gap-3">
                    {GROUP_COLORS.map((item) => (
                      <button
                        key={item.value}
                        type="button"
                        title={item.name}
                        aria-label={`Elegir color ${item.name}`}
                        aria-pressed={color === item.value}
                        onClick={() => setColor(item.value)}
                        className={`grid size-10 place-items-center rounded-full ${color === item.value ? "ring-2 ring-slate-900 ring-offset-2" : "hover:opacity-80"}`}
                        style={{ backgroundColor: item.value }}
                      >
                        {color === item.value && <span aria-hidden="true" className="font-bold text-slate-950">✓</span>}
                      </button>
                    ))}
                  </div>
                  <p className="mt-2 text-xs text-slate-600">
                    Color seleccionado: {GROUP_COLORS.find((item) => item.value === color)?.name}
                  </p>
                </fieldset>
                <div>
                  <p className="mb-2 text-sm font-semibold">Agregar un PDF (opcional)</p>
                  <button type="button" onClick={() => fileInputRef.current?.click()} className="flex w-full flex-col items-center gap-2 rounded-lg border border-dashed border-[#C5D2E7] p-5 text-center hover:bg-slate-50">
                    {file ? <FileText aria-hidden="true" className="size-6 text-primary" /> : <Upload aria-hidden="true" className="size-6 text-primary" />}
                    <span className="break-all text-sm font-medium">{file ? file.name : "Seleccioná un archivo PDF"}</span>
                    <span className="text-xs text-slate-600">{file ? `${(file.size / (1024 * 1024)).toFixed(2)} MB` : "Máximo 10 MB"}</span>
                  </button>
                  <input ref={fileInputRef} type="file" accept="application/pdf,.pdf" onChange={handleFileChange} className="sr-only" tabIndex={-1} aria-label="Seleccionar archivo PDF" />
                  {file && (
                    <button type="button" onClick={() => { setFile(null); setError(""); if (fileInputRef.current) fileInputRef.current.value = ""; }} className="mt-2 text-sm font-medium text-red-700 hover:underline">
                      Quitar archivo
                    </button>
                  )}
                </div>
              </>
            )}

            {error && <p role="alert" className="text-sm font-medium text-red-700">{error}</p>}

            <div className="flex flex-wrap justify-end gap-2">
              <Button type="button" variant="lumi-outline" onClick={handleClose}>Cancelar</Button>
              <Button type="submit" variant="lumi-primary" disabled={!name.trim()} className="disabled:border-transparent disabled:bg-slate-300 disabled:text-slate-600 disabled:opacity-100">
                Crear carpeta
              </Button>
            </div>
          </form>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}
