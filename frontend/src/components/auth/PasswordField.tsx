

"use client";

import { useState } from "react";
import { Eye, EyeOff, Lock } from "lucide-react";

interface PasswordFieldProps {
  autoComplete: "current-password" | "new-password";
  error?: string;
  id: string;
  label?: string;
  onChange: (value: string) => void;
  placeholder: string;
  value: string;
}

export default function PasswordField({
  autoComplete,
  error,
  id,
  label = "Contraseña",
  onChange,
  placeholder,
  value,
}: PasswordFieldProps) {
  const [isVisible, setIsVisible] = useState(false);
  const errorId = `${id}-error`;

  return (
    <div>
      <label
        htmlFor={id}
        className="mb-1.5 block text-sm font-semibold text-[#14203C]"
      >
        {label}
        <span aria-hidden="true" className="ml-1 text-rose-700">
          *
        </span>
      </label>

      <div className="relative">
        <Lock
          aria-hidden="true"
          className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-slate-500"
        />

        <input
          id={id}
          name={id}
          type={isVisible ? "text" : "password"}
          autoComplete={autoComplete}
          value={value}
          required
          minLength={autoComplete === "new-password" ? 8 : undefined}
          placeholder={placeholder}
          aria-invalid={Boolean(error)}
          aria-describedby={error ? errorId : undefined}
          onChange={(event) =>
            onChange(event.currentTarget.value)
          }
          className={`min-h-11 w-full rounded-lg border bg-white py-2.5 pl-10 pr-12 text-sm text-[#14203C] placeholder:text-slate-500 transition-colors focus-visible:border-[#6360ED] focus-visible:outline-[#6360ED] ${
            error ? "border-rose-700" : "border-[#C5D2E7]"
          }`}
        />

        <button
          type="button"
          aria-label={isVisible ? "Ocultar contraseña" : "Mostrar contraseña"}
          aria-pressed={isVisible}
          aria-controls={id}
          onClick={() => setIsVisible((visible) => !visible)}
          className="absolute right-1 top-1/2 grid size-9 -translate-y-1/2 place-items-center rounded-md text-slate-600 transition-colors hover:bg-[#E8EDFC] hover:text-[#6360ED]"
        >
          {isVisible ? (
            <Eye aria-hidden="true" className="size-4" />
          ) : (
            <EyeOff aria-hidden="true" className="size-4" />
          )}
        </button>
      </div>

      {error && (
        <p
          id={errorId}
          role="alert"
          className="mt-1.5 text-sm font-medium text-rose-700"
        >
          {error}
        </p>
      )}
    </div>
  );
}
