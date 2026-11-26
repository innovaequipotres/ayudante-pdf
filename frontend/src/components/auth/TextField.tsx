
import { Mail } from "lucide-react";

interface TextFieldProps {
  autoComplete: string;
  error?: string;
  id: string;
  label: string;
  maxLength?: number;
  onChange: (value: string) => void;
  placeholder: string;
  required?: boolean;
  type?: "email" | "tel" | "text";
  value: string;
}

export default function TextField({
  autoComplete,
  error,
  id,
  label,
  maxLength,
  onChange,
  placeholder,
  required = true,
  type = "text",
  value,
}: TextFieldProps) {
  const errorId = `${id}-error`;
  const isEmail = type === "email";

  return (
    <div>
      <label
        htmlFor={id}
        className="mb-1.5 block text-sm font-semibold text-[#14203C]"
      >
        {label}
        {required && (
          <span aria-hidden="true" className="ml-1 text-rose-700">
            *
          </span>
        )}
      </label>

      <div className="relative">
        {isEmail && (
          <Mail
            aria-hidden="true"
            className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-slate-500"
          />
        )}

        <input
          id={id}
          name={id}
          type={type}
          autoComplete={autoComplete}
          value={value}
          required={required}
          maxLength={maxLength}
          placeholder={placeholder}
          aria-invalid={Boolean(error)}
          aria-describedby={error ? errorId : undefined}
          onChange={(event) =>
            onChange(event.currentTarget.value)
          }
          className={`min-h-11 w-full rounded-lg border bg-white py-2.5 pr-3.5 text-sm text-[#14203C] placeholder:text-slate-500 transition-colors focus-visible:border-[#6360ED] focus-visible:outline-[#6360ED] ${
            isEmail ? "pl-10" : "pl-3.5"
          } ${
            error ? "border-rose-700" : "border-[#C5D2E7]"
          }`}
        />
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
