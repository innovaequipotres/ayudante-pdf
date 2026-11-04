import type { HTMLAttributes, ReactNode } from "react";
import clsx from "clsx";
import { twMerge } from "tailwind-merge";

export type BadgeVariant =
  | "Alta"
  | "Media"
  | "Baja"
  | "Aplicada"
  | "En edición"
  | "Analizado"
  | "Guardado"
  | "Sin guardar"
  | "Finalizado"
  | "Revisado"
  | "Procesando";

export interface BadgeProps extends HTMLAttributes<HTMLSpanElement> {
  variant: BadgeVariant;
  children?: ReactNode;
}

const variantClasses: Record<BadgeVariant, string> = {
  Alta: "border-severity-high/25 bg-severity-high/10 text-red-800",
  Media: "border-severity-medium/25 bg-severity-medium/10 text-amber-900",
  Baja: "border-severity-low/25 bg-severity-low/10 text-blue-800",
  Aplicada: "border-emerald-200 bg-emerald-50 text-emerald-800",
  "En edición": "border-blue-200 bg-blue-50 text-blue-800",
  Analizado: "border-cyan-200 bg-cyan-50 text-cyan-800",
  Guardado: "border-emerald-200 bg-emerald-50 text-emerald-800",
  "Sin guardar": "border-amber-200 bg-amber-50 text-amber-800",
  Finalizado: "border-slate-200 bg-slate-100 text-slate-800",
  Revisado: "border-teal-200 bg-teal-50 text-teal-800",
  Procesando: "border-sky-200 bg-sky-50 text-sky-800",
};

export function Badge({ variant, className, children, ...props }: BadgeProps) {
  const classes = twMerge(
    clsx(
      "inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-medium",
      variantClasses[variant],
      className,
    ),
  );

  return (
    <span {...props} className={classes}>
      {children ?? variant}
    </span>
  );
}
