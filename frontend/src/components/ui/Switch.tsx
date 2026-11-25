
"use client";

import type { ButtonHTMLAttributes } from "react";
import clsx from "clsx";
import { twMerge } from "tailwind-merge";

export interface SwitchProps
  extends Omit<
    ButtonHTMLAttributes<HTMLButtonElement>,
    "onChange" | "role" | "aria-checked"
  > {
  checked: boolean;
  onCheckedChange: (checked: boolean) => void;
  label: string;
}

export function Switch({
  checked,
  onCheckedChange,
  label,
  disabled = false,
  className,
  onClick,
  ...props
}: SwitchProps) {
  return (
    <button
      {...props}
      type="button"
      role="switch"
      aria-checked={checked}
      aria-label={label}
      disabled={disabled}
      onClick={(event) => {
        onClick?.(event);

        if (!event.defaultPrevented) {
          onCheckedChange(!checked);
        }
      }}
      className={twMerge(
        clsx(
          "relative inline-flex h-7 w-12 shrink-0 items-center rounded-full",
          "transition-colors motion-reduce:transition-none",
          "focus-visible:outline-2 focus-visible:outline-offset-2",
          "focus-visible:outline-[#6360ED]",
          "disabled:cursor-not-allowed disabled:opacity-50",
          checked ? "bg-[#6360ED]" : "bg-slate-500",
          className,
        ),
      )}
    >
      <span
        aria-hidden="true"
        className={clsx(
          "pointer-events-none size-5 rounded-full bg-white shadow-sm",
          "transition-transform motion-reduce:transition-none",
          checked ? "translate-x-6" : "translate-x-1",
        )}
      />
    </button>
  );
}
