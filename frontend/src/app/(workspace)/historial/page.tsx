"use client";

import Link from "next/link";
import { useMemo, useState } from "react";
import {
  Download,
  EllipsisVertical,
  FileText,
  Pencil,
  Search,
} from "lucide-react";
import { useLumiStore } from "@/store/useLumiStore";
import type { LumiDocument } from "@/types";

type HistoryStatus = LumiDocument["status"] | "Guardado";
type StatusFilter = "Todos" | "Analizados" | "En edición" | "Guardados";

interface HistoryDocument {
  id: string;
  sourceDocumentId: string;
  name: string;
  date: string;
  status: HistoryStatus;
  content: string;
}

const FILTERS: StatusFilter[] = [
  "Todos",
  "Analizados",
  "En edición",
  "Guardados",
];

const STATUS_STYLES: Record<HistoryStatus, string> = {
  Analizado: "bg-emerald-100 text-emerald-800",
  "En edición": "bg-blue-100 text-blue-800",
  Procesando: "bg-amber-100 text-amber-800",
  Guardado: "bg-fuchsia-100 text-fuchsia-800",
};

const SAVED_DOCUMENTS: HistoryDocument[] = [
  {
    id: "guardado-guia-funciones",
    sourceDocumentId: "documento-guia-funciones",
    name: "Guia_Funciones_guardada.pdf",
    date: "20 de octubre de 2026",
    status: "Guardado",
    content:
      "Introducción a las funciones\n\nUna función relaciona cada elemento de un conjunto con un único elemento de otro conjunto.",
  },
];

function downloadDocument(document: HistoryDocument) {
  const blob = new Blob([document.content], {
    type: "text/plain;charset=utf-8",
  });
  const url = URL.createObjectURL(blob);
  const link = window.document.createElement("a");

  link.href = url;
  link.download = `${document.name.replace(/\.pdf$/i, "")}.txt`;
  link.click();
  window.setTimeout(() => URL.revokeObjectURL(url), 0);
}

export default function HistorialPage() {
  const documents = useLumiStore((state) => state.documents);
  const [search, setSearch] = useState("");
  const [activeFilter, setActiveFilter] = useState<StatusFilter>("Todos");

  const historyDocuments = useMemo<HistoryDocument[]>(
    () => [
      ...documents.map((document) => ({
        id: document.id,
        sourceDocumentId: document.id,
        name: document.name,
        date: document.date,
        status: document.status,
        content: document.modifiedContent || document.originalContent,
      })),
      ...SAVED_DOCUMENTS,
    ],
    [documents],
  );

  const visibleDocuments = useMemo(() => {
    const normalizedSearch = search.trim().toLocaleLowerCase("es");

    return historyDocuments.filter((document) => {
      const matchesSearch = document.name
        .toLocaleLowerCase("es")
        .includes(normalizedSearch);
      const matchesFilter =
        activeFilter === "Todos" ||
        (activeFilter === "Analizados" && document.status === "Analizado") ||
        (activeFilter === "En edición" && document.status === "En edición") ||
        (activeFilter === "Guardados" && document.status === "Guardado");

      return matchesSearch && matchesFilter;
    });
  }, [activeFilter, historyDocuments, search]);

  return (
    <main className="min-h-svh bg-[#f7fafc] py-8 text-slate-900 sm:py-10">
      <div className="mx-auto w-full max-w-7xl px-4 sm:px-6">
        <header>
          <h1 className="page-title">Historial de documentos</h1>
          <p className="page-subtitle mt-2">
            Los materiales que analizaste. El original se conserva siempre.
          </p>
        </header>

        <section
          aria-label="Buscar y filtrar documentos"
          className="mt-6 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between"
        >
          <div
            aria-label="Filtrar por estado"
            className="flex w-full overflow-x-auto rounded-md bg-slate-200 p-1 sm:w-auto"
          >
            {FILTERS.map((filter) => {
              const isActive = activeFilter === filter;

              return (
                <button
                  key={filter}
                  type="button"
                  aria-pressed={isActive}
                  onClick={() => setActiveFilter(filter)}
                  className={`min-h-10 shrink-0 rounded px-4 text-xs font-semibold transition-colors focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-blue-700 ${
                    isActive
                      ? "bg-slate-700 text-white"
                      : "text-slate-700 hover:bg-white/70"
                  }`}
                >
                  {filter}
                </button>
              );
            })}
          </div>

          <label className="relative block w-full sm:max-w-sm sm:flex-1">
            <Search
              aria-hidden="true"
              className="absolute left-3 top-1/2 size-4 -translate-y-1/2 text-slate-600"
            />
            <span className="sr-only">Buscar por nombre</span>
            <input
              type="search"
              value={search}
              onChange={(event) => setSearch(event.currentTarget.value)}
              placeholder="Buscar por nombre..."
              className="min-h-11 w-full rounded-md border border-slate-500 bg-white py-2 pl-10 pr-3 text-sm text-slate-900 placeholder:text-slate-500 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-blue-700"
            />
          </label>
        </section>

        <section
          aria-label="Documentos del historial"
          className="mt-8 overflow-hidden rounded-md border border-slate-300 bg-white sm:mt-10"
        >
          {visibleDocuments.length > 0 ? (
            <div className="overflow-x-auto">
              <table className="w-full min-w-165 border-collapse text-left">
                <thead className="border-b border-slate-200 text-xs text-slate-700">
                  <tr>
                    <th scope="col" className="px-4 py-3 font-semibold">
                      Nombre
                    </th>
                    <th scope="col" className="px-4 py-3 font-semibold">
                      Fecha
                    </th>
                    <th scope="col" className="px-4 py-3 font-semibold">
                      Estado
                    </th>
                    <th
                      scope="col"
                      className="px-4 py-3 text-right font-semibold"
                    >
                      Acciones
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-200">
                  {visibleDocuments.map((document) => (
                    <tr
                      key={document.id}
                      className="transition-colors hover:bg-slate-50"
                    >
                      <td className="max-w-72 px-4 py-3">
                        <span className="flex min-w-0 items-center gap-3">
                          <span className="grid size-9 shrink-0 place-items-center rounded bg-indigo-50 text-indigo-600">
                            <FileText aria-hidden="true" className="size-5" />
                          </span>
                          <span className="truncate text-sm font-semibold text-slate-800">
                            {document.name}
                          </span>
                        </span>
                      </td>
                      <td className="whitespace-nowrap px-4 py-3 text-sm text-slate-600">
                        {document.date}
                      </td>
                      <td className="px-4 py-3">
                        <span
                          className={`inline-flex rounded-full px-3 py-1 text-xs font-semibold ${STATUS_STYLES[document.status]}`}
                        >
                          {document.status}
                        </span>
                      </td>
                      <td className="px-4 py-3">
                        <div className="flex items-center justify-end gap-1">
                          <Link
                            href={`/editar/${document.sourceDocumentId}`}
                            aria-label={`Editar ${document.name}`}
                            title="Editar documento"
                            className="grid size-9 place-items-center rounded text-slate-600 transition hover:bg-blue-50 hover:text-blue-800 focus-visible:outline-2 focus-visible:outline-blue-700"
                          >
                            <Pencil aria-hidden="true" className="size-4" />
                          </Link>
                          <button
                            type="button"
                            onClick={() => downloadDocument(document)}
                            aria-label={`Descargar ${document.name} como texto`}
                            title="Descargar como texto"
                            className="grid size-9 place-items-center rounded text-slate-600 transition hover:bg-emerald-50 hover:text-emerald-800 focus-visible:outline-2 focus-visible:outline-emerald-700"
                          >
                            <Download aria-hidden="true" className="size-4" />
                          </button>
                          <details className="relative">
                            <summary
                              aria-label={`Más acciones para ${document.name}`}
                              title="Más acciones"
                              className="grid size-9 cursor-pointer list-none place-items-center rounded text-slate-600 transition hover:bg-slate-100 focus-visible:outline-2 focus-visible:outline-blue-700 [&::-webkit-details-marker]:hidden"
                            >
                              <EllipsisVertical
                                aria-hidden="true"
                                className="size-4"
                              />
                            </summary>
                            <div className="absolute right-0 z-10 mt-1 min-w-40 rounded-md border border-slate-200 bg-white p-1 shadow-lg">
                              <Link
                                href={`/diagnostico/${document.sourceDocumentId}`}
                                className="block rounded px-3 py-2 text-sm text-slate-700 hover:bg-slate-50 focus-visible:outline-2 focus-visible:outline-blue-700"
                              >
                                Ver diagnóstico
                              </Link>
                            </div>
                          </details>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <p className="px-4 py-10 text-center text-sm text-slate-600">
              No encontramos documentos con esos criterios.
            </p>
          )}
        </section>
      </div>
    </main>
  );
}
