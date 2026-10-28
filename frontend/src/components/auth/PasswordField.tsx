"use client";

import { useState } from "react";
import { Eye, EyeOff } from "lucide-react";

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
        className="mb-1.5 block text-sm font-semibold text-slate-800"
      >
        {label}
        <span aria-hidden="true" className="ml-1 text-rose-700">
          *
        </span>
      </label>
      <div className="relative">
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
          onChange={(event) => onChange(event.currentTarget.value)}
          className="min-h-12 w-full rounded-lg border border-slate-300 bg-white px-3.5 py-3 pr-12 text-sm text-slate-900 placeholder:text-slate-500 focus-visible:border-blue-600 focus-visible:outline-blue-600"
        />
        <button
          type="button"
          aria-label={isVisible ? "Ocultar contraseña" : "Mostrar contraseña"}
          aria-pressed={isVisible}
          aria-controls={id}
          onClick={() => setIsVisible((visible) => !visible)}
          className="absolute right-1.5 top-1/2 grid size-9 -translate-y-1/2 place-items-center rounded-md text-slate-600 hover:bg-slate-100 hover:text-blue-700"
        >
          {isVisible ? (
            <EyeOff aria-hidden="true" className="size-4" />
          ) : (
            <Eye aria-hidden="true" className="size-4" />
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
