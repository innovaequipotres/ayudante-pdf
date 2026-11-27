
import type { InputHTMLAttributes, ReactNode } from "react";
import clsx from "clsx";
import { twMerge } from "tailwind-merge";

export interface CheckboxProps
  extends Omit<InputHTMLAttributes<HTMLInputElement>, "type"> {
  label: ReactNode;
  containerClassName?: string;
}

export function Checkbox({
  label,
  className,
  containerClassName,
  disabled,
  ...props
}: CheckboxProps) {
  return (
    <label
      className={twMerge(
        clsx(
          "inline-flex items-start gap-3",
          "text-sm leading-6 text-[#14203C]",
          disabled
            ? "cursor-not-allowed opacity-50"
            : "cursor-pointer",
          containerClassName,
        ),
      )}
    >
      <input
        {...props}
        type="checkbox"
        disabled={disabled}
        className={twMerge(
          clsx(
            "mt-1 size-4 shrink-0",
            "cursor-pointer accent-[#6360ED]",
            "focus-visible:outline-2",
            "focus-visible:outline-offset-2",
            "focus-visible:outline-[#6360ED]",
            "disabled:cursor-not-allowed",
            className,
          ),
        )}
      />

      <span>{label}</span>
    </label>
  );
}
