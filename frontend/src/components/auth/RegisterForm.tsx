"use client";

import { useState, type FormEvent } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import GoogleAuthButton from "@/components/auth/GoogleAuthButton";
import PasswordField from "@/components/auth/PasswordField";
import TextField from "@/components/auth/TextField";
import { isValidEmail } from "@/components/auth/auth-validation";

interface RegisterValues {
  firstName: string;
  lastName: string;
  phone: string;
  email: string;
  password: string;
  acceptedTerms: boolean;
  receiveNews: boolean;
}

type RegisterField = keyof RegisterValues;
type RegisterErrors = Partial<Record<RegisterField, string>>;

export default function RegisterForm() {
  const router = useRouter();
  const [values, setValues] = useState<RegisterValues>({
    firstName: "",
    lastName: "",
    phone: "",
    email: "",
    password: "",
    acceptedTerms: false,
    receiveNews: false,
  });
  const [errors, setErrors] = useState<RegisterErrors>({});
  const [helpNotice, setHelpNotice] = useState("");

  function updateText(
    field: Exclude<RegisterField, "acceptedTerms" | "receiveNews">,
    value: string,
  ) {
    setValues((current) => ({ ...current, [field]: value }));
    setErrors((current) => ({ ...current, [field]: undefined }));
  }

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const nextErrors: RegisterErrors = {};

    if (!values.firstName.trim()) nextErrors.firstName = "Ingresá tu nombre.";
    if (!values.lastName.trim()) nextErrors.lastName = "Ingresá tu apellido.";
    if (!values.phone.trim())
      nextErrors.phone = "Ingresá tu número telefónico.";
    if (!values.email.trim())
      nextErrors.email = "Ingresá tu correo electrónico.";
    else if (!isValidEmail(values.email))
      nextErrors.email = "Ingresá un correo electrónico válido.";
    if (values.password.length < 8)
      nextErrors.password = "Usá al menos 8 caracteres.";
    if (!values.acceptedTerms)
      nextErrors.acceptedTerms =
        "Necesitás aceptar los términos y condiciones.";

    setErrors(nextErrors);
    if (Object.keys(nextErrors).length > 0) {
      const firstInvalidField = (
        [
          "firstName",
          "lastName",
          "phone",
          "email",
          "password",
          "acceptedTerms",
        ] as const
      ).find((field) => nextErrors[field]);
      const firstInvalidControl = firstInvalidField
        ? event.currentTarget.elements.namedItem(firstInvalidField)
        : null;
      if (firstInvalidControl instanceof HTMLElement)
        firstInvalidControl.focus();
      return;
    }

    router.push("/inicio");
  }

  return (
    <div>
      <p className="text-sm font-bold uppercase text-blue-700">
        Un primer paso
      </p>
      <h1
        id="auth-heading"
        className="mt-2 text-3xl font-bold text-slate-900 sm:text-4xl"
      >
        Crear cuenta
      </h1>
      <p className="mt-2 text-sm leading-6 text-slate-600">
        Sumate a una comunidad que crea materiales para aprender sin barreras.
      </p>

      <form
        noValidate
        onSubmit={handleSubmit}
        aria-labelledby="auth-heading"
        className="mt-6 space-y-4"
      >
        <div className="grid gap-4 sm:grid-cols-2">
          <TextField
            id="firstName"
            label="Nombre"
            placeholder="Ingresa tu nombre"
            autoComplete="given-name"
            value={values.firstName}
            error={errors.firstName}
            onChange={(value) => updateText("firstName", value)}
          />
          <TextField
            id="lastName"
            label="Apellido"
            placeholder="Ingresa tu apellido"
            autoComplete="family-name"
            value={values.lastName}
            error={errors.lastName}
            onChange={(value) => updateText("lastName", value)}
          />
        </div>
        <TextField
          id="phone"
          label="Teléfono"
          type="tel"
          placeholder="Ingresa tu número telefónico"
          autoComplete="tel"
          maxLength={30}
          value={values.phone}
          error={errors.phone}
          onChange={(value) => updateText("phone", value)}
        />
        <TextField
          id="email"
          label="Correo electrónico"
          type="email"
          placeholder="Ingresa tu correo electrónico"
          autoComplete="email"
          value={values.email}
          error={errors.email}
          onChange={(value) => updateText("email", value)}
        />
        <PasswordField
          id="password"
          autoComplete="new-password"
          placeholder="Ingresa tu contraseña"
          value={values.password}
          error={errors.password}
          onChange={(value) => updateText("password", value)}
        />

        <div className="space-y-3 pt-1">
          <div>
            <label
              htmlFor="acceptedTerms"
              className="flex cursor-pointer items-start gap-2.5 text-sm leading-5 text-slate-700"
            >
              <input
                id="acceptedTerms"
                name="acceptedTerms"
                type="checkbox"
                checked={values.acceptedTerms}
                aria-invalid={Boolean(errors.acceptedTerms)}
                aria-describedby={
                  errors.acceptedTerms ? "acceptedTerms-error" : undefined
                }
                onChange={(event) => {
                  const acceptedTerms = event.currentTarget.checked;
                  setValues((current) => ({ ...current, acceptedTerms }));
                  setErrors((current) => ({
                    ...current,
                    acceptedTerms: undefined,
                  }));
                }}
                className="mt-0.5 size-4 shrink-0 accent-blue-600 focus-visible:outline-blue-600"
              />
              <span>
                He leído y acepto términos y condiciones{" "}
                <span aria-hidden="true" className="text-rose-700">
                  *
                </span>
              </span>
            </label>
            {errors.acceptedTerms && (
              <p
                id="acceptedTerms-error"
                role="alert"
                className="ml-6 mt-1 text-sm font-medium text-rose-700"
              >
                {errors.acceptedTerms}
              </p>
            )}
          </div>
          <label
            htmlFor="receiveNews"
            className="flex cursor-pointer items-start gap-2.5 text-sm leading-5 text-slate-700"
          >
            <input
              id="receiveNews"
              name="receiveNews"
              type="checkbox"
              checked={values.receiveNews}
              onChange={(event) => {
                const receiveNews = event.currentTarget.checked;
                setValues((current) => ({ ...current, receiveNews }));
              }}
              className="mt-0.5 size-4 shrink-0 accent-blue-600 focus-visible:outline-blue-600"
            />
            <span>Deseo recibir novedades de LUMI</span>
          </label>
        </div>

        <div className="grid gap-3 pt-1 sm:grid-cols-2">
          <button
            type="submit"
            className="min-h-12 rounded-lg bg-blue-600 px-4 py-3 text-sm font-semibold text-white shadow-sm transition hover:bg-blue-700 focus-visible:outline-blue-600"
          >
            Crear cuenta
          </button>
          <Link
            href="/login"
            className="inline-flex min-h-12 items-center justify-center rounded-lg border border-slate-300 px-4 py-3 text-sm font-semibold text-slate-700 transition hover:border-blue-300 hover:bg-blue-50 focus-visible:outline-blue-600"
          >
            Iniciar sesión
          </Link>
        </div>
      </form>

      <div className="my-5 flex items-center gap-4" aria-hidden="true">
        <span className="h-px flex-1 bg-slate-200" />
        <span className="text-xs font-medium text-slate-500">o también</span>
        <span className="h-px flex-1 bg-slate-200" />
      </div>
      <GoogleAuthButton label="Registrarse con Google" />

      <p className="mt-6 text-center text-sm text-slate-600">
        ¿Necesitas ayuda con Lumi?{" "}
        <button
          type="button"
          onClick={() =>
            setHelpNotice(
              "Para recibir ayuda, contactá al equipo de LUMI cuando el canal de soporte esté disponible.",
            )
          }
          className="rounded-sm font-semibold text-blue-700 underline-offset-4 hover:underline"
        >
          Clickea aquí
        </button>
      </p>
      <p
        role="status"
        aria-live="polite"
        className="mt-2 min-h-5 text-center text-sm text-slate-600"
      >
        {helpNotice}
      </p>
    </div>
  );
}
