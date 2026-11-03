import {
  Download,
  FileUp,
  PencilRuler,
  ScanSearch,
  TriangleAlert,
} from "lucide-react";

const steps = [
  {
    title: "Subí tu PDF",
    description: "Empezá con el material educativo que querés revisar.",
    icon: FileUp,
    color: "bg-blue-100 text-blue-700",
  },
  {
    title: "La IA lo analiza",
    description: "LUMI explora estructura, lectura y elementos visuales.",
    icon: ScanSearch,
    color: "bg-indigo-100 text-indigo-700",
  },
  {
    title: "Revisá los hallazgos",
    description: "Priorizá las barreras detectadas y evaluá cada sugerencia.",
    icon: TriangleAlert,
    color: "bg-amber-100 text-amber-800",
  },
  {
    title: "Editá si lo necesitás",
    description: "Aplicá los cambios que tengan sentido para tu contexto.",
    icon: PencilRuler,
    color: "bg-emerald-100 text-emerald-800",
  },
  {
    title: "Guardá y descargá",
    description: "Prepará una versión revisada para compartir con tu clase.",
    icon: Download,
    color: "bg-sky-100 text-sky-800",
  },
];

export default function HowItWorksSection() {
  return (
    <section
      id="como-funciona"
      className="scroll-mt-24 bg-white px-5 py-20 sm:px-8 lg:py-24"
    >
      <div className="mx-auto max-w-7xl">
        <div className="mx-auto max-w-2xl text-center">
          <p className="text-sm font-bold uppercase text-blue-700">
            Un camino simple
          </p>
          <h2 className="mt-3 text-3xl font-bold text-slate-900 sm:text-4xl">
            ¿Cómo funciona?
          </h2>
          <p className="mt-4 text-base leading-7 text-slate-600 sm:text-lg">
            De un documento por revisar a una guía clara para crear una
            experiencia de aprendizaje más accesible.
          </p>
        </div>
        <ol className="relative mt-14 grid gap-8 sm:grid-cols-2 lg:grid-cols-5 lg:gap-5">
          <div
            aria-hidden="true"
            className="absolute left-[10%] right-[10%] top-8 hidden h-0.5 bg-linear-to-r from-blue-300 via-indigo-300 to-emerald-300 lg:block"
          />
          {steps.map((step, index) => {
            const Icon = step.icon;
            return (
              <li
                key={step.title}
                className="relative flex flex-col items-center text-center"
              >
                <div
                  className={`relative z-10 grid size-16 place-items-center rounded-2xl ${step.color} ring-8 ring-white`}
                >
                  <Icon
                    aria-hidden="true"
                    className="size-7"
                    strokeWidth={1.8}
                  />
                </div>
                <span className="mt-5 text-xs font-bold uppercase text-blue-700">
                  Paso {index + 1}
                </span>
                <h3 className="mt-2 text-lg font-bold text-slate-900">
                  {step.title}
                </h3>
                <p className="mt-2 max-w-xs text-sm leading-6 text-slate-600">
                  {step.description}
                </p>
              </li>
            );
          })}
        </ol>
        <p className="mx-auto mt-12 max-w-3xl rounded-xl border border-blue-100 bg-blue-50 px-5 py-4 text-center text-sm leading-6 text-blue-950">
          La IA puede equivocarse: cada adaptación se revisa y se decide con
          criterio docente.
        </p>
      </div>
    </section>
  );
}
