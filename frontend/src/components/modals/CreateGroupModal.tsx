
"use client";

import { useRef, useState, type ChangeEvent, type FormEvent } from "react";
import { X, Upload, FileText, FolderPlus } from "lucide-react";

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
}

export default function CreateGroupModal({
  isOpen,
  onClose,
  onCreate,
}: CreateGroupModalProps) {
  const [name, setName] = useState("");
  const [color, setColor] = useState(GROUP_COLORS[0].value);
  const [file, setFile] = useState<File | null>(null);
  const [error, setError] = useState("");
  const fileInputRef = useRef<HTMLInputElement>(null);

  if (!isOpen) return null;

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
      setError("Ingresá un nombre para el grupo.");
      return;
    }

    onCreate({
      name: cleanName,
      color,
      file,
    });

    setName("");
    setColor(GROUP_COLORS[0].value);
    setFile(null);
    setError("");
  }

  function handleClose() {
    setName("");
    setColor(GROUP_COLORS[0].value);
    setFile(null);
    setError("");
    onClose();
  }

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4"
      onMouseDown={(event) => {
        if (event.target === event.currentTarget) handleClose();
      }}
    >
      <section
        role="dialog"
        aria-modal="true"
        aria-labelledby="create-group-title"
        className="w-full max-w-lg rounded-2xl bg-white p-6 text-gray-900 shadow-xl sm:p-8"
      >
        <div className="mb-6 flex items-start justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="rounded-xl bg-violet-100 p-3 text-violet-700">
              <FolderPlus size={24} aria-hidden="true" />
            </div>

            <div>
              <h2
                id="create-group-title"
                className="text-xl font-bold"
              >
                Crear grupo
              </h2>
              <p className="mt-1 text-sm text-gray-500">
                Organizá tus archivos por materia.
              </p>
            </div>
          </div>

          <button
            type="button"
            onClick={handleClose}
            aria-label="Cerrar ventana"
            className="rounded-lg p-2 text-gray-500 hover:bg-gray-100 focus-visible:outline-2 focus-visible:outline-violet-600"
          >
            <X size={20} />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-6">
          <div>
            <label
              htmlFor="group-name"
              className="mb-2 block text-sm font-semibold"
            >
              Nombre del grupo
            </label>

            <input
              id="group-name"
              type="text"
              value={name}
              onChange={(event) => {
                setName(event.target.value);
                setError("");
              }}
              placeholder="Ej.: Matemática"
              maxLength={60}
              required
              autoFocus
              className="w-full rounded-xl border border-gray-300 px-4 py-3 outline-none transition focus:border-violet-600 focus:ring-2 focus:ring-violet-100"
            />
          </div>

          <fieldset>
            <legend className="mb-3 text-sm font-semibold">
              Elegí un color
            </legend>

            <div className="flex flex-wrap gap-4">
              {GROUP_COLORS.map((item) => (
                <button
                  key={item.value}
                  type="button"
                  title={item.name}
                  aria-label={`Elegir color ${item.name}`}
                  aria-pressed={color === item.value}
                  onClick={() => setColor(item.value)}
                  className={`flex h-10 w-10 items-center justify-center rounded-full transition focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-violet-600 ${
                    color === item.value
                      ? "ring-2 ring-gray-900 ring-offset-2"
                      : "hover:scale-110"
                  }`}
                  style={{ backgroundColor: item.value }}
                >
                  {color === item.value && (
                    <span className="text-lg font-bold text-white">✓</span>
                  )}
                </button>
              ))}
            </div>

            <p className="mt-2 text-xs text-gray-500">
              Color seleccionado:{" "}
              {GROUP_COLORS.find((item) => item.value === color)?.name}
            </p>
          </fieldset>

          <div>
            <label className="mb-2 block text-sm font-semibold">
              Agregar un PDF (opcional)
            </label>

            <button
              type="button"
              onClick={() => fileInputRef.current?.click()}
              className="flex w-full flex-col items-center rounded-xl border-2 border-dashed border-gray-300 px-4 py-6 text-center transition hover:border-violet-500 hover:bg-violet-50 focus-visible:outline-2 focus-visible:outline-violet-600"
            >
              {file ? (
                <>
                  <FileText
                    size={28}
                    className="mb-2 text-violet-600"
                    aria-hidden="true"
                  />
                  <span className="break-all text-sm font-medium">
                    {file.name}
                  </span>
                  <span className="mt-1 text-xs text-gray-500">
                    {(file.size / (1024 * 1024)).toFixed(2)} MB
                  </span>
                </>
              ) : (
                <>
                  <Upload
                    size={28}
                    className="mb-2 text-gray-500"
                    aria-hidden="true"
                  />
                  <span className="text-sm font-medium">
                    Seleccioná un archivo PDF
                  </span>
                  <span className="mt-1 text-xs text-gray-500">
                    Máximo 10 MB
                  </span>
                </>
              )}
            </button>

            <input
              ref={fileInputRef}
              type="file"
              accept="application/pdf,.pdf"
              onChange={handleFileChange}
              className="sr-only"
              aria-label="Seleccionar archivo PDF"
            />

            {file && (
              <button
                type="button"
                onClick={() => {
                  setFile(null);
                  if (fileInputRef.current) {
                    fileInputRef.current.value = "";
                  }
                }}
                className="mt-2 text-sm font-medium text-red-600 hover:underline"
              >
                Quitar archivo
              </button>
            )}
          </div>

          {error && (
            <p role="alert" className="text-sm font-medium text-red-600">
              {error}
            </p>
          )}

          <div className="flex flex-col-reverse gap-3 sm:flex-row sm:justify-end">
            <button
              type="button"
              onClick={handleClose}
              className="rounded-xl border border-gray-300 px-5 py-3 font-medium hover:bg-gray-50 focus-visible:outline-2 focus-visible:outline-violet-600"
            >
              Cancelar
            </button>

            <button
              type="submit"
              className="rounded-xl bg-violet-600 px-5 py-3 font-semibold text-white transition hover:bg-violet-700 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-violet-600"
            >
              Crear grupo
            </button>
          </div>
        </form>
      </section>
    </div>
  );
}
