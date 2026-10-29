
export default function InicioPage() {
  return (
    <section className="p-6 sm:p-10">
      <header className="mb-8">
        <p className="mb-2 text-sm font-medium text-violet-700">
          Espacio de trabajo
        </p>

        <h1 className="text-3xl font-bold tracking-tight text-slate-900">
          ¡Bienvenida a InclusIA!
        </h1>

        <p className="mt-3 max-w-2xl text-slate-600">
          Un espacio para revisar la accesibilidad de tus materiales
          educativos y preparar recursos más inclusivos para tus estudiantes.
        </p>
      </header>

      <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
        <h2 className="text-lg font-semibold text-slate-900">
          Tu espacio de trabajo
        </h2>

        <p className="mt-2 text-sm leading-6 text-slate-600">
          Desde el menú lateral podrás acceder a tus archivos, consultar el
          historial de análisis y configurar tus preferencias.
        </p>
      </div>
    </section>
  );
}
