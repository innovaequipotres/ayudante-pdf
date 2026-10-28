"use client";

import { useState } from "react";
import Link from "next/link";
import {
  ArrowRight,
  Check,
  FileText,
  ScanSearch,
  ShieldCheck,
  Sparkles,
} from "lucide-react";

const promises = [
  "Detectá barreras de lectura y estructura",
  "Recibí sugerencias claras para cada hallazgo",
  "Conservá el control de cada decisión",
  "Prepará materiales para más estudiantes",
];

type PreviewMode = "documento" | "diagnostico";

export default function HeroSection() {
  const [previewMode, setPreviewMode] = useState<PreviewMode>("documento");

  return (
    <section className="relative isolate overflow-hidden bg-linear-to-br from-blue-700 via-indigo-800 to-slate-900 text-white">
      <div
        aria-hidden="true"
        className="absolute -right-32 -top-40 size-120 rounded-full border border-white/10"
      />
      <div
        aria-hidden="true"
        className="absolute -right-16 -top-24 size-88 rounded-full border border-emerald-300/15"
      />
      <div className="relative mx-auto grid max-w-7xl items-center gap-14 px-5 py-16 sm:px-8 sm:py-20 lg:grid-cols-[1.05fr_0.95fr] lg:gap-16 lg:py-24">
        <div className="max-w-2xl">
          <p className="mb-5 inline-flex items-center gap-2 rounded-full border border-white/20 bg-white/10 px-3.5 py-2 text-sm font-semibold text-blue-100">
            <Sparkles aria-hidden="true" className="size-4 text-emerald-300" />
            Accesibilidad educativa, con IA como aliada
          </p>
          <h1 className="max-w-xl text-4xl font-bold leading-tight text-white sm:text-5xl lg:text-6xl">
            Tu PDF, más accesible, preciso e inclusivo.
          </h1>
          <p className="mt-6 max-w-xl text-lg leading-8 text-blue-100 sm:text-xl">
            LUMI te ayuda a detectar barreras y adaptar materiales educativos
            con sugerencias prácticas, para que cada estudiante pueda aprender a
            su manera.
          </p>
          <ul className="mt-8 grid gap-3 sm:grid-cols-2">
            {promises.map((promise) => (
              <li
                key={promise}
                className="flex items-start gap-2.5 text-sm leading-6 text-blue-50"
              >
                <span className="mt-0.5 grid size-5 shrink-0 place-items-center rounded-full bg-emerald-400 text-slate-950">
                  <Check
                    aria-hidden="true"
                    className="size-3.5"
                    strokeWidth={3}
                  />
                </span>
                {promise}
              </li>
            ))}
          </ul>
          <div className="mt-9 flex flex-col gap-3 sm:flex-row">
            <Link
              href="#contacto"
              className="inline-flex min-h-12 items-center justify-center gap-2 rounded-lg bg-white px-5 py-3 font-semibold text-blue-800 shadow-lg shadow-blue-950/20 transition hover:bg-blue-50 focus-visible:outline-white"
            >
              Comenzar ahora
              <ArrowRight aria-hidden="true" className="size-4" />
            </Link>
            <Link
              href="#como-funciona"
              className="inline-flex min-h-12 items-center justify-center rounded-lg border border-white/40 px-5 py-3 font-semibold text-white transition hover:bg-white/10"
            >
              Ver cómo funciona
            </Link>
          </div>
          <p className="mt-4 text-sm text-blue-200">
            Una herramienta de apoyo: vos conservás siempre la decisión final.
          </p>
        </div>

        <div className="mx-auto w-full max-w-xl rounded-2xl border border-white/30 bg-white p-3 text-slate-900 shadow-2xl shadow-slate-950/30 sm:p-5">
          <div className="flex items-center justify-between gap-3 border-b border-slate-100 px-2 pb-4">
            <div className="flex items-center gap-3">
              <span className="grid size-10 place-items-center rounded-xl bg-blue-50 text-blue-700">
                <FileText aria-hidden="true" className="size-5" />
              </span>
              <div>
                <p className="font-semibold text-slate-900">
                  Unidad 3 · Ecosistemas.pdf
                </p>
                <p className="mt-0.5 text-xs text-slate-500">
                  Vista demostrativa · 8 páginas
                </p>
              </div>
            </div>
            <span className="hidden items-center gap-1.5 rounded-full bg-emerald-50 px-2.5 py-1.5 text-xs font-semibold text-emerald-800 sm:inline-flex">
              <ShieldCheck aria-hidden="true" className="size-3.5" />
              Revisión sugerida
            </span>
          </div>
          <div
            className="flex gap-2 border-b border-slate-100 px-2 py-3"
            aria-label="Vista del documento"
          >
            <button
              type="button"
              aria-pressed={previewMode === "documento"}
              onClick={() => setPreviewMode("documento")}
              className={`rounded-md px-3 py-2 text-sm font-semibold transition focus-visible:ring-2 focus-visible:ring-blue-600 ${previewMode === "documento" ? "bg-blue-600 text-white" : "text-slate-600 hover:bg-slate-100"}`}
            >
              Vista previa
            </button>
            <button
              type="button"
              aria-pressed={previewMode === "diagnostico"}
              onClick={() => setPreviewMode("diagnostico")}
              className={`rounded-md px-3 py-2 text-sm font-semibold transition focus-visible:ring-2 focus-visible:ring-blue-600 ${previewMode === "diagnostico" ? "bg-blue-600 text-white" : "text-slate-600 hover:bg-slate-100"}`}
            >
              Diagnóstico
            </button>
          </div>
          {previewMode === "documento" ? (
            <div
              className="grid min-h-64 grid-cols-[1fr_0.72fr] gap-3 p-2 sm:min-h-72 sm:gap-4 sm:p-3"
              aria-live="polite"
            >
              <div className="rounded-lg border border-slate-200 bg-slate-50 p-4 sm:p-5">
                <div className="mb-4 h-2.5 w-2/3 rounded-full bg-blue-200" />
                <p className="text-sm font-bold text-slate-800">
                  Los ecosistemas
                </p>
                <div className="mt-3 space-y-2.5" aria-hidden="true">
                  <div className="h-2 w-full rounded-full bg-slate-200" />
                  <div className="h-2 w-11/12 rounded-full bg-slate-200" />
                  <div className="h-2 w-4/5 rounded-full bg-slate-200" />
                </div>
                <div className="mt-5 grid aspect-[1.5] place-items-center rounded-md bg-linear-to-br from-emerald-100 via-sky-100 to-blue-200">
                  <div className="grid size-12 place-items-center rounded-full bg-white/80 text-emerald-700 shadow-sm">
                    <Sparkles aria-hidden="true" className="size-6" />
                  </div>
                </div>
                <p className="mt-3 text-xs leading-5 text-slate-600">
                  Cada elemento cumple una función dentro de su ambiente.
                </p>
              </div>
              <div className="flex flex-col justify-center gap-3 py-2">
                <div className="rounded-lg bg-emerald-50 p-3.5">
                  <p className="text-xs font-bold uppercase text-emerald-800">
                    Estructura
                  </p>
                  <p className="mt-1.5 text-sm leading-5 text-slate-700">
                    Título principal identificado
                  </p>
                </div>
                <div className="rounded-lg bg-amber-50 p-3.5">
                  <p className="text-xs font-bold uppercase text-amber-800">
                    Imagen
                  </p>
                  <p className="mt-1.5 text-sm leading-5 text-slate-700">
                    Revisá si necesita descripción
                  </p>
                </div>
                <div className="rounded-lg bg-blue-50 p-3.5">
                  <p className="text-xs font-bold uppercase text-blue-800">
                    Lectura
                  </p>
                  <p className="mt-1.5 text-sm leading-5 text-slate-700">
                    Contraste para verificar
                  </p>
                </div>
              </div>
            </div>
          ) : (
            <div className="min-h-64 p-4 sm:min-h-72 sm:p-6" aria-live="polite">
              <div className="flex items-start gap-3 rounded-xl bg-blue-50 p-4">
                <span className="grid size-10 shrink-0 place-items-center rounded-lg bg-blue-600 text-white">
                  <ScanSearch aria-hidden="true" className="size-5" />
                </span>
                <div>
                  <h2 className="font-semibold text-slate-900">
                    Hallazgos para revisar
                  </h2>
                  <p className="mt-1 text-sm leading-6 text-slate-600">
                    La IA organiza señales; confirmá cada sugerencia con el
                    contexto de tu material.
                  </p>
                </div>
              </div>
              <ol className="mt-4 space-y-3">
                <li className="flex gap-3 rounded-lg border border-slate-200 p-3.5">
                  <span className="grid size-7 shrink-0 place-items-center rounded-full bg-amber-100 text-sm font-bold text-amber-900">
                    1
                  </span>
                  <p className="text-sm leading-6 text-slate-700">
                    <strong>Imagen sin descripción:</strong> agregá qué idea
                    aporta al tema.
                  </p>
                </li>
                <li className="flex gap-3 rounded-lg border border-slate-200 p-3.5">
                  <span className="grid size-7 shrink-0 place-items-center rounded-full bg-emerald-100 text-sm font-bold text-emerald-900">
                    2
                  </span>
                  <p className="text-sm leading-6 text-slate-700">
                    <strong>Texto extenso:</strong> probá dividirlo con
                    subtítulos informativos.
                  </p>
                </li>
              </ol>
            </div>
          )}
          <div className="flex items-center justify-between rounded-xl bg-slate-900 px-4 py-3 text-white">
            <span className="text-sm font-medium">
              La revisión humana importa
            </span>
            <span className="inline-flex items-center gap-1.5 text-xs text-emerald-300">
              <Sparkles aria-hidden="true" className="size-3.5" />
              Asistencia IA
            </span>
          </div>
        </div>
      </div>
    </section>
  );
}
