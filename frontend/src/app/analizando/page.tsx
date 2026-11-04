"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Check, Circle, FileText, LoaderCircle, Sparkles } from "lucide-react";
import { useLumiStore } from "@/store/useLumiStore";

const ANALYSIS_STEPS = [
  "Extrayendo contenido del PDF...",
  "Analizando estructura y formato...",
  "Detectando barreras de accesibilidad...",
  "Generando recomendaciones...",
];

export default function AnalizandoPage() {
  const pendingUpload = useLumiStore((state) => state.pendingUpload);
  const router = useRouter();
  const [progress, setProgress] = useState(0);

  useEffect(() => {
    const intervalId = window.setInterval(() => {
      setProgress((currentProgress) => Math.min(currentProgress + 1, 100));
    }, 100);

    return () => window.clearInterval(intervalId);
  }, []);

  useEffect(() => {
    if (progress === 100) {
      router.push("/diagnostico/documento-trabajo-practico");
    }
  }, [progress, router]);

  const activeStep = Math.min(
    Math.floor(progress / 25),
    ANALYSIS_STEPS.length - 1,
  );

  return (
    <main className="flex min-h-svh flex-col bg-[#f7fafc] px-4 py-6 text-slate-900 sm:px-8 sm:py-8">
      <header className="mx-auto w-full max-w-7xl">
        <ol
          aria-label="Etapas del proceso"
          className="mx-auto flex max-w-sm items-center justify-between gap-3 text-xs font-medium sm:text-sm"
        >
          <li
            aria-current="step"
            className="flex items-center gap-2 text-blue-700"
          >
            <span className="grid size-7 place-items-center rounded-full bg-blue-600 font-semibold text-white">
              1
            </span>
            Analizar
          </li>
          <li className="flex items-center gap-2 text-slate-500">
            <span className="grid size-7 place-items-center rounded-full border border-slate-300 bg-white font-semibold">
              2
            </span>
            Revisar
          </li>
          <li className="flex items-center gap-2 text-slate-500">
            <span className="grid size-7 place-items-center rounded-full border border-slate-300 bg-white font-semibold">
              3
            </span>
            Finalizar
          </li>
        </ol>
      </header>

      <section className="mx-auto flex w-full max-w-7xl flex-1 flex-col items-center justify-center py-12 text-center">
        <div className="relative grid size-32 place-items-center rounded-full bg-slate-200 text-slate-800 sm:size-36">
          <FileText
            aria-hidden="true"
            className="size-16 motion-safe:animate-pulse"
            strokeWidth={1.6}
          />
          <Sparkles
            aria-hidden="true"
            className="absolute right-5 top-5 size-5 text-blue-700 motion-safe:animate-pulse"
          />
          <Sparkles
            aria-hidden="true"
            className="absolute bottom-7 left-5 size-4 text-slate-500 motion-safe:animate-pulse"
          />
        </div>

        <h1 className="page-title mt-7">Analizando tu material...</h1>
        <p className="mt-3 max-w-full wrap-break-word text-sm text-slate-500">
          {pendingUpload?.name ?? "Documento PDF"}
        </p>

        <div className="mt-12 w-full max-w-2xl">
          <div className="flex items-center gap-4 sm:gap-6">
            <div
              aria-label="Progreso del análisis"
              aria-valuemin={0}
              aria-valuemax={100}
              aria-valuenow={progress}
              className="h-2.5 flex-1 overflow-hidden rounded-full bg-slate-300"
              role="progressbar"
            >
              <div
                className="h-full rounded-full bg-slate-800 transition-[width] duration-100 motion-reduce:transition-none"
                style={{ width: `${progress}%` }}
              />
            </div>
            <span className="w-12 text-right text-sm font-semibold tabular-nums text-slate-800">
              {progress}%
            </span>
          </div>

          <ol
            aria-label="Tareas del análisis"
            className="mx-auto mt-8 max-w-lg space-y-4 text-left"
          >
            {ANALYSIS_STEPS.map((step, index) => {
              const isComplete = progress >= (index + 1) * 25;
              const isActive = !isComplete && activeStep === index;

              return (
                <li
                  key={step}
                  aria-current={isActive ? "step" : undefined}
                  className={`flex min-h-5 items-center gap-3 text-sm ${
                    isComplete
                      ? "text-slate-700"
                      : isActive
                        ? "font-medium text-slate-900"
                        : "text-slate-500"
                  }`}
                >
                  {isComplete ? (
                    <span className="grid size-4 shrink-0 place-items-center rounded-full bg-emerald-600 text-white">
                      <Check
                        aria-hidden="true"
                        className="size-3"
                        strokeWidth={3}
                      />
                    </span>
                  ) : isActive ? (
                    <LoaderCircle
                      aria-hidden="true"
                      className="size-4 shrink-0 animate-spin text-blue-700 motion-reduce:animate-none"
                    />
                  ) : (
                    <Circle
                      aria-hidden="true"
                      className="size-4 shrink-0 text-slate-400"
                    />
                  )}
                  <span>{step}</span>
                </li>
              );
            })}
          </ol>
        </div>
      </section>

      <p className="mx-auto mt-4 max-w-xl text-center text-xs leading-5 text-slate-600 sm:text-sm">
        Por favor, no cierres esta ventana mientras procesamos tu documento.
      </p>
    </main>
  );
}
