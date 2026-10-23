
"use client";

import { useMemo, useState, type ChangeEvent } from "react";
import {
  Search,
  Plus,
  Folder,
  FileText,
  MoreHorizontal,
  SlidersHorizontal,
  BookOpen,
  X,
} from "lucide-react";
import CreateGroupModal, {
  type NewGroup,
} from "@/components/modals/CreateGroupModal";

interface Group {
  id: number;
  name: string;
  color: string;
  files: string[];
}

const INITIAL_GROUPS: Group[] = [
  {
    id: 1,
    name: "Matemática",
    color: "#8B5CF6",
    files: ["Trabajo_Practico.pdf", "Resumen_Materia.pdf"],
  },
  {
    id: 2,
    name: "Lengua",
    color: "#3B82F6",
    files: ["Trabajo_Practico.pdf"],
  },
  {
    id: 3,
    name: "Historia",
    color: "#F97316",
    files: [],
  },
  {
    id: 4,
    name: "Biología",
    color: "#22C55E",
    files: [],
  },
  {
    id: 5,
    name: "Física",
    color: "#EC4899",
    files: [],
  },
];

export default function MisArchivosPage() {
  const [groups, setGroups] = useState<Group[]>(INITIAL_GROUPS);
  const [search, setSearch] = useState("");
  const [filter, setFilter] = useState("todos");
  const [modalOpen, setModalOpen] = useState(false);
  const [notice, setNotice] = useState("");

  const visibleGroups = useMemo(() => {
    const query = search.trim().toLocaleLowerCase("es");

    return groups.filter((group) => {
      const matchesSearch =
        group.name.toLocaleLowerCase("es").includes(query) ||
        group.files.some((file) =>
          file.toLocaleLowerCase("es").includes(query),
        );

      const matchesFilter =
        filter === "todos" ||
        (filter === "con-archivos" && group.files.length > 0) ||
        (filter === "sin-archivos" && group.files.length === 0);

      return matchesSearch && matchesFilter;
    });
  }, [groups, search, filter]);

  function handleCreateGroup(newGroup: NewGroup) {
    const alreadyExists = groups.some(
      (group) =>
        group.name.toLocaleLowerCase("es") ===
        newGroup.name.trim().toLocaleLowerCase("es"),
    );

    if (alreadyExists) {
      setNotice("Ya existe un grupo con ese nombre.");
      return;
    }

    setGroups((current) => [
      ...current,
      {
        id: Date.now(),
        name: newGroup.name,
        color: newGroup.color,
        files: newGroup.file ? [newGroup.file.name] : [],
      },
    ]);

    setModalOpen(false);
    setSearch("");
    setFilter("todos");
    setNotice(
      newGroup.file
        ? `Grupo "${newGroup.name}" creado con el archivo seleccionado.`
        : `Grupo "${newGroup.name}" creado correctamente.`,
    );
  }

  function handleSearchChange(event: ChangeEvent<HTMLInputElement>) {
    setSearch(event.target.value);
    setNotice("");
  }

  return (
    <main className="min-h-screen bg-gray-50 px-4 py-8 text-gray-900 sm:px-8 lg:px-12">
      <div className="mx-auto max-w-7xl">
        <header className="mb-8 flex flex-col gap-5 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <div className="mb-3 flex items-center gap-2 text-sm text-gray-500">
              <BookOpen size={17} aria-hidden="true" />
              <span>InclusIA</span>
              <span aria-hidden="true">/</span>
              <span>Mis archivos</span>
            </div>

            <h1 className="text-3xl font-bold tracking-tight sm:text-4xl">
              Mis archivos
            </h1>

            <p className="mt-2 max-w-xl text-gray-600">
              Accedé a tus documentos y organizalos como prefieras.
            </p>
          </div>

          <button
            type="button"
            onClick={() => {
              setNotice("");
              setModalOpen(true);
            }}
            className="inline-flex min-h-12 items-center justify-center gap-2 rounded-xl bg-violet-600 px-5 py-3 font-semibold text-white shadow-sm transition hover:bg-violet-700 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-violet-600"
          >
            <Plus size={20} aria-hidden="true" />
            Crear grupo
          </button>
        </header>

        {notice && (
          <div
            role="status"
            className="mb-5 flex items-start justify-between gap-3 rounded-xl border border-violet-200 bg-violet-50 p-4 text-sm text-violet-900"
          >
            <p>{notice}</p>
            <button
              type="button"
              onClick={() => setNotice("")}
              aria-label="Cerrar mensaje"
              className="rounded p-1 hover:bg-violet-100"
            >
              <X size={17} />
            </button>
          </div>
        )}

        <section
          aria-label="Buscar y filtrar archivos"
          className="mb-8 flex flex-col gap-3 rounded-2xl border border-gray-200 bg-white p-4 shadow-sm sm:flex-row sm:items-center"
        >
          <div className="relative flex-1">
            <Search
              size={19}
              aria-hidden="true"
              className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400"
            />

            <label htmlFor="search-groups" className="sr-only">
              Buscar por nombre de grupo o archivo
            </label>

            <input
              id="search-groups"
              type="search"
              value={search}
              onChange={handleSearchChange}
              placeholder="Buscar por nombre de archivo, curso o materia..."
              className="min-h-12 w-full rounded-xl border border-gray-200 bg-gray-50 py-3 pl-10 pr-4 outline-none transition focus:border-violet-500 focus:ring-2 focus:ring-violet-100"
            />
          </div>

          <div className="flex items-center gap-2">
            <SlidersHorizontal
              size={18}
              aria-hidden="true"
              className="text-gray-500"
            />

            <label htmlFor="filter-groups" className="sr-only">
              Filtrar grupos
            </label>

            <select
              id="filter-groups"
              value={filter}
              onChange={(event) => setFilter(event.target.value)}
              className="min-h-12 flex-1 rounded-xl border border-gray-200 bg-white px-3 py-3 text-sm outline-none focus:border-violet-500 focus:ring-2 focus:ring-violet-100 sm:flex-none"
            >
              <option value="todos">Todos los grupos</option>
              <option value="con-archivos">Con archivos</option>
              <option value="sin-archivos">Sin archivos</option>
            </select>
          </div>
        </section>

        <div className="mb-5 flex items-center justify-between gap-3">
          <div>
            <h2 className="text-xl font-bold">Mis grupos</h2>
            <p className="mt-1 text-sm text-gray-500">
              {visibleGroups.length}{" "}
              {visibleGroups.length === 1 ? "grupo" : "grupos"}
            </p>
          </div>
        </div>

        {visibleGroups.length > 0 ? (
          <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
            {visibleGroups.map((group) => (
              <article
                key={group.id}
                className="overflow-hidden rounded-2xl border border-gray-200 bg-white shadow-sm transition hover:-translate-y-0.5 hover:shadow-md"
              >
                <div
                  className="h-2"
                  style={{ backgroundColor: group.color }}
                />

                <div className="p-5">
                  <div className="mb-5 flex items-start justify-between gap-3">
                    <div
                      className="rounded-xl p-3"
                      style={{
                        backgroundColor: `${group.color}20`,
                        color: group.color,
                      }}
                    >
                      <Folder size={25} aria-hidden="true" />
                    </div>

                    <button
                      type="button"
                      aria-label={`Más opciones para ${group.name}`}
                      title="Más opciones"
                      onClick={() =>
                        setNotice(
                          `Grupo "${group.name}". Las opciones adicionales todavía no están implementadas.`,
                        )
                      }
                      className="rounded-lg p-2 text-gray-400 hover:bg-gray-100 hover:text-gray-700 focus-visible:outline-2 focus-visible:outline-violet-600"
                    >
                      <MoreHorizontal size={21} />
                    </button>
                  </div>

                  <h3 className="break-words text-lg font-bold">
                    {group.name}
                  </h3>

                  <p className="mt-1 text-sm text-gray-500">
                    {group.files.length}{" "}
                    {group.files.length === 1 ? "archivo" : "archivos"}
                  </p>

                  <div className="mt-5 border-t border-gray-100 pt-4">
                    {group.files.length > 0 ? (
                      <ul className="space-y-3">
                        {group.files.slice(0, 3).map((file, index) => (
                          <li
                            key={`${group.id}-${file}-${index}`}
                            className="flex min-w-0 items-center gap-2 text-sm text-gray-600"
                          >
                            <FileText
                              size={17}
                              className="shrink-0 text-gray-400"
                              aria-hidden="true"
                            />
                            <span className="truncate">{file}</span>
                          </li>
                        ))}

                        {group.files.length > 3 && (
                          <li className="text-xs text-gray-500">
                            Y {group.files.length - 3} archivos más
                          </li>
                        )}
                      </ul>
                    ) : (
                      <p className="text-sm text-gray-400">
                        Todavía no hay archivos.
                      </p>
                    )}
                  </div>
                </div>
              </article>
            ))}
          </div>
        ) : (
          <div className="rounded-2xl border border-dashed border-gray-300 bg-white px-6 py-14 text-center">
            <Folder
              size={42}
              className="mx-auto mb-4 text-gray-300"
              aria-hidden="true"
            />
            <h3 className="text-lg font-semibold">
              No encontramos grupos
            </h3>
            <p className="mx-auto mt-2 max-w-md text-sm text-gray-500">
              Probá con otra búsqueda o cambiá los filtros para ver tus grupos.
            </p>
            <button
              type="button"
              onClick={() => {
                setSearch("");
                setFilter("todos");
              }}
              className="mt-5 rounded-lg px-4 py-2 font-medium text-violet-700 hover:bg-violet-50 focus-visible:outline-2 focus-visible:outline-violet-600"
            >
              Limpiar búsqueda y filtros
            </button>
          </div>
        )}

        <p className="mt-8 text-xs leading-5 text-gray-500">
          Vista de demostración: los grupos y archivos se mantienen en el
          estado de esta página. La persistencia y la carga al servidor
          requieren integración con el backend.
        </p>
      </div>

      <CreateGroupModal
        isOpen={modalOpen}
        onClose={() => setModalOpen(false)}
        onCreate={handleCreateGroup}
      />
    </main>
  );
}
