"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  House,
  FolderOpen,
  History,
  Settings,
  Accessibility,
  CircleHelp,
} from "lucide-react";

const navigation = [
  { label: "Inicio", href: "/inicio", icon: House },
  { label: "Mis archivos", href: "/archivos", icon: FolderOpen },
  { label: "Historial", href: "/historial", icon: History },
];

export default function Sidebar() {
  const pathname = usePathname();

  return (
    <header className="sticky top-0 z-40 w-full border-b border-slate-200 bg-white">
      <div className="mx-auto flex min-h-20 w-full max-w-7xl flex-wrap items-center justify-between gap-4 px-4 py-3 md:px-8">
        {/* Logo */}
        <Link
          href="/inicio"
          className="flex items-center gap-3"
          aria-label="LUMI - Ir al inicio"
        >
          <span className="flex h-10 w-10 items-center justify-center rounded-xl bg-violet-100 text-violet-700">
            <Accessibility size={25} aria-hidden="true" />
          </span>

          <span className="text-xl font-bold tracking-tight text-slate-900">
            LUM<span className="text-violet-600">I</span>
          </span>
        </Link>

        {/* Navegación principal */}
        <nav
          aria-label="Navegación principal"
          className="order-3 flex w-full items-center gap-1 overflow-x-auto md:order-2 md:w-auto"
        >
          {navigation.map(({ label, href, icon: Icon }) => {
            const active = pathname === href;

            return (
              <Link
                key={href}
                href={href}
                aria-current={active ? "page" : undefined}
                className={`flex shrink-0 items-center gap-2 rounded-lg px-3 py-2 text-sm font-medium transition-colors ${
                  active
                    ? "bg-violet-100 text-violet-800"
                    : "text-slate-600 hover:bg-slate-100 hover:text-slate-900"
                }`}
              >
                <Icon size={18} aria-hidden="true" />
                <span>{label}</span>
              </Link>
            );
          })}
        </nav>

        {/* Acciones */}
        <div className="order-2 flex items-center gap-2 md:order-3">
          <Link
            href="/ayuda"
            className="flex items-center gap-2 rounded-lg px-3 py-2 text-sm font-medium text-slate-600 hover:bg-slate-100"
          >
            <CircleHelp size={18} aria-hidden="true" />
            <span className="hidden sm:inline">Ayuda</span>
          </Link>

          <Link
            href="/configuracion"
            aria-label="Configuración"
            aria-current={
              pathname === "/configuracion" ? "page" : undefined
            }
            className={`rounded-lg p-2 transition-colors ${
              pathname === "/configuracion"
                ? "bg-violet-100 text-violet-800"
                : "text-slate-600 hover:bg-slate-100"
            }`}
          >
            <Settings size={20} aria-hidden="true" />
          </Link>
        </div>
      </div>
    </header>
  );
}