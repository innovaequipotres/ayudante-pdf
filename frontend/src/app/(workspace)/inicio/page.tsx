"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useRef, useState, type ChangeEvent, type DragEvent } from "react";
import { ArrowRight, ChevronRight, FileText, UploadCloud } from "lucide-react";
import { DEMO_MOCKS } from "@/lib/demoMocks";
import { useLumiStore } from "@/store/useLumiStore";
import type { LumiDocument } from "@/types";

const MAX_FILE_SIZE = 25 * 1024 * 1024;

const STATUS_STYLES: Record<LumiDocument["status"], string> = {
  Analizado: "bg-emerald-100 text-emerald-800",
  "En edición": "bg-blue-100 text-blue-800",
  Procesando: "bg-amber-100 text-amber-800",
};

export default function InicioPage() {
  const router = useRouter();
  const inputRef = useRef<HTMLInputElement>(null);
  const user = useLumiStore((state) => state.user);
  const documents = useLumiStore((state) => state.documents);
  const diagnostics = useLumiStore((state) => state.diagnostics);
  const setPendingUpload = useLumiStore((state) => state.setPendingUpload);
  const setDemoDocument = useLumiStore((state) => state.setDemoDocument);
  const [error, setError] = useState("");
  const [isDragging, setIsDragging] = useState(false);

  const firstName = user.fullName.trim().split(/\s+/)[0] || user.fullName;

  const selectFile = (file?: File) => {
    if (!file) return;

    if (!file.name.toLowerCase().endsWith(".pdf")) {
      setError("El archivo debe tener formato PDF.");
      return;
    }

    if (file.size > MAX_FILE_SIZE) {
      setError("El archivo supera el límite de 25 MB.");
      return;
    }

    const demo = DEMO_MOCKS[file.name];

    if (!demo) {
      setError("");
      alert("Para la demo solo se admiten los archivos de prueba.");
      return;
    }

    setError("");
    setPendingUpload(file);
    router.push("/analizando");
    window.setTimeout(() => {
      setDemoDocument(file.name);
      router.push(`/diagnostico/${demo.id}`);
    }, 3000);
  };

  const handleFileChange = (event: ChangeEvent<HTMLInputElement>) => {
    selectFile(event.currentTarget.files?.[0]);
    event.currentTarget.value = "";
  };

  const handleDragOver = (event: DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    setIsDragging(true);
  };

  const handleDrop = (event: DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    setIsDragging(false);
    selectFile(event.dataTransfer.files[0]);
  };

  const recentDocuments = documents.slice(0, 4);

  return (
    <main className="min-h-svh bg-[#f7fafc] text-slate-900">
      <div className="mx-auto w-full max-w-7xl px-4 pb-10 pt-8 sm:px-6 sm:pt-10">
        <section aria-labelledby="welcome-title">
          <h1 id="welcome-title" className="page-title">
            ¡Hola, {firstName}!
          </h1>
          <p className="page-subtitle mt-2">
            ¿Qué material querés analizar hoy?
          </p>

          <div
            onDragEnter={() => setIsDragging(true)}
            onDragOver={handleDragOver}
            onDragLeave={() => setIsDragging(false)}
            onDrop={handleDrop}
            className={`mx-auto mt-6 flex min-h-52 max-w-3xl flex-col items-center justify-center rounded-lg border-2 border-dashed px-5 py-8 text-center transition-colors sm:min-h-60 ${
              isDragging
                ? "border-blue-600 bg-blue-50"
                : "border-slate-500 bg-white/70"
            }`}
            aria-label="Zona para cargar un archivo PDF"
          >
            <UploadCloud
              aria-hidden="true"
              className="size-10 text-slate-800"
            />
            <input
              ref={inputRef}
              type="file"
              accept=".pdf,application/pdf"
              onChange={handleFileChange}
              className="sr-only"
              aria-label="Seleccionar archivo PDF"
            />
            <button
              type="button"
              onClick={() => inputRef.current?.click()}
              className="mt-3 min-h-11 rounded-md bg-slate-800 px-8 py-2.5 text-sm font-semibold text-white transition hover:bg-slate-700 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-blue-700"
            >
              Seleccionar archivo
            </button>
            <p className="mt-3 text-xs text-slate-600 sm:text-sm">
              Arrastrá tu archivo acá o seleccioná un PDF de hasta 25 MB.
            </p>
            {error && (
              <p role="alert" className="mt-3 text-sm font-medium text-red-700">
                {error}
              </p>
            )}
          </div>
        </section>

        <section
          aria-labelledby="recent-documents-title"
          className="mt-10 sm:mt-12"
        >
          <div className="mb-3 flex items-center justify-between gap-4">
            <h2
              id="recent-documents-title"
              className="text-sm font-semibold text-slate-900"
            >
              Tus últimos documentos
            </h2>
            <Link
              href="/archivos"
              className="inline-flex shrink-0 items-center gap-2 text-sm font-semibold text-slate-800 hover:text-blue-800"
            >
              Ver todos
              <ArrowRight aria-hidden="true" className="size-4" />
            </Link>
          </div>

          {recentDocuments.length > 0 ? (
            <ul className="divide-y divide-slate-200 overflow-hidden rounded-md border border-slate-300 bg-white">
              {recentDocuments.map((document) => {
                const observationCount =
                  diagnostics.find((item) => item.documentId === document.id)
                    ?.barriers.length ?? 0;

                return (
                  <li key={document.id}>
                    <Link
                      href={`/diagnostico/${document.id}`}
                      className="grid min-h-16 grid-cols-[minmax(0,1fr)_auto] items-center gap-x-3 gap-y-1 px-3 py-3 transition hover:bg-slate-50 focus-visible:bg-slate-50 sm:grid-cols-[minmax(0,1fr)_auto_auto_auto] sm:gap-5 sm:px-4"
                    >
                      <span className="flex min-w-0 items-center gap-3">
                        <span className="grid size-9 shrink-0 place-items-center rounded bg-indigo-50 text-indigo-600">
                          <FileText aria-hidden="true" className="size-5" />
                        </span>
                        <span className="truncate text-sm font-semibold text-slate-800">
                          {document.name}
                        </span>
                      </span>
                      <span
                        className={`row-start-1 rounded-full px-3 py-1 text-center text-xs font-semibold ${STATUS_STYLES[document.status]}`}
                      >
                        {document.status}
                      </span>
                      <span className="col-span-2 text-xs text-slate-500 sm:col-span-1 sm:col-start-2 sm:row-start-1 sm:text-sm">
                        {document.date}
                        {observationCount > 0 && (
                          <span className="before:px-1 before:content-['·']">
                            {observationCount}{" "}
                            {observationCount === 1
                              ? "observación"
                              : "observaciones"}
                          </span>
                        )}
                      </span>
                      <ChevronRight
                        aria-hidden="true"
                        className="hidden size-5 text-slate-400 sm:block"
                      />
                    </Link>
                  </li>
                );
              })}
            </ul>
          ) : (
            <p className="rounded-md border border-slate-300 bg-white px-4 py-6 text-sm text-slate-600">
              Todavía no tenés documentos. Cargá un PDF para empezar.
            </p>
          )}
        </section>
      </div>
    </main>
  );
}
