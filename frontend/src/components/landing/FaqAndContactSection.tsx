"use client";

import { useState, type FormEvent } from "react";
import Link from "next/link";
import { ArrowRight, BookOpenCheck, Sparkles } from "lucide-react";

const questions = [
  {
    question: "¿Qué tipos de PDF puedo revisar?",
    answer:
      "La experiencia está pensada para documentos educativos en PDF. Los archivos con texto seleccionable suelen ofrecer más información que un escaneo; un documento escaneado puede requerir reconocimiento óptico de caracteres (OCR), y los resultados pueden variar.",
  },
  {
    question: "¿La inteligencia artificial hace los cambios por mí?",
    answer:
      "No. La IA funciona como asistente: señala posibles barreras y propone alternativas. La persona docente revisa cada hallazgo y decide qué cambio tiene sentido para su material y su grupo.",
  },
  {
    question: "¿LUMI garantiza que mi PDF cumple WCAG 2.1 AA?",
    answer:
      "No. Las pautas WCAG 2.1 AA son una referencia para orientar la revisión, pero una sugerencia automática no equivale a una auditoría ni a una certificación. La accesibilidad requiere evaluación humana y pruebas con tecnologías de apoyo.",
  },
  {
    question: "¿Qué debería revisar antes de usar un documento?",
    answer:
      "Considerá si el texto se puede seleccionar, si las imágenes importantes tienen una descripción útil, si el orden de lectura es claro y si el contraste facilita la lectura. No subas información sensible sin verificar antes las políticas aplicables a tu institución.",
  },
];

export default function FaqAndContactSection() {
  const [formMessage, setFormMessage] = useState("");

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = event.currentTarget;

    if (!form.reportValidity()) {
      setFormMessage("Revisá los campos indicados antes de continuar.");
      return;
    }

    setFormMessage(
      "La validación fue correcta. Esta demostración no envió ni guardó tus datos.",
    );
  }

  return (
    <>
      <section
        id="preguntas"
        className="scroll-mt-24 bg-white px-5 py-20 sm:px-8 lg:py-24"
      >
        <div className="mx-auto max-w-3xl">
          <p className="text-center text-sm font-bold uppercase text-blue-700">
            Respuestas claras
          </p>
          <h2 className="mt-3 text-center text-3xl font-bold text-slate-900 sm:text-4xl">
            Preguntas frecuentes
          </h2>
          <div className="mt-10 divide-y divide-slate-200 border-y border-slate-200">
            {questions.map((item) => (
              <details key={item.question} className="group py-1">
                <summary className="flex cursor-pointer list-none items-center justify-between gap-5 py-5 text-left text-base font-semibold text-slate-900 marker:content-none focus-visible:rounded-md [&::-webkit-details-marker]:hidden">
                  {item.question}
                  <span className="grid size-8 shrink-0 place-items-center rounded-full bg-blue-50 text-blue-700 transition-transform group-open:rotate-45">
                    <span
                      aria-hidden="true"
                      className="text-xl font-normal leading-none"
                    >
                      +
                    </span>
                  </span>
                </summary>
                <p className="max-w-2xl pb-5 pr-12 text-sm leading-7 text-slate-600">
                  {item.answer}
                </p>
              </details>
            ))}
          </div>
        </div>
      </section>

      <section
        id="contacto"
        className="scroll-mt-24 bg-slate-50 px-5 py-20 sm:px-8 lg:py-24"
      >
        <div className="mx-auto grid max-w-7xl gap-12 lg:grid-cols-[0.8fr_1.2fr] lg:gap-20">
          <div className="max-w-lg">
            <p className="text-sm font-bold uppercase text-blue-700">
              Hablemos
            </p>
            <h2 className="mt-3 text-3xl font-bold text-slate-900 sm:text-4xl">
              Contacto
            </h2>
            <p className="mt-4 text-base leading-7 text-slate-600">
              ¿Querés conocer más sobre LUMI o acercarnos una idea para tu
              institución? Dejanos un mensaje.
            </p>
            <div className="mt-8 rounded-xl border border-blue-100 bg-white p-5">
              <div className="flex items-start gap-3">
                <span className="grid size-10 shrink-0 place-items-center rounded-lg bg-blue-100 text-blue-700">
                  <Sparkles aria-hidden="true" className="size-5" />
                </span>
                <p className="text-sm leading-6 text-slate-700">
                  Tu experiencia ayuda a imaginar herramientas que acompañen
                  mejor la enseñanza inclusiva.
                </p>
              </div>
            </div>
          </div>

          <form
            noValidate
            onSubmit={handleSubmit}
            className="grid gap-x-5 gap-y-4 sm:grid-cols-2"
            aria-describedby="form-note form-status"
          >
            <p id="form-note" className="sm:col-span-2 text-sm text-slate-600">
              Los campos con{" "}
              <span className="font-semibold text-rose-700">*</span> son
              obligatorios.
            </p>
            <div>
              <label
                htmlFor="contact-name"
                className="mb-1.5 block text-sm font-semibold text-slate-800"
              >
                Nombre{" "}
                <span aria-hidden="true" className="text-rose-700">
                  *
                </span>
              </label>
              <input
                id="contact-name"
                name="name"
                type="text"
                autoComplete="name"
                required
                maxLength={100}
                onChange={() => setFormMessage("")}
                className="min-h-12 w-full rounded-lg border border-slate-300 bg-white px-3.5 py-3 text-slate-900 placeholder:text-slate-500 focus-visible:border-blue-600 focus-visible:outline-blue-600"
              />
            </div>
            <div>
              <label
                htmlFor="contact-email"
                className="mb-1.5 block text-sm font-semibold text-slate-800"
              >
                Email{" "}
                <span aria-hidden="true" className="text-rose-700">
                  *
                </span>
              </label>
              <input
                id="contact-email"
                name="email"
                type="email"
                autoComplete="email"
                required
                maxLength={254}
                onChange={() => setFormMessage("")}
                className="min-h-12 w-full rounded-lg border border-slate-300 bg-white px-3.5 py-3 text-slate-900 placeholder:text-slate-500 focus-visible:border-blue-600 focus-visible:outline-blue-600"
              />
            </div>
            <div>
              <label
                htmlFor="contact-institution"
                className="mb-1.5 block text-sm font-semibold text-slate-800"
              >
                Institución
              </label>
              <input
                id="contact-institution"
                name="institution"
                type="text"
                autoComplete="organization"
                maxLength={150}
                className="min-h-12 w-full rounded-lg border border-slate-300 bg-white px-3.5 py-3 text-slate-900 placeholder:text-slate-500 focus-visible:border-blue-600 focus-visible:outline-blue-600"
              />
            </div>
            <div>
              <label
                htmlFor="contact-subject"
                className="mb-1.5 block text-sm font-semibold text-slate-800"
              >
                Asunto{" "}
                <span aria-hidden="true" className="text-rose-700">
                  *
                </span>
              </label>
              <input
                id="contact-subject"
                name="subject"
                type="text"
                required
                maxLength={150}
                onChange={() => setFormMessage("")}
                className="min-h-12 w-full rounded-lg border border-slate-300 bg-white px-3.5 py-3 text-slate-900 placeholder:text-slate-500 focus-visible:border-blue-600 focus-visible:outline-blue-600"
              />
            </div>
            <div className="sm:col-span-2">
              <label
                htmlFor="contact-message"
                className="mb-1.5 block text-sm font-semibold text-slate-800"
              >
                Mensaje{" "}
                <span aria-hidden="true" className="text-rose-700">
                  *
                </span>
              </label>
              <textarea
                id="contact-message"
                name="message"
                rows={5}
                required
                minLength={10}
                maxLength={2000}
                onChange={() => setFormMessage("")}
                className="w-full resize-y rounded-lg border border-slate-300 bg-white px-3.5 py-3 text-slate-900 placeholder:text-slate-500 focus-visible:border-blue-600 focus-visible:outline-blue-600"
              />
            </div>
            <div className="sm:col-span-2">
              <button
                type="submit"
                className="inline-flex min-h-12 items-center justify-center gap-2 rounded-lg bg-blue-600 px-5 py-3 font-semibold text-white transition hover:bg-blue-700 focus-visible:outline-offset-4"
              >
                Enviar consulta
                <ArrowRight aria-hidden="true" className="size-4" />
              </button>
              <p
                id="form-status"
                role="status"
                aria-live="polite"
                className="mt-3 min-h-6 text-sm font-medium text-slate-700"
              >
                {formMessage}
              </p>
            </div>
          </form>
        </div>
      </section>
    </>
  );
}

export function LandingFooter() {
  return (
    <footer className="bg-slate-950 px-5 pb-8 pt-12 text-white sm:px-8">
      <div className="mx-auto max-w-7xl">
        <div className="flex flex-col items-start justify-between gap-6 rounded-xl bg-linear-to-br from-blue-700 via-indigo-800 to-slate-900 p-6 sm:flex-row sm:items-center sm:p-8 lg:p-10">
          <div className="max-w-2xl">
            <div className="mb-3 inline-flex items-center gap-2 text-sm font-semibold text-emerald-200">
              <Sparkles aria-hidden="true" className="size-4" />
              Aprender también es incluir
            </div>
            <h2 className="text-2xl font-bold leading-tight text-white sm:text-3xl">
              ¿Listo para hacer tus documentos más inclusivos?
            </h2>
            <p className="mt-2 text-sm leading-6 text-blue-100 sm:text-base">
              Empezá a imaginar materiales donde más estudiantes puedan
              participar.
            </p>
          </div>
          <Link
            href="#contacto"
            className="inline-flex min-h-12 shrink-0 items-center justify-center gap-2 rounded-lg bg-white px-5 py-3 font-semibold text-blue-800 transition hover:bg-blue-50"
          >
            Hablemos
            <ArrowRight aria-hidden="true" className="size-4" />
          </Link>
        </div>

        <div className="grid gap-8 border-b border-white/15 py-9 sm:grid-cols-2 sm:items-center">
          <div>
            <Link
              href="/"
              aria-label="LUMI, ir al inicio"
              className="inline-flex items-center gap-2 rounded-md"
            >
              <span className="grid size-9 place-items-center rounded-lg bg-linear-to-br from-blue-500 to-indigo-500 text-white">
                <BookOpenCheck aria-hidden="true" className="size-5" />
              </span>
              <span className="font-extrabold">LUMI</span>
            </Link>
            <p className="mt-3 max-w-sm text-sm leading-6 text-slate-300">
              Una propuesta para acompañar la creación de materiales educativos
              más accesibles.
            </p>
          </div>
          <div className="sm:text-right">
            <p className="text-sm font-semibold text-white">
              Encontranos en redes
            </p>
            <ul
              className="mt-3 flex flex-wrap gap-x-4 gap-y-2 sm:justify-end"
              aria-label="Redes sociales"
            >
              <li>
                <a
                  href="https://www.linkedin.com/"
                  target="_blank"
                  rel="noreferrer"
                  className="rounded-sm text-sm text-slate-300 underline decoration-slate-500 underline-offset-4 hover:text-white"
                >
                  LinkedIn
                </a>
              </li>
              <li>
                <a
                  href="https://www.instagram.com/"
                  target="_blank"
                  rel="noreferrer"
                  className="rounded-sm text-sm text-slate-300 underline decoration-slate-500 underline-offset-4 hover:text-white"
                >
                  Instagram
                </a>
              </li>
              <li>
                <a
                  href="https://www.youtube.com/"
                  target="_blank"
                  rel="noreferrer"
                  className="rounded-sm text-sm text-slate-300 underline decoration-slate-500 underline-offset-4 hover:text-white"
                >
                  YouTube
                </a>
              </li>
              <li>
                <a
                  href="https://www.facebook.com/"
                  target="_blank"
                  rel="noreferrer"
                  className="rounded-sm text-sm text-slate-300 underline decoration-slate-500 underline-offset-4 hover:text-white"
                >
                  Facebook
                </a>
              </li>
            </ul>
          </div>
        </div>

        <div className="grid gap-3 pt-5 text-xs leading-5 text-slate-400 sm:grid-cols-2 sm:items-start">
          <p>© 2026 LUMI. Todos los derechos reservados.</p>
          <p id="aviso-legal" className="max-w-2xl">
            Las sugerencias son orientativas y no sustituyen una auditoría de
            accesibilidad ni garantizan conformidad con WCAG.
          </p>
          <p id="privacidad" className="max-w-2xl">
            Esta landing es demostrativa: no procesa documentos ni envía o
            almacena los datos ingresados en el formulario.
          </p>
          <ul className="flex flex-wrap gap-x-4 gap-y-2 sm:justify-end">
            <li>
              <a
                href="#aviso-legal"
                className="rounded-sm underline decoration-slate-500 underline-offset-4 hover:text-white"
              >
                Aviso legal
              </a>
            </li>
            <li>
              <a
                href="#privacidad"
                className="rounded-sm underline decoration-slate-500 underline-offset-4 hover:text-white"
              >
                Privacidad
              </a>
            </li>
          </ul>
        </div>
      </div>
    </footer>
  );
}
