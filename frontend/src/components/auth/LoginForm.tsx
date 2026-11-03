"use client";

import { useState, type FormEvent } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import GoogleAuthButton from "@/components/auth/GoogleAuthButton";
import PasswordField from "@/components/auth/PasswordField";
import TextField from "@/components/auth/TextField";
import { isValidEmail } from "@/components/auth/auth-validation";

interface LoginValues {
  email: string;
  password: string;
}

type LoginErrors = Partial<Record<keyof LoginValues, string>>;

export default function LoginForm() {
  const router = useRouter();
  const [values, setValues] = useState<LoginValues>({
    email: "",
    password: "",
  });
  const [errors, setErrors] = useState<LoginErrors>({});
  const [notice, setNotice] = useState("");

  function updateValue(field: keyof LoginValues, value: string) {
    setValues((current) => ({ ...current, [field]: value }));
    setErrors((current) => ({ ...current, [field]: undefined }));
    setNotice("");
  }

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const nextErrors: LoginErrors = {};

    if (!values.email.trim())
      nextErrors.email = "Ingresá tu correo electrónico.";
    else if (!isValidEmail(values.email))
      nextErrors.email = "Ingresá un correo electrónico válido.";
    if (!values.password) nextErrors.password = "Ingresá tu contraseña.";

    setErrors(nextErrors);
    if (Object.keys(nextErrors).length > 0) {
      const firstInvalidField = nextErrors.email ? "email" : "password";
      const firstInvalidControl =
        event.currentTarget.elements.namedItem(firstInvalidField);
      if (firstInvalidControl instanceof HTMLElement)
        firstInvalidControl.focus();
      return;
    }

    router.push("/inicio");
  }

  return (
    <div>
      <p className="text-sm font-bold uppercase text-blue-700">
        Tu espacio de trabajo
      </p>
      <h1
        id="auth-heading"
        className="mt-2 text-3xl font-bold text-slate-900 sm:text-4xl"
      >
        Iniciar sesión
      </h1>
      <p className="mt-2 text-sm leading-6 text-slate-600">
        Ingresá a tu cuenta para continuar con tus materiales.
      </p>

      <form
        noValidate
        onSubmit={handleSubmit}
        aria-labelledby="auth-heading"
        className="mt-8 space-y-5"
      >
        <TextField
          id="email"
          label="Correo electrónico"
          type="email"
          placeholder="Ingresa tu correo electrónico"
          autoComplete="email"
          value={values.email}
          error={errors.email}
          onChange={(value) => updateValue("email", value)}
        />
        <div>
          <PasswordField
            id="password"
            autoComplete="current-password"
            placeholder="Ingresa tu contraseña"
            value={values.password}
            error={errors.password}
            onChange={(value) => updateValue("password", value)}
          />
          <div className="mt-2 text-right">
            <button
              type="button"
              onClick={() =>
                setNotice(
                  "La recuperación de contraseña estará disponible cuando se conecte el servicio de correo.",
                )
              }
              className="rounded-sm text-sm font-semibold text-blue-700 underline-offset-4 hover:underline"
            >
              ¿Olvidaste tu contraseña?
            </button>
          </div>
        </div>

        <p
          role="status"
          aria-live="polite"
          className="min-h-5 text-sm text-slate-600"
        >
          {notice}
        </p>
        <div className="grid gap-3 sm:grid-cols-2">
          <button
            type="submit"
            className="min-h-12 rounded-lg bg-blue-600 px-4 py-3 text-sm font-semibold text-white shadow-sm transition hover:bg-blue-700 focus-visible:outline-blue-600"
          >
            Iniciar sesión
          </button>
          <Link
            href="/registro"
            className="inline-flex min-h-12 items-center justify-center rounded-lg border border-slate-300 px-4 py-3 text-sm font-semibold text-slate-700 transition hover:border-blue-300 hover:bg-blue-50 focus-visible:outline-blue-600"
          >
            Crear cuenta
          </Link>
        </div>
      </form>

      <div className="my-6 flex items-center gap-4" aria-hidden="true">
        <span className="h-px flex-1 bg-slate-200" />
        <span className="text-xs font-medium text-slate-500">o también</span>
        <span className="h-px flex-1 bg-slate-200" />
      </div>
      <GoogleAuthButton label="Continuar con Google" />

      <p className="mt-8 text-center text-sm text-slate-600">
        ¿Necesitas ayuda con Lumi?{" "}
        <button
          type="button"
          onClick={() =>
            setNotice(
              "Para recibir ayuda, contactá al equipo de LUMI cuando el canal de soporte esté disponible.",
            )
          }
          className="rounded-sm font-semibold text-blue-700 underline-offset-4 hover:underline"
        >
          Clickea aquí
        </button>
      </p>
    </div>
  );
}
