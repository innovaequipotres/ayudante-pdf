"use client";

import { useState } from "react";
import Link from "next/link";
import { BookOpenCheck, Menu, Sparkles, X } from "lucide-react";

const sectionLinks = [
  { href: "#como-funciona", label: "Cómo funciona" },
  { href: "#beneficios", label: "Beneficios" },
  { href: "#preguntas", label: "Preguntas" },
  { href: "#contacto", label: "Contacto" },
];

function Brand() {
  return (
    <Link
      href="/"
      aria-label="LUMI, ir al inicio"
      className="inline-flex items-center gap-2.5 rounded-md"
    >
      <span className="relative grid size-10 place-items-center rounded-xl bg-linear-to-br from-blue-600 to-indigo-600 text-white shadow-md shadow-blue-900/15">
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
      <span className="text-xl font-extrabold text-slate-900">LUMI</span>
    </Link>
  );
}

function SectionLinks({
  mobile = false,
  onNavigate,
}: {
  mobile?: boolean;
  onNavigate?: () => void;
}) {
  return (
    <ul
      className={
        mobile
          ? "grid gap-1 border-t border-slate-200 py-3"
          : "hidden items-center gap-7 md:flex"
      }
    >
      {sectionLinks.map((link) => (
        <li key={link.href}>
          <Link
            href={link.href}
            onClick={onNavigate}
            className="block rounded-md px-2 py-2 text-sm font-medium text-slate-600 transition-colors hover:text-blue-700 focus-visible:text-blue-700"
          >
            {link.label}
          </Link>
        </li>
      ))}
      {mobile && (
        <>
          <li>
            <Link
              href="/login"
              onClick={onNavigate}
              className="block rounded-md px-2 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-50"
            >
              Iniciar sesión
            </Link>
          </li>
          <li>
            <Link
              href="/registro"
              onClick={onNavigate}
              className="block rounded-md bg-blue-600 px-4 py-2.5 text-center text-sm font-semibold text-white hover:bg-blue-700"
            >
              Crear cuenta
            </Link>
          </li>
        </>
      )}
    </ul>
  );
}

export default function Navbar() {
  const [isMenuOpen, setIsMenuOpen] = useState(false);

  return (
    <header className="sticky top-0 z-50 border-b border-slate-200/80 bg-white/95 backdrop-blur-md">
      <nav
        aria-label="Navegación principal"
        className="mx-auto flex min-h-17 max-w-7xl items-center justify-between gap-6 px-5 sm:px-8"
      >
        <Brand />
        <SectionLinks />
        <div className="hidden items-center gap-3 md:flex">
          <Link
            href="/login"
            className="rounded-md px-3 py-2 text-sm font-semibold text-slate-700 transition-colors hover:text-blue-700"
          >
            Iniciar sesión
          </Link>
          <Link
            href="/registro"
            className="rounded-lg bg-blue-600 px-4 py-2.5 text-sm font-semibold text-white shadow-sm transition hover:bg-blue-700 focus-visible:outline-offset-4"
          >
            Crear cuenta
          </Link>
        </div>
        <div className="relative md:hidden">
          <button
            type="button"
            aria-label={isMenuOpen ? "Cerrar menú" : "Abrir menú"}
            aria-expanded={isMenuOpen}
            aria-controls="menu-movil"
            onClick={() => setIsMenuOpen((open) => !open)}
            className="grid size-11 place-items-center rounded-lg border border-slate-200 text-slate-700 hover:bg-slate-50"
          >
            {isMenuOpen ? (
              <X aria-hidden="true" className="size-5" />
            ) : (
              <Menu aria-hidden="true" className="size-5" />
            )}
          </button>
          {isMenuOpen && (
            <div
              id="menu-movil"
              className="absolute right-0 top-14 w-64 rounded-xl border border-slate-200 bg-white p-3 shadow-xl shadow-slate-900/10"
            >
              <SectionLinks mobile onNavigate={() => setIsMenuOpen(false)} />
            </div>
          )}
        </div>
      </nav>
    </header>
  );
}
