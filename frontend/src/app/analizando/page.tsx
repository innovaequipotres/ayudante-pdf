"use client";

import Link from "next/link";
import { ArrowLeft, FileText } from "lucide-react";
import { useLumiStore } from "@/store/useLumiStore";

export default function AnalizandoPage() {
  const pendingUpload = useLumiStore((state) => state.pendingUpload);

  return (
    <main className="min-h-svh bg-[#c6cfe1] px-4 py-8 sm:px-6">
      <div className="mx-auto flex min-h-[calc(100svh-4rem)] max-w-5xl flex-col bg-[#f7fafc] shadow-sm">
        <header className="flex min-h-16 items-center border-b border-slate-200 bg-white px-5 sm:px-8">
          <Link href="/inicio" className="text-sm font-bold text-slate-900">
            LUMI
          </Link>
        </header>

        <section className="flex flex-1 items-center justify-center px-5 py-12">
          <div className="w-full max-w-xl text-center">
            <span className="mx-auto grid size-14 place-items-center rounded-full bg-indigo-50 text-indigo-700">
              <FileText aria-hidden="true" className="size-7" />
            </span>
            {pendingUpload ? (
              <>
                <h1 className="mt-5 text-2xl font-bold text-slate-900">
                  Archivo recibido
                </h1>
                <p className="mt-3 wrap-break-word text-base font-semibold text-slate-700">
                  {pendingUpload.name}
                </p>
                <p className="mt-3 text-sm leading-6 text-slate-600">
                  El procesamiento del análisis todavía no está conectado. Tu
                  archivo quedó listo en esta sesión.
                </p>
              </>
            ) : (
              <>
                <h1 className="mt-5 text-2xl font-bold text-slate-900">
                  No hay un archivo seleccionado
                </h1>
                <p className="mt-3 text-sm leading-6 text-slate-600">
                  Volvé a Inicio para cargar un archivo PDF.
                </p>
              </>
            )}
            <Link
              href="/inicio"
              className="mt-7 inline-flex min-h-11 items-center gap-2 rounded-md bg-slate-800 px-5 py-2.5 text-sm font-semibold text-white transition hover:bg-slate-700 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-blue-700"
            >
              <ArrowLeft aria-hidden="true" className="size-4" />
              Volver a Inicio
            </Link>
          </div>
        </section>
      </div>
    </main>
  );
}
