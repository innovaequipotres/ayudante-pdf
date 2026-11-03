import type { Metadata } from "next";
import Link from "next/link";
import { BookOpenCheck, FileText, Sparkles } from "lucide-react";

export const metadata: Metadata = {
  title: "Inicio | LUMI",
  description: "Espacio de bienvenida de la demostración local de LUMI.",
};

export default function HomePage() {
  return (
    <main className="min-h-svh bg-slate-50 px-5 py-8 sm:px-8">
      <div className="mx-auto flex max-w-6xl items-center justify-between border-b border-slate-200 pb-5">
        <Link
          href="/"
          aria-label="LUMI, ir al inicio"
          className="inline-flex items-center gap-2.5 rounded-md"
        >
          <span className="grid size-10 place-items-center rounded-xl bg-linear-to-br from-blue-600 to-indigo-600 text-white">
            <BookOpenCheck aria-hidden="true" className="size-5" />
          </span>
          <span className="text-xl font-extrabold text-slate-900">LUMI</span>
        </Link>
        <Link
          href="/login"
          className="rounded-lg border border-slate-300 bg-white px-4 py-2.5 text-sm font-semibold text-slate-700 transition hover:bg-slate-50 focus-visible:outline-blue-600"
        >
          Salir de la demostración
        </Link>
      </div>

      <section className="mx-auto max-w-6xl py-14 sm:py-20">
        <p className="inline-flex items-center gap-2 rounded-full bg-emerald-50 px-3 py-1.5 text-sm font-semibold text-emerald-800">
          <Sparkles aria-hidden="true" className="size-4" />
          Modo demostración
        </p>
        <h1 className="mt-5 text-3xl font-bold text-slate-900 sm:text-4xl">
          ¡Bienvenida/o a LUMI!
        </h1>
        <p className="mt-3 max-w-2xl text-base leading-7 text-slate-600">
          El acceso se simuló correctamente. Esta pantalla no creó una sesión ni
          guardó tus datos; la experiencia de trabajo estará disponible
          próximamente.
        </p>
        <div className="mt-10 grid gap-5 md:grid-cols-2">
          <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
            <span className="grid size-11 place-items-center rounded-lg bg-blue-100 text-blue-700">
              <FileText aria-hidden="true" className="size-5" />
            </span>
            <h2 className="mt-4 text-lg font-bold text-slate-900">
              Tus documentos, en un solo lugar
            </h2>
            <p className="mt-2 text-sm leading-6 text-slate-600">
              Próximamente vas a poder organizar y revisar tus materiales
              educativos.
            </p>
          </div>
          <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
            <span className="grid size-11 place-items-center rounded-lg bg-indigo-100 text-indigo-700">
              <Sparkles aria-hidden="true" className="size-5" />
            </span>
            <h2 className="mt-4 text-lg font-bold text-slate-900">
              Accesibilidad con acompañamiento
            </h2>
            <p className="mt-2 text-sm leading-6 text-slate-600">
              LUMI busca acercarte sugerencias para que puedas tomar decisiones
              con criterio docente.
            </p>
          </div>
        </div>
      </section>
    </main>
  );
}
