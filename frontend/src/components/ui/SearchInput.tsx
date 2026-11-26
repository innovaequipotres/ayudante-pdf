
import type { InputHTMLAttributes } from "react";
import { Search } from "lucide-react";
import clsx from "clsx";
import { twMerge } from "tailwind-merge";

export interface SearchInputProps
  extends InputHTMLAttributes<HTMLInputElement> {
  containerClassName?: string;
}

export function SearchInput({
  className,
  containerClassName,
  placeholder = "Buscar",
  "aria-label": ariaLabel = "Buscar",
  ...props
}: SearchInputProps) {
  return (
    <div
      className={twMerge(
        "relative w-full",
        containerClassName,
      )}
    >
      <Search
        aria-hidden="true"
        className="pointer-events-none absolute left-4 top-1/2 size-5 -translate-y-1/2 text-[#14203C]"
      />

      <input
        {...props}
        type="search"
        aria-label={ariaLabel}
        placeholder={placeholder}
        className={twMerge(
          clsx(
            "min-h-11 w-full rounded-lg border border-[#C5D2E7]",
            "bg-white py-2 pl-12 pr-4 text-sm text-[#14203C]",
            "placeholder:text-[#14203C]",
            "transition-colors hover:border-[#2563EB]",
            "focus-visible:border-[#2563EB]",
            "focus-visible:outline-[#2563EB]",
            "disabled:cursor-not-allowed disabled:opacity-50",
            className,
          ),
        )}
      />
    </div>
  );
}
