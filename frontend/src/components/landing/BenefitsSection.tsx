import {
  Accessibility,
  Clock3,
  MonitorSmartphone,
  ShieldCheck,
  Sparkles,
  Target,
} from "lucide-react";

const benefits = [
  {
    title: "Ahorro de tiempo",
    description:
      "Encontrá primero lo que necesita atención y dedicá más tiempo a enseñar.",
    icon: Clock3,
    color: "bg-blue-100 text-blue-700",
  },
  {
    title: "Mayor precisión",
    description: "Revisá señales concretas de estructura, lectura e imágenes.",
    icon: Target,
    color: "bg-indigo-100 text-indigo-700",
  },
  {
    title: "Inclusión real",
    description: "Diseñá recursos que contemplen distintas formas de aprender.",
    icon: Accessibility,
    color: "bg-emerald-100 text-emerald-800",
  },
  {
    title: "Seguridad",
    description: "Mantené criterio y supervisión humana en cada decisión.",
    icon: ShieldCheck,
    color: "bg-sky-100 text-sky-800",
  },
  {
    title: "Multiplataforma",
    description:
      "Consultá tu material desde distintos dispositivos y tamaños de pantalla.",
    icon: MonitorSmartphone,
    color: "bg-amber-100 text-amber-900",
  },
  {
    title: "Evolución constante",
    description:
      "Una propuesta pensada para mejorar junto a las necesidades educativas.",
    icon: Sparkles,
    color: "bg-rose-100 text-rose-800",
  },
];

export default function BenefitsSection() {
  return (
    <section
      id="beneficios"
      className="scroll-mt-24 bg-sky-50 px-5 py-20 sm:px-8 lg:py-24"
    >
      <div className="mx-auto max-w-7xl">
        <div className="grid items-start gap-12 lg:grid-cols-[0.9fr_1.1fr] lg:gap-16">
          <div>
            <p className="text-sm font-bold uppercase text-blue-700">
              Acompañar para incluir
            </p>
            <h2 className="mt-3 max-w-xl text-3xl font-bold leading-tight text-slate-900 sm:text-4xl">
              Más que una herramienta, es un aliado en tu inclusión.
            </h2>
            <p className="mt-4 max-w-xl text-base leading-7 text-slate-600">
              Tecnología al servicio de tu experiencia y del derecho de cada
              estudiante a aprender.
            </p>
            <ul className="mt-8 grid gap-x-5 gap-y-7 sm:grid-cols-2">
              {benefits.map((benefit) => {
                const Icon = benefit.icon;
                return (
                  <li key={benefit.title} className="flex items-start gap-3">
                    <span
                      className={`grid size-10 shrink-0 place-items-center rounded-xl ${benefit.color}`}
                    >
                      <Icon aria-hidden="true" className="size-5" />
                    </span>
                    <div>
                      <h3 className="font-bold text-slate-900">
                        {benefit.title}
                      </h3>
                      <p className="mt-1 text-sm leading-6 text-slate-600">
                        {benefit.description}
                      </p>
                    </div>
                  </li>
                );
              })}
            </ul>
          </div>

          <div className="overflow-hidden rounded-xl border border-blue-200 bg-white shadow-lg shadow-blue-950/5">
            <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-200 px-5 py-4 sm:px-6">
              <div>
                <p className="text-xs font-bold uppercase text-blue-700">
                  Demostración
                </p>
                <h3 className="mt-1 text-lg font-bold text-slate-900">
                  Del hallazgo a una sugerencia
                </h3>
              </div>
              <span className="inline-flex items-center gap-1.5 rounded-full bg-emerald-50 px-3 py-1.5 text-xs font-semibold text-emerald-800">
                <Sparkles aria-hidden="true" className="size-3.5" />
                Vista de ejemplo
              </span>
            </div>
            <div className="grid divide-y divide-slate-200 md:grid-cols-2 md:divide-x md:divide-y-0">
              <div className="bg-slate-50 p-5 sm:p-6">
                <p className="mb-4 text-sm font-bold text-slate-700">
                  Documento original
                </p>
                <div className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
                  <p className="text-xs font-bold uppercase text-slate-500">
                    Actividad · Ciencias
                  </p>
                  <h4 className="mt-3 text-base font-bold text-slate-900">
                    Los ciclos del agua
                  </h4>
                  <div
                    className="mt-3 h-24 rounded-md bg-linear-to-br from-sky-100 via-blue-100 to-indigo-200"
                    role="img"
                    aria-label="Ilustración decorativa de nubes, lluvia y agua"
                  />
                  <p className="mt-3 rounded-md bg-amber-50 px-3 py-2 text-sm leading-6 text-amber-950">
                    Observá la imagen y explicá qué sucede.
                  </p>
                  <p className="mt-2 text-xs text-slate-500">
                    La ilustración no tiene descripción textual.
                  </p>
                </div>
              </div>
              <div className="p-5 sm:p-6">
                <p className="mb-4 text-sm font-bold text-slate-700">
                  Diagnóstico orientativo
                </p>
                <div className="space-y-4">
                  <div className="border-l-4 border-amber-400 pl-4">
                    <p className="text-sm font-bold text-slate-900">
                      Imagen informativa
                    </p>
                    <p className="mt-1 text-sm leading-6 text-slate-600">
                      La consigna depende de una ilustración sin alternativa
                      textual.
                    </p>
                  </div>
                  <div className="rounded-lg bg-blue-50 p-4">
                    <p className="text-sm font-bold text-blue-950">
                      Sugerencia pedagógica
                    </p>
                    <p className="mt-1.5 text-sm leading-6 text-blue-950">
                      Describí las etapas principales o incorporá una secuencia
                      breve en texto.
                    </p>
                  </div>
                  <p className="text-xs leading-5 text-slate-500">
                    Ejemplo ilustrativo. Revisá la sugerencia según el objetivo
                    de tu actividad; no es una certificación de conformidad.
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
