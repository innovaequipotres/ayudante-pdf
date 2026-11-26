
import type { ButtonHTMLAttributes } from "react";
import clsx from "clsx";
import { twMerge } from "tailwind-merge";

export type ButtonVariant =
  | "primary"
  | "secondary"
  | "outline"
  | "ghost"
  | "lumi-primary"
  | "lumi-outline"
  | "lumi-ghost"
  | "lumi-blue";

export interface ButtonProps
  extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
}

const variantClasses: Record<ButtonVariant, string> = {
  // Variantes existentes: se conservan.
  primary:
    "bg-primary text-white hover:bg-primary/90 active:bg-primary/80",

  secondary:
    "bg-secondary text-emerald-950 hover:bg-secondary/90 active:bg-secondary/80",

  outline:
    "border border-slate-300 bg-transparent text-slate-900 hover:bg-slate-100",

  ghost:
    "bg-transparent text-slate-700 hover:bg-slate-100",

  // Nuevas variantes del diseño LUMI.
  "lumi-primary":
    "min-h-11 rounded-lg border border-transparent bg-[#6360ED] text-white font-semibold hover:bg-[#2C2066] active:bg-[#2C2066] disabled:border-[#C5D2E7] disabled:bg-white disabled:text-[#B9C0CA] disabled:opacity-100",

  "lumi-outline":
    "min-h-11 rounded-lg border border-[#C5D2E7] bg-white text-[#14203C] font-semibold hover:border-[#2563EB] hover:bg-[#E8EDFC] hover:text-[#2563EB] disabled:text-[#B9C0CA] disabled:opacity-100",

  "lumi-ghost":
    "min-h-11 rounded-lg bg-transparent text-[#14203C] font-semibold hover:text-[#2563EB] disabled:text-[#B9C0CA] disabled:opacity-100",

  "lumi-blue":
    "min-h-11 rounded-lg bg-[#245DE9] text-white font-semibold hover:bg-[#0736AE] active:bg-[#0736AE]",
};

export function Button({
  variant = "primary",
  className,
  type = "button",
  ...props
}: ButtonProps) {
  const classes = twMerge(
    clsx(
      "inline-flex items-center justify-center gap-2 rounded-md px-4 py-2 text-sm font-medium transition-colors focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary disabled:pointer-events-none disabled:opacity-50",
      variantClasses[variant],
      className,
    ),
  );

  return (
    <button {...props} type={type} className={classes} />
  );
}
