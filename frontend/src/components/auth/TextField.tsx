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

  return (
    <div>
      <label
        htmlFor={id}
        className="mb-1.5 block text-sm font-semibold text-slate-800"
      >
        {label}
        {required && (
          <span aria-hidden="true" className="ml-1 text-rose-700">
            *
          </span>
        )}
      </label>
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
        onChange={(event) => onChange(event.currentTarget.value)}
        className="min-h-12 w-full rounded-lg border border-slate-300 bg-white px-3.5 py-3 text-sm text-slate-900 placeholder:text-slate-500 focus-visible:border-blue-600 focus-visible:outline-blue-600"
      />
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
