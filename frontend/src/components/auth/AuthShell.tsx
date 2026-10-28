import type { ReactNode } from "react";
import Link from "next/link";
import { BookOpenCheck, Sparkles } from "lucide-react";

interface AuthShellProps {
  children: ReactNode;
  message: string;
}

export default function AuthShell({ children, message }: AuthShellProps) {
  return (
    <div className="min-h-svh bg-white lg:grid lg:grid-cols-[1.05fr_0.95fr]">
      <aside className="relative isolate flex min-h-[24rem] flex-col overflow-hidden bg-linear-to-br from-blue-700 via-indigo-800 to-slate-900 px-6 py-8 text-white sm:px-10 lg:min-h-svh lg:px-14 lg:py-12">
        <div
          aria-hidden="true"
          className="absolute inset-x-0 bottom-0 -z-10 h-48 bg-linear-to-t from-slate-950/30 to-transparent"
        />
        <div
          aria-hidden="true"
          className="absolute right-8 top-8 -z-10 h-40 w-40 rotate-12 rounded-[2rem] border border-white/10 sm:right-16 sm:top-16 sm:h-56 sm:w-56"
        />
        <div
          aria-hidden="true"
          className="absolute bottom-8 right-16 -z-10 h-32 w-32 -rotate-12 rounded-[2rem] border border-emerald-300/15 sm:bottom-16 sm:right-28 sm:h-44 sm:w-44"
        />

        <Link
          href="/"
          aria-label="LUMI, volver al inicio"
          className="inline-flex w-fit items-center gap-3 rounded-md"
        >
          <span className="relative grid size-11 place-items-center rounded-xl bg-white text-blue-700 shadow-lg shadow-slate-950/20">
            <BookOpenCheck
              aria-hidden="true"
              className="size-6"
              strokeWidth={2.2}
            />
            <Sparkles
              aria-hidden="true"
              className="absolute -right-1 -top-1 size-4 fill-emerald-300 text-emerald-300"
            />
          </span>
          <span className="text-2xl font-extrabold text-white">LUMI</span>
        </Link>

        <div className="my-auto max-w-xl py-12 lg:py-20">
          <p className="mb-5 inline-flex items-center gap-2 rounded-full border border-white/20 bg-white/10 px-3.5 py-2 text-sm font-semibold text-blue-100">
            <Sparkles aria-hidden="true" className="size-4 text-emerald-300" />
            Tecnología para aprender sin barreras
          </p>
          <p className="text-4xl font-bold leading-tight text-white sm:text-5xl">
            Aprender también es incluir.
          </p>
          <p className="mt-6 max-w-lg text-lg leading-8 text-blue-100">
            {message}
          </p>
          <div className="mt-9 flex items-start gap-3 rounded-xl border border-white/20 bg-white/10 p-4 backdrop-blur-sm sm:p-5">
            <span className="grid size-10 shrink-0 place-items-center rounded-lg bg-emerald-400/15 text-emerald-200">
              <Sparkles aria-hidden="true" className="size-5" />
            </span>
            <p className="text-sm leading-6 text-blue-50">
              La inteligencia artificial acompaña tu criterio docente; vos
              elegís qué cambios aplicar.
            </p>
          </div>
        </div>

        <p className="text-xs text-blue-200">
          © 2026 LUMI · Accesibilidad educativa
        </p>
      </aside>

      <main className="flex items-center justify-center px-5 py-12 sm:px-10 lg:px-12 lg:py-16">
        <div className="w-full max-w-md">{children}</div>
      </main>
    </div>
  );
}
