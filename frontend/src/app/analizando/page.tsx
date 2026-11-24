"use client";

import { Suspense, useCallback, useEffect, useRef, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import {
  Check,
  Circle,
  FileText,
  LoaderCircle,
  Sparkles,
  AlertCircle,
} from "lucide-react";
import { useLumiStore } from "@/store/useLumiStore";

const ANALYSIS_STEPS = [
  { label: "Extrayendo contenido del PDF...", weight: 25 },
  { label: "Analizando estructura y formato...", weight: 25 },
  { label: "Detectando barreras de accesibilidad...", weight: 25 },
  { label: "Generando recomendaciones...", weight: 25 },
] as const;

type StepStatus = "pending" | "active" | "complete" | "error";

interface StepState {
  status: StepStatus;
  label: string;
}

function AnalizandoContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const sessionId = searchParams.get("sessionId");
  const pendingUpload = useLumiStore((state) => state.pendingUpload);
  const error = useLumiStore((state) => state.error);
  const currentSessionId = useLumiStore((state) => state.currentSessionId);
  const pollAnalysis = useLumiStore((state) => state.pollAnalysis);
  const clearError = useLumiStore((state) => state.clearError);
  const resetAnalysisState = useLumiStore((state) => state.resetAnalysisState);

  const [steps, setSteps] = useState<StepState[]>(
    ANALYSIS_STEPS.map((s) => ({
      status: "pending" as StepStatus,
      label: s.label,
    })),
  );
  const [overallProgress, setOverallProgress] = useState(0);
  const hasStartedRef = useRef(false);

  const runAnalysis = useCallback(
    async (sid: string) => {
      setSteps(
        ANALYSIS_STEPS.map((s, i) => ({
          status: i === 0 ? "active" : "pending",
          label: s.label,
        })),
      );
      setOverallProgress(0);

      try {
        await pollAnalysis(sid);

        if (useLumiStore.getState().error) return;

        setSteps(
          ANALYSIS_STEPS.map((s) => ({
            status: "complete" as StepStatus,
            label: s.label,
          })),
        );
        setOverallProgress(100);

        await new Promise((resolve) => setTimeout(resolve, 800));

        const activeDoc = useLumiStore.getState().activeDocument;
        if (activeDoc) {
          router.push(`/diagnostico/${activeDoc.id}`);
        }
      } catch {
        setSteps((prev) => {
          const failedIndex = prev.findIndex((s) => s.status === "active");
          if (failedIndex < 0) return prev;
          return prev.map((s, i) =>
            i === failedIndex ? { ...s, status: "error" as StepStatus } : s,
          );
        });
      }
    },
    [pollAnalysis, router],
  );

  useEffect(() => {
    if (!sessionId && !currentSessionId) {
      router.push("/inicio");
      return;
    }

    const targetSessionId = sessionId ?? currentSessionId;
    if (!targetSessionId || hasStartedRef.current) return;

    hasStartedRef.current = true;
    void runAnalysis(targetSessionId);
  }, [sessionId, currentSessionId, router, runAnalysis]);

  const activeStep = steps.findIndex((s) => s.status === "active");

  return (
    <main className="flex min-h-svh flex-col bg-[#f7fafc] px-4 py-6 text-slate-900 sm:px-8 sm:py-8">
      <header className="mx-auto w-full max-w-7xl">
        <ol
          aria-label="Etapas del proceso"
          className="mx-auto flex max-w-sm items-center justify-between gap-3 text-xs font-medium sm:text-sm"
        >
          <li
            aria-current={activeStep === 0 ? "step" : undefined}
            className={`flex items-center gap-2 ${activeStep <= 0 ? "text-blue-700" : "text-slate-500"}`}
          >
            <span
              className={`grid size-7 place-items-center rounded-full font-semibold ${
                activeStep < 0
                  ? "bg-blue-600 text-white"
                  : "border border-slate-300 bg-white"
              }`}
            >
              1
            </span>
            Analizar
          </li>
          <li
            aria-current={activeStep === 1 ? "step" : undefined}
            className={`flex items-center gap-2 ${activeStep <= 1 && activeStep >= 0 ? "text-blue-700" : "text-slate-500"}`}
          >
            <span
              className={`grid size-7 place-items-center rounded-full font-semibold ${
                activeStep < 1
                  ? "border border-slate-300 bg-white"
                  : activeStep === 1
                    ? "bg-blue-600 text-white"
                    : "bg-emerald-600 text-white"
              }`}
            >
              2
            </span>
            Revisar
          </li>
          <li
            aria-current={activeStep >= 2 ? "step" : undefined}
            className={`flex items-center gap-2 ${activeStep >= 2 ? "text-blue-700" : "text-slate-500"}`}
          >
            <span
              className={`grid size-7 place-items-center rounded-full font-semibold ${
                activeStep < 2
                  ? "border border-slate-300 bg-white"
                  : "bg-emerald-600 text-white"
              }`}
            >
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

        <h1 className="page-title mt-7">
          {error ? "Error en el análisis" : "Analizando tu material..."}
        </h1>
        <p className="mt-3 max-w-full wrap-break-word text-sm text-slate-500">
          {pendingUpload?.name ?? "Documento PDF"}
        </p>

        <div className="mt-12 w-full max-w-2xl">
          <div className="flex items-center gap-4 sm:gap-6">
            <div
              aria-label="Progreso del análisis"
              aria-valuemin={0}
              aria-valuemax={100}
              aria-valuenow={overallProgress}
              className="h-2.5 flex-1 overflow-hidden rounded-full bg-slate-300"
              role="progressbar"
            >
              <div
                className="h-full rounded-full bg-slate-800 transition-[width] duration-300 motion-reduce:transition-none"
                style={{ width: `${overallProgress}%` }}
              />
            </div>
            <span className="w-12 text-right text-sm font-semibold tabular-nums text-slate-800">
              {overallProgress}%
            </span>
          </div>

          <ol
            aria-label="Tareas del análisis"
            className="mx-auto mt-8 max-w-lg space-y-4 text-left"
          >
            {steps.map((step) => {
              const isComplete = step.status === "complete";
              const isActive = step.status === "active";
              const isError = step.status === "error";

              return (
                <li
                  key={step.label}
                  aria-current={isActive ? "step" : undefined}
                  className={`flex min-h-5 items-center gap-3 text-sm ${
                    isComplete
                      ? "text-slate-700"
                      : isActive
                        ? "font-medium text-slate-900"
                        : isError
                          ? "text-red-700"
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
                  ) : isError ? (
                    <span className="grid size-4 shrink-0 place-items-center rounded-full bg-red-100 text-red-700">
                      <AlertCircle
                        aria-hidden="true"
                        className="size-3"
                        strokeWidth={2.5}
                      />
                    </span>
                  ) : (
                    <Circle
                      aria-hidden="true"
                      className="size-4 shrink-0 text-slate-400"
                    />
                  )}
                  <span>{step.label}</span>
                </li>
              );
            })}
          </ol>
        </div>
      </section>

      {error && (
        <div className="mx-auto mt-6 max-w-xl rounded-lg border border-red-200 bg-red-50 p-4 text-center text-red-800">
          <p className="font-medium">No se pudo completar el análisis</p>
          <p className="mt-1 text-sm">{error}</p>
          <button
            type="button"
            onClick={() => {
              clearError();
              resetAnalysisState();
              router.push("/inicio");
            }}
            className="mt-3 inline-flex items-center gap-2 rounded-md bg-red-700 px-4 py-2 text-sm font-semibold text-white hover:bg-red-800"
          >
            Volver al inicio
          </button>
        </div>
      )}

      <p className="mx-auto mt-4 max-w-xl text-center text-xs leading-5 text-slate-600 sm:text-sm">
        Por favor, no cierres esta ventana mientras procesamos tu documento.
      </p>
    </main>
  );
}

export default function AnalizandoPage() {
  return (
    <Suspense
      fallback={
        <div className="grid min-h-svh place-items-center bg-[#f7fafc] text-sm text-slate-500">
          Preparando el análisis...
        </div>
      }
    >
      <AnalizandoContent />
    </Suspense>
  );
}
