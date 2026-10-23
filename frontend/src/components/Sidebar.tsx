
"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  House,
  FolderOpen,
  History,
  Settings,
  Accessibility,
} from "lucide-react";

const navigation = [
  { label: "Inicio", href: "/inicio", icon: House },
  { label: "Mis archivos", href: "/archivos", icon: FolderOpen },
  { label: "Historial", href: "/historial", icon: History },
  { label: "Configuración", href: "/configuracion", icon: Settings },
];

export default function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="fixed inset-y-0 left-0 z-40 flex h-screen w-64 shrink-0 flex-col overflow-y-auto border-r border-slate-200 bg-white px-4 py-6">
      <Link href="/inicio" className="mb-10 flex items-center gap-3 px-2">
        <span className="flex h-10 w-10 items-center justify-center rounded-xl bg-violet-100 text-violet-700">
          <Accessibility size={25} aria-hidden="true" />
        </span>
        <span className="text-xl font-bold tracking-tight text-slate-900">
          Inclus<span className="text-violet-600">IA</span>
        </span>
      </Link>

      <p className="mb-3 px-3 text-xs font-semibold uppercase tracking-wider text-slate-400">
        Menú principal
      </p>

      <nav aria-label="Navegación principal" className="flex flex-col gap-2">
        {navigation.map(({ label, href, icon: Icon }) => {
          const active = pathname === href;

          return (
            <Link
              key={href}
              href={href}
              aria-current={active ? "page" : undefined}
              className={`flex items-center gap-3 rounded-xl px-3 py-3 text-sm font-medium transition-colors ${
                active
                  ? "bg-violet-100 text-violet-800"
                  : "text-slate-600 hover:bg-slate-100 hover:text-slate-900"
              }`}
            >
              <Icon size={20} aria-hidden="true" />
              <span>{label}</span>
            </Link>
          );
        })}
      </nav>

      <div className="mt-auto rounded-xl bg-slate-50 p-3 text-xs leading-5 text-slate-500">
        <p className="font-semibold text-slate-700">InclusIA</p>
        <p>Accesibilidad educativa con inteligencia artificial.</p>
      </div>
    </aside>
  );
}
