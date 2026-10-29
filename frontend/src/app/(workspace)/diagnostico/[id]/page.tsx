"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import {
  ArrowLeft,
  ArrowRight,
  Check,
  CheckCircle2,
  ChevronDown,
  CircleAlert,
  FileText,
  Info,
  ScanSearch,
  TriangleAlert,
} from "lucide-react";
import type { Barrier } from "@/types";
import { useLumiStore } from "@/store/useLumiStore";

type SeverityFilter = "Todas" | Barrier["severity"];

const SEVERITIES: Barrier["severity"][] = ["Alta", "Media", "Baja"];

const SEVERITY_STYLES: Record<Barrier["severity"], string> = {
  Alta: "border-red-200 bg-red-50 text-red-800",
  Media: "border-amber-200 bg-amber-50 text-amber-800",
  Baja: "border-violet-200 bg-violet-50 text-violet-800",
};

const SEVERITY_ICON_STYLES: Record<Barrier["severity"], string> = {
  Alta: "text-red-600",
  Media: "text-amber-600",
  Baja: "text-violet-600",
};

const STATUS_STYLES: Record<Barrier["status"], string> = {
  Pendiente: "bg-slate-100 text-slate-700",
  Aplicada: "bg-emerald-50 text-emerald-800",
  Ignorada: "bg-slate-100 text-slate-500",
};

const BARRIER_TITLES: Record<string, string> = {
  "Error de claridad en el texto": "Simplificar el vocabulario y las consignas",
  "Uso del lenguaje inclusivo": "Usar un lenguaje inclusivo",
  "Falta de jerarquía en los títulos": "Organizar la jerarquía de los títulos",
};

const SEVERITY_DESCRIPTIONS: Record<Barrier["severity"], string> = {
  Alta: "Puede impedir el acceso o dificultar gravemente la comprensión.",
  Media: "Puede generar dificultades de lectura, orientación o comprensión.",
  Baja: "Es una mejora sugerida que no representa necesariamente una barrera grave.",
};

function getSeverityIcon(severity: Barrier["severity"]) {
  if (severity === "Alta") return TriangleAlert;
  if (severity === "Media") return CircleAlert;
  return Info;
}

export default function DiagnosticoGeneralPage() {
  const { id } = useParams<{ id: string }>();
  const [severityFilter, setSeverityFilter] = useState<SeverityFilter>("Todas");
  const activeDocument = useLumiStore((state) => state.activeDocument);
  const activeDiagnostic = useLumiStore((state) => state.activeDiagnostic);
  const routeDocumentFromStore = useLumiStore((state) =>
    state.documents.find((document) => document.id === id),
  );
  const routeDiagnosticFromStore = useLumiStore((state) =>
    state.diagnostics.find((diagnostic) => diagnostic.documentId === id),
  );
  const setActiveDocument = useLumiStore((state) => state.setActiveDocument);

  useEffect(() => {
    setActiveDocument(id);
  }, [id, setActiveDocument]);

  const routeDocument =
    routeDocumentFromStore ??
    (activeDocument?.id === id ? activeDocument : null);
  const diagnostic = routeDocument
    ? activeDiagnostic?.documentId === id
      ? activeDiagnostic
      : (routeDiagnosticFromStore ?? null)
    : null;
  const barriers = diagnostic?.barriers ?? [];
  const score = diagnostic
    ? Math.max(0, Math.min(100, diagnostic.globalScore))
    : 0;
  const correctedCount = barriers.filter(
    (barrier) => barrier.status === "Aplicada",
  ).length;
  const groupedBarriers = barriers.reduce<Map<string, Barrier[]>>(
    (groups, barrier) => {
      const group = groups.get(barrier.type) ?? [];
      group.push(barrier);
      groups.set(barrier.type, group);
      return groups;
    },
    new Map(),
  );
  const visibleBarriers = barriers.filter(
    (barrier) =>
      severityFilter === "Todas" || barrier.severity === severityFilter,
  );

  if (!routeDocument) {
    return (
      <main className="min-h-screen bg-slate-50 px-4 py-10 text-slate-900 sm:px-6">
        <section className="mx-auto max-w-2xl rounded-xl border border-slate-200 bg-white p-8 text-center shadow-sm">
          <div className="mx-auto grid size-12 place-items-center rounded-lg bg-slate-100 text-slate-600">
            <FileText aria-hidden="true" className="size-6" />
          </div>
          <h1 className="mt-4 text-xl font-bold">
            No encontramos este documento
          </h1>
          <p className="mt-2 text-sm leading-6 text-slate-600">
            Revisá el enlace o volvé a tus archivos para elegir otro material.
          </p>
          <Link
            href="/archivos"
            className="mt-6 inline-flex min-h-11 items-center justify-center gap-2 rounded-lg bg-emerald-700 px-4 py-2.5 text-sm font-semibold text-white transition hover:bg-emerald-800"
          >
            <ArrowLeft aria-hidden="true" className="size-4" />
            Volver a mis archivos
          </Link>
        </section>
      </main>
    );
  }

  return (
    <main className="min-h-screen bg-slate-50 px-4 py-6 text-slate-900 sm:px-6 lg:px-8">
      <div className="mx-auto max-w-7xl">
        <Link
          href="/archivos"
          className="mb-5 inline-flex items-center gap-2 rounded-md text-sm font-medium text-slate-600 transition hover:text-emerald-800"
        >
          <ArrowLeft aria-hidden="true" className="size-4" />
          Mis archivos
        </Link>

        <header className="mb-6 flex flex-col justify-between gap-5 rounded-xl border border-slate-200 bg-white p-5 shadow-sm sm:flex-row sm:items-center sm:p-6">
          <div className="flex min-w-0 items-center gap-4">
            <span className="grid size-12 shrink-0 place-items-center rounded-lg bg-blue-50 text-blue-700">
              <FileText aria-hidden="true" className="size-6" />
            </span>
            <div className="min-w-0">
              <p className="text-xs font-semibold uppercase text-emerald-800">
                Diagnóstico general
              </p>
              <h1 className="mt-1 truncate text-lg font-bold sm:text-xl">
                {routeDocument.name.replace(/\.pdf$/i, "")}
              </h1>
              <p className="mt-1 text-sm text-slate-500">
                {routeDocument.subject} <span aria-hidden="true">·</span>{" "}
                {routeDocument.date} <span aria-hidden="true">·</span>{" "}
                {routeDocument.size}
              </p>
            </div>
          </div>

          <Link
            href={`/comparador/${encodeURIComponent(routeDocument.id)}`}
            className="inline-flex min-h-11 shrink-0 items-center justify-center gap-2 rounded-lg bg-emerald-700 px-5 py-3 text-sm font-semibold text-white shadow-sm transition hover:bg-emerald-800 focus-visible:outline-offset-2"
          >
            <ScanSearch aria-hidden="true" className="size-4" />
            Revisar propuesta
            <ArrowRight aria-hidden="true" className="size-4" />
          </Link>
        </header>

        {!diagnostic ? (
          <section className="rounded-xl border border-blue-200 bg-blue-50 p-5 text-blue-950 sm:p-6">
            <div className="flex items-start gap-3">
              <Info
                aria-hidden="true"
                className="mt-0.5 size-5 shrink-0 text-blue-700"
              />
              <div>
                <h2 className="font-semibold">
                  Todavía no hay un diagnóstico disponible
                </h2>
                <p className="mt-1 text-sm leading-6">
                  Este documento aún no tiene un análisis asociado. Cuando esté
                  listo, vas a poder consultar acá sus resultados y barreras.
                </p>
              </div>
            </div>
          </section>
        ) : (
          <>
            <section
              aria-labelledby="resumen-titulo"
              className="mb-6 grid gap-5 lg:grid-cols-2"
            >
              <article className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm sm:p-6">
                <div className="mb-5">
                  <h2 id="resumen-titulo" className="text-lg font-bold">
                    Resumen general
                  </h2>
                  <p className="mt-1 text-sm text-slate-500">
                    Puntaje y legibilidad del material analizado.
                  </p>
                </div>

                <div className="grid items-center gap-6 sm:grid-cols-[minmax(150px,0.8fr)_1fr]">
                  <div className="flex justify-center">
                    <div
                      role="img"
                      aria-label={`Puntaje de accesibilidad: ${score} de 100`}
                      className="grid size-36 place-items-center rounded-full p-2"
                      style={{
                        background: `conic-gradient(#15803d ${score}%, #e2e8f0 ${score}% 100%)`,
                      }}
                    >
                      <div className="grid size-full place-content-center rounded-full bg-white text-center">
                        <span className="text-4xl font-bold tabular-nums">
                          {score}
                        </span>
                        <span className="text-sm font-medium text-slate-500">
                          / 100
                        </span>
                      </div>
                    </div>
                  </div>

                  <div className="space-y-5">
                    <div>
                      <div className="flex items-center justify-between gap-3 text-sm">
                        <span className="font-medium text-slate-700">
                          Legibilidad
                        </span>
                        <span className="font-bold tabular-nums text-slate-900">
                          {diagnostic.readabilityPercentage}%
                        </span>
                      </div>
                      <div
                        className="mt-2 h-2 overflow-hidden rounded-full bg-slate-100"
                        role="progressbar"
                        aria-label="Porcentaje de legibilidad"
                        aria-valuemin={0}
                        aria-valuemax={100}
                        aria-valuenow={diagnostic.readabilityPercentage}
                      >
                        <div
                          className="h-full rounded-full bg-blue-600"
                          style={{
                            width: `${diagnostic.readabilityPercentage}%`,
                          }}
                        />
                      </div>
                    </div>

                    <div className="grid grid-cols-2 gap-3">
                      <div className="rounded-lg bg-slate-50 p-3">
                        <p className="text-xs font-medium text-slate-500">
                          Barreras detectadas
                        </p>
                        <p className="mt-1 text-2xl font-bold tabular-nums">
                          {barriers.length}
                        </p>
                      </div>
                      <div className="rounded-lg bg-emerald-50 p-3">
                        <p className="text-xs font-medium text-emerald-800">
                          Barreras corregidas
                        </p>
                        <p className="mt-1 text-2xl font-bold tabular-nums text-emerald-900">
                          {correctedCount}
                        </p>
                      </div>
                    </div>
                  </div>
                </div>
              </article>

              <article className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm sm:p-6">
                <div className="mb-5 flex items-start justify-between gap-3">
                  <div>
                    <h2 className="text-lg font-bold">Barreras detectadas</h2>
                    <p className="mt-1 text-sm text-slate-500">
                      Hallazgos agrupados por tipo.
                    </p>
                  </div>
                  <span className="rounded-full bg-slate-100 px-2.5 py-1 text-xs font-semibold text-slate-700">
                    {barriers.length} en total
                  </span>
                </div>

                {groupedBarriers.size > 0 ? (
                  <ul className="divide-y divide-slate-100">
                    {Array.from(groupedBarriers.entries()).map(
                      ([type, items]) => (
                        <li
                          key={type}
                          className="flex items-center justify-between gap-3 py-3 first:pt-0 last:pb-0"
                        >
                          <span className="flex min-w-0 items-center gap-3">
                            <span
                              aria-hidden="true"
                              className="size-2.5 shrink-0 rounded-full bg-slate-300"
                            />
                            <span className="truncate text-sm font-medium text-slate-700">
                              {type}
                            </span>
                          </span>
                          <span className="shrink-0 rounded-full bg-slate-100 px-2.5 py-1 text-xs font-semibold tabular-nums text-slate-600">
                            {items.length}
                          </span>
                        </li>
                      ),
                    )}
                  </ul>
                ) : (
                  <p className="rounded-lg bg-emerald-50 p-4 text-sm text-emerald-900">
                    No se detectaron barreras en este análisis.
                  </p>
                )}
              </article>
            </section>

            <section aria-labelledby="barreras-titulo">
              <div className="mb-4 rounded-xl border border-slate-200 bg-white p-4 shadow-sm sm:flex sm:items-center sm:justify-between sm:gap-6">
                <div className="flex items-start gap-3">
                  <span className="grid size-9 shrink-0 place-items-center rounded-full bg-slate-900 text-white">
                    <Info aria-hidden="true" className="size-4" />
                  </span>
                  <div>
                    <h2 id="barreras-titulo" className="text-sm font-bold">
                      ¿Cómo se clasifican las barreras?
                    </h2>
                    <p className="mt-1 text-xs leading-5 text-slate-500">
                      La severidad indica cuánto puede afectar el acceso y la
                      comprensión del material.
                    </p>
                  </div>
                </div>

                <div
                  className="mt-4 flex flex-wrap gap-2 sm:mt-0 sm:justify-end"
                  role="group"
                  aria-label="Filtrar barreras por severidad"
                >
                  {(["Todas", ...SEVERITIES] as SeverityFilter[]).map(
                    (severity) => {
                      const count =
                        severity === "Todas"
                          ? barriers.length
                          : barriers.filter(
                              (barrier) => barrier.severity === severity,
                            ).length;
                      const isSelected = severityFilter === severity;

                      return (
                        <button
                          key={severity}
                          type="button"
                          aria-pressed={isSelected}
                          onClick={() => setSeverityFilter(severity)}
                          className={`inline-flex min-h-9 items-center gap-2 rounded-lg border px-3 py-1.5 text-xs font-semibold transition focus-visible:outline-offset-2 ${
                            isSelected
                              ? "border-slate-900 bg-slate-900 text-white"
                              : "border-slate-200 bg-white text-slate-600 hover:bg-slate-50"
                          }`}
                        >
                          {severity}
                          <span
                            className={`tabular-nums ${isSelected ? "text-slate-300" : "text-slate-400"}`}
                          >
                            {count}
                          </span>
                        </button>
                      );
                    },
                  )}
                </div>
              </div>

              <div className="space-y-3">
                {visibleBarriers.map((barrier) => {
                  const SeverityIcon = getSeverityIcon(barrier.severity);

                  return (
                    <details
                      key={barrier.id}
                      className="group rounded-xl border border-slate-200 bg-white shadow-sm"
                    >
                      <summary className="flex cursor-pointer list-none items-center gap-3 p-4 marker:hidden sm:gap-4 sm:p-5">
                        <span
                          className={`grid size-10 shrink-0 place-items-center rounded-full ${SEVERITY_STYLES[barrier.severity]}`}
                        >
                          <SeverityIcon
                            aria-hidden="true"
                            className={`size-5 ${SEVERITY_ICON_STYLES[barrier.severity]}`}
                          />
                        </span>
                        <span className="min-w-0 flex-1">
                          <span className="flex flex-wrap items-center gap-2">
                            <span className="font-semibold text-slate-900">
                              {BARRIER_TITLES[barrier.type] ?? barrier.type}
                            </span>
                            <span
                              className={`rounded-full border px-2 py-0.5 text-xs font-semibold ${SEVERITY_STYLES[barrier.severity]}`}
                            >
                              {barrier.severity}
                            </span>
                          </span>
                          <span className="mt-1 block text-sm text-slate-500">
                            {barrier.type}
                          </span>
                        </span>
                        <span
                          className={`hidden shrink-0 rounded-full px-2.5 py-1 text-xs font-medium sm:inline-flex ${STATUS_STYLES[barrier.status]}`}
                        >
                          {barrier.status}
                        </span>
                        <ChevronDown
                          aria-hidden="true"
                          className="size-5 shrink-0 text-slate-400 transition-transform group-open:rotate-180"
                        />
                      </summary>

                      <div className="space-y-4 border-t border-slate-100 px-4 py-4 sm:px-5 sm:py-5">
                        <span
                          className={`inline-flex rounded-full px-2.5 py-1 text-xs font-medium sm:hidden ${STATUS_STYLES[barrier.status]}`}
                        >
                          {barrier.status}
                        </span>
                        <div>
                          <p className="text-xs font-semibold uppercase text-slate-500">
                            Fragmento detectado
                          </p>
                          <blockquote className="mt-2 border-l-2 border-slate-300 pl-3 text-sm leading-6 text-slate-700">
                            “{barrier.detectedFragment}”
                          </blockquote>
                        </div>
                        <div className="rounded-lg border border-blue-100 bg-blue-50 p-4">
                          <p className="text-xs font-semibold uppercase text-blue-800">
                            Sugerencia
                          </p>
                          <p className="mt-2 text-sm leading-6 text-blue-950">
                            {barrier.suggestion}
                          </p>
                        </div>
                        <p className="flex items-start gap-2 text-xs leading-5 text-slate-500">
                          <SeverityIcon
                            aria-hidden="true"
                            className={`mt-0.5 size-4 shrink-0 ${SEVERITY_ICON_STYLES[barrier.severity]}`}
                          />
                          {SEVERITY_DESCRIPTIONS[barrier.severity]}
                        </p>
                      </div>
                    </details>
                  );
                })}

                {visibleBarriers.length === 0 && (
                  <div className="rounded-xl border border-dashed border-slate-300 bg-white px-5 py-10 text-center">
                    <CheckCircle2
                      aria-hidden="true"
                      className="mx-auto size-8 text-emerald-600"
                    />
                    <p className="mt-3 font-semibold text-slate-800">
                      No hay barreras de severidad{" "}
                      {severityFilter.toLowerCase()}.
                    </p>
                    <button
                      type="button"
                      onClick={() => setSeverityFilter("Todas")}
                      className="mt-3 rounded-sm text-sm font-semibold text-emerald-800 underline underline-offset-4 hover:text-emerald-900"
                    >
                      Ver todas las barreras
                    </button>
                  </div>
                )}
              </div>
            </section>

            <p className="mt-6 flex items-start gap-2 text-xs leading-5 text-slate-500">
              <Check
                aria-hidden="true"
                className="mt-0.5 size-4 shrink-0 text-emerald-700"
              />
              Las sugerencias son orientativas. Vos conservás la decisión final
              sobre cada cambio.
            </p>
          </>
        )}
      </div>
    </main>
  );
}
