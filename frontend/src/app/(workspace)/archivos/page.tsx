
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
  List,
  LayoutGrid,
  Files,
  ChevronDown,
  ChevronRight,
  ArrowUpDown,
  Check,
  Eye,
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

type ViewMode = "lista" | "iconos" | "archivos";
type FilterMode = "todos" | "con-archivos" | "sin-archivos";
type SortMode = "nombre" | "nombre-desc";
type GroupMode = "materia" | "estado";

interface DocumentItem {
  id: string;
  name: string;
  groupName: string;
  groupId: number;
  color: string;
  status: string;
  date: string;
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
  const [filter, setFilter] = useState<FilterMode>("todos");
  const [sort, setSort] = useState<SortMode>("nombre");
  const [groupMode, setGroupMode] = useState<GroupMode>("materia");
  const [view, setView] = useState<ViewMode>("lista");
  const [modalOpen, setModalOpen] = useState(false);
  const [notice, setNotice] = useState("");
  const [expandedGroups, setExpandedGroups] = useState<number[]>(
    INITIAL_GROUPS.map((group) => group.id)
  );
  const [selectedFiles, setSelectedFiles] = useState<string[]>([]);

  const documents = useMemo<DocumentItem[]>(() => {
    return groups.flatMap((group) =>
      group.files.map((file, index) => ({
        id: `${group.id}-${index}-${file}`,
        name: file,
        groupName: group.name,
        groupId: group.id,
        color: group.color,
        status: "Disponible",
        date: "Sin fecha",
      }))
    );
  }, [groups]);

  const visibleGroups = useMemo(() => {
    const normalizedSearch = search.trim().toLowerCase();

    return groups
      .filter((group) => {
        const matchesSearch =
          !normalizedSearch ||
          group.name.toLowerCase().includes(normalizedSearch) ||
          group.files.some((file) =>
            file.toLowerCase().includes(normalizedSearch)
          );

        const matchesFilter =
          filter === "todos" ||
          (filter === "con-archivos" && group.files.length > 0) ||
          (filter === "sin-archivos" && group.files.length === 0);

        return matchesSearch && matchesFilter;
      })
      .sort((a, b) =>
        sort === "nombre-desc"
          ? b.name.localeCompare(a.name, "es")
          : a.name.localeCompare(b.name, "es")
      );
  }, [groups, search, filter, sort]);

  const visibleDocuments = useMemo(() => {
    const allowedGroupIds = new Set(visibleGroups.map((group) => group.id));

    return documents
      .filter((document) => allowedGroupIds.has(document.groupId))
      .filter((document) => {
        const normalizedSearch = search.trim().toLowerCase();

        return (
          !normalizedSearch ||
          document.name.toLowerCase().includes(normalizedSearch) ||
          document.groupName.toLowerCase().includes(normalizedSearch)
        );
      })
      .sort((a, b) =>
        sort === "nombre-desc"
          ? b.name.localeCompare(a.name, "es")
          : a.name.localeCompare(b.name, "es")
      );
  }, [documents, visibleGroups, search, sort]);

  const toggleGroup = (groupId: number) => {
    setExpandedGroups((current) =>
      current.includes(groupId)
        ? current.filter((id) => id !== groupId)
        : [...current, groupId]
    );
  };

  const toggleFile = (fileId: string) => {
    setSelectedFiles((current) =>
      current.includes(fileId)
        ? current.filter((id) => id !== fileId)
        : [...current, fileId]
    );
  };

  const toggleAllVisible = () => {
    const visibleIds = visibleDocuments.map((document) => document.id);
    const allSelected =
      visibleIds.length > 0 &&
      visibleIds.every((id) => selectedFiles.includes(id));

    setSelectedFiles((current) =>
      allSelected
        ? current.filter((id) => !visibleIds.includes(id))
        : [...new Set([...current, ...visibleIds])]
    );
  };

  const handleCreateGroup = (newGroup: NewGroup) => {
    const exists = groups.some(
      (group) =>
        group.name.trim().toLowerCase() ===
        newGroup.name.trim().toLowerCase()
    );

    if (exists) {
      setNotice("Ya existe una materia con ese nombre.");
      return;
    }

    const group: Group = {
      id: Date.now(),
      name: newGroup.name.trim(),
      color: newGroup.color,
      files: newGroup.file ? [newGroup.file.name] : [],
    };

    setGroups((current) => [...current, group]);
    setExpandedGroups((current) => [...current, group.id]);
    setSearch("");
    setFilter("todos");
    setNotice(`Se creó el grupo "${group.name}".`);
    setModalOpen(false);
  };

  const handleSearchChange = (event: ChangeEvent<HTMLInputElement>) => {
    setSearch(event.target.value);
  };

  const allVisibleSelected =
    visibleDocuments.length > 0 &&
    visibleDocuments.every((document) =>
      selectedFiles.includes(document.id)
    );

  return (
    <main className="min-h-screen bg-slate-50 px-4 py-6 text-slate-800 sm:px-6 lg:px-8">
      <div className="mx-auto max-w-7xl">
        <header className="mb-8 flex flex-col justify-between gap-4 sm:flex-row sm:items-center">
          <div>
            <p className="mb-2 text-sm font-semibold text-green-700">
              InclusIA
            </p>
            <h1 className="text-3xl font-bold tracking-tight">Mis archivos</h1>
            <p className="mt-2 text-sm text-slate-500">
              Organizá tus documentos y materiales por materia.
            </p>
          </div>

          <button
            type="button"
            onClick={() => {
              setNotice("");
              setModalOpen(true);
            }}
            className="inline-flex items-center justify-center gap-2 rounded-xl bg-green-600 px-5 py-3 font-semibold text-white shadow-sm transition hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-green-500 focus:ring-offset-2"
          >
            <Plus size={19} />
            Crear grupo
          </button>
        </header>

        {notice && (
          <div
            role="status"
            className="mb-5 flex items-center justify-between gap-3 rounded-xl border border-green-200 bg-green-50 px-4 py-3 text-sm text-green-800"
          >
            <span>{notice}</span>
            <button
              type="button"
              onClick={() => setNotice("")}
              aria-label="Cerrar aviso"
            >
              <X size={18} />
            </button>
          </div>
        )}

        <section
          aria-label="Herramientas de documentos"
          className="mb-6 rounded-2xl border border-slate-200 bg-white p-4 shadow-sm"
        >
          <div className="flex flex-col gap-4">
            <div className="relative">
              <Search
                size={19}
                className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400"
              />
              <input
                type="search"
                value={search}
                onChange={handleSearchChange}
                placeholder="Buscar por materia o nombre de archivo..."
                aria-label="Buscar archivos y materias"
                className="w-full rounded-xl border border-slate-200 py-3 pl-10 pr-4 outline-none transition focus:border-green-500 focus:ring-2 focus:ring-green-100"
              />
            </div>

            <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
              <div className="flex flex-wrap items-center gap-2">
                <span className="inline-flex items-center gap-2 text-sm font-medium text-slate-600">
                  <SlidersHorizontal size={17} />
                  Filtros
                </span>

                <select
                  aria-label="Filtrar materias"
                  value={filter}
                  onChange={(event) =>
                    setFilter(event.target.value as FilterMode)
                  }
                  className="rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm outline-none focus:border-green-500"
                >
                  <option value="todos">Todas las materias</option>
                  <option value="con-archivos">Con archivos</option>
                  <option value="sin-archivos">Sin archivos</option>
                </select>

                <label className="flex items-center gap-2 rounded-lg border border-slate-200 px-3 py-2 text-sm">
                  <ArrowUpDown size={16} className="text-slate-500" />
                  <span>Ordenar</span>
                  <select
                    aria-label="Ordenar archivos"
                    value={sort}
                    onChange={(event) =>
                      setSort(event.target.value as SortMode)
                    }
                    className="max-w-32 bg-transparent outline-none"
                  >
                    <option value="nombre">A–Z</option>
                    <option value="nombre-desc">Z–A</option>
                  </select>
                </label>

                <label className="flex items-center gap-2 rounded-lg border border-slate-200 px-3 py-2 text-sm">
                  <Folder size={16} className="text-slate-500" />
                  <span>Agrupar</span>
                  <select
                    aria-label="Agrupar documentos"
                    value={groupMode}
                    onChange={(event) =>
                      setGroupMode(event.target.value as GroupMode)
                    }
                    className="max-w-32 bg-transparent outline-none"
                  >
                    <option value="materia">Materia</option>
                    <option value="estado">Estado</option>
                  </select>
                </label>
              </div>

              <div
                className="flex flex-wrap items-center gap-1 rounded-xl bg-slate-100 p-1"
                role="group"
                aria-label="Selector de vista"
              >
                <button
                  type="button"
                  onClick={() => setView("lista")}
                  aria-pressed={view === "lista"}
                  className={`inline-flex items-center gap-2 rounded-lg px-3 py-2 text-sm font-medium transition ${
                    view === "lista"
                      ? "bg-white text-green-700 shadow-sm"
                      : "text-slate-600 hover:text-slate-900"
                  }`}
                >
                  <List size={17} />
                  Lista
                </button>
                <button
                  type="button"
                  onClick={() => setView("iconos")}
                  aria-pressed={view === "iconos"}
                  className={`inline-flex items-center gap-2 rounded-lg px-3 py-2 text-sm font-medium transition ${
                    view === "iconos"
                      ? "bg-white text-green-700 shadow-sm"
                      : "text-slate-600 hover:text-slate-900"
                  }`}
                >
                  <LayoutGrid size={17} />
                  Iconos
                </button>
                <button
                  type="button"
                  onClick={() => setView("archivos")}
                  aria-pressed={view === "archivos"}
                  className={`inline-flex items-center gap-2 rounded-lg px-3 py-2 text-sm font-medium transition ${
                    view === "archivos"
                      ? "bg-white text-green-700 shadow-sm"
                      : "text-slate-600 hover:text-slate-900"
                  }`}
                >
                  <Files size={17} />
                  Archivos
                </button>
              </div>
            </div>
          </div>
        </section>

        {selectedFiles.length > 0 && (
          <div className="mb-4 flex flex-wrap items-center justify-between gap-3 rounded-xl border border-green-200 bg-green-50 px-4 py-3">
            <p className="text-sm font-medium text-green-800">
              {selectedFiles.length} documento(s) seleccionado(s)
            </p>
            <button
              type="button"
              onClick={() => setSelectedFiles([])}
              className="text-sm font-semibold text-green-800 underline underline-offset-2"
            >
              Quitar selección
            </button>
          </div>
        )}

        <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
          <div>
            <h2 className="text-xl font-bold">
              {groupMode === "materia" ? "Mis materias" : "Documentos por estado"}
            </h2>
            <p className="mt-1 text-sm text-slate-500">
              {groupMode === "materia"
                ? `${visibleGroups.length} materia(s)`
                : `${visibleDocuments.length} documento(s)`}
            </p>
          </div>

          {view === "lista" && visibleDocuments.length > 0 && (
            <button
              type="button"
              onClick={toggleAllVisible}
              className="inline-flex items-center gap-2 rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm font-medium hover:bg-slate-50"
            >
              {allVisibleSelected ? (
                <X size={16} />
              ) : (
                <Check size={16} />
              )}
              {allVisibleSelected ? "Deseleccionar visibles" : "Seleccionar visibles"}
            </button>
          )}
        </div>

        {groupMode === "materia" ? (
          <div className="space-y-4">
            {visibleGroups.map((group) => {
              const groupDocuments = visibleDocuments.filter(
                (document) => document.groupId === group.id
              );
              const isExpanded = expandedGroups.includes(group.id);

              return (
                <section
                  key={group.id}
                  className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm"
                >
                  <button
                    type="button"
                    onClick={() => toggleGroup(group.id)}
                    aria-expanded={isExpanded}
                    className="flex w-full items-center gap-3 p-4 text-left transition hover:bg-slate-50 sm:p-5"
                  >
                    <span
                      className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl"
                      style={{
                        backgroundColor: `${group.color}18`,
                        color: group.color,
                      }}
                    >
                      <BookOpen size={22} />
                    </span>

                    <span className="min-w-0 flex-1">
                      <span className="block font-semibold">{group.name}</span>
                      <span className="mt-1 block text-sm text-slate-500">
                        {group.files.length} archivo(s)
                      </span>
                    </span>

                    {isExpanded ? (
                      <ChevronDown size={20} className="text-slate-500" />
                    ) : (
                      <ChevronRight size={20} className="text-slate-500" />
                    )}
                  </button>

                  {isExpanded && (
                    <div className="border-t border-slate-100 p-3 sm:p-5">
                      {groupDocuments.length === 0 ? (
                        <div className="rounded-xl border border-dashed border-slate-200 px-4 py-8 text-center">
                          <Folder
                            size={28}
                            className="mx-auto mb-2 text-slate-400"
                          />
                          <p className="font-medium text-slate-600">
                            {group.files.length === 0
                              ? "Todavía no hay archivos en esta materia."
                              : "No hay documentos que coincidan con la búsqueda."}
                          </p>
                          <p className="mt-1 text-sm text-slate-400">
                            Los documentos aparecerán aquí cuando estén disponibles.
                          </p>
                        </div>
                      ) : (
                        <DocumentView
                          documents={groupDocuments}
                          view={view}
                          selectedFiles={selectedFiles}
                          onToggleFile={toggleFile}
                        />
                      )}
                    </div>
                  )}
                </section>
              );
            })}

            {visibleGroups.length === 0 && (
              <EmptyState message="No se encontraron materias con esos criterios." />
            )}
          </div>
        ) : (
          <div className="space-y-4">
            {visibleDocuments.length === 0 ? (
              <EmptyState message="No se encontraron documentos con esos criterios." />
            ) : (
              <section className="rounded-2xl border border-slate-200 bg-white p-3 shadow-sm sm:p-5">
                <h3 className="mb-4 font-semibold">Disponible</h3>
                <DocumentView
                  documents={visibleDocuments}
                  view={view}
                  selectedFiles={selectedFiles}
                  onToggleFile={toggleFile}
                  showSubject
                />
              </section>
            )}
          </div>
        )}

        <p className="mt-6 text-center text-xs leading-5 text-slate-400">
          Datos de demostración. Los estados, fechas y previsualizaciones reales
          dependerán de la integración con los documentos del sistema.
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

function DocumentView({
  documents,
  view,
  selectedFiles,
  onToggleFile,
  showSubject = false,
}: {
  documents: DocumentItem[];
  view: ViewMode;
  selectedFiles: string[];
  onToggleFile: (id: string) => void;
  showSubject?: boolean;
}) {
  if (view === "lista") {
    return (
      <div className="overflow-x-auto">
        <table className="w-full min-w-[600px] text-left text-sm">
          <thead>
            <tr className="border-b border-slate-200 text-slate-500">
              <th className="w-12 px-3 py-3">
                <span className="sr-only">Seleccionar</span>
              </th>
              <th className="px-3 py-3 font-medium">Documento</th>
              {showSubject && (
                <th className="px-3 py-3 font-medium">Materia</th>
              )}
              <th className="px-3 py-3 font-medium">Estado</th>
              <th className="px-3 py-3 font-medium">Fecha</th>
              <th className="w-12 px-3 py-3">
                <span className="sr-only">Acciones</span>
              </th>
            </tr>
          </thead>
          <tbody>
            {documents.map((document) => (
              <tr
                key={document.id}
                className="border-b border-slate-100 last:border-0 hover:bg-slate-50"
              >
                <td className="px-3 py-4">
                  <input
                    type="checkbox"
                    checked={selectedFiles.includes(document.id)}
                    onChange={() => onToggleFile(document.id)}
                    aria-label={`Seleccionar ${document.name}`}
                    className="h-4 w-4 rounded border-slate-300 accent-green-600"
                  />
                </td>
                <td className="px-3 py-4">
                  <div className="flex items-center gap-3">
                    <FileText
                      size={21}
                      className="shrink-0 text-red-500"
                    />
                    <span className="font-medium text-slate-700">
                      {document.name}
                    </span>
                  </div>
                </td>
                {showSubject && (
                  <td className="px-3 py-4">{document.groupName}</td>
                )}
                <td className="px-3 py-4">
                  <StatusLabel status={document.status} />
                </td>
                <td className="px-3 py-4 text-slate-500">{document.date}</td>
                <td className="px-3 py-4 text-slate-400">
                  <MoreHorizontal size={19} />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
      {documents.map((document) => (
        <article
          key={document.id}
          className="relative rounded-xl border border-slate-200 bg-white p-4 transition hover:border-green-300 hover:shadow-md"
        >
          <label className="absolute right-3 top-3 z-10 cursor-pointer rounded-md bg-white p-1 shadow-sm">
            <input
              type="checkbox"
              checked={selectedFiles.includes(document.id)}
              onChange={() => onToggleFile(document.id)}
              aria-label={`Seleccionar ${document.name}`}
              className="h-4 w-4 accent-green-600"
            />
          </label>

          {view === "iconos" ? (
            <div className="flex min-h-44 flex-col items-center justify-center rounded-lg bg-slate-50 px-3 py-5 text-center">
              <FileText size={48} className="mb-3 text-red-500" />
              <p className="w-full break-words text-sm font-semibold text-slate-700">
                {document.name}
              </p>
              <div className="mt-3">
                <StatusLabel status={document.status} />
              </div>
            </div>
          ) : (
            <>
              <div
                className="mb-4 flex aspect-[4/3] flex-col items-center justify-center overflow-hidden rounded-lg border border-slate-200 bg-slate-50 p-4"
                aria-label="Previsualización ilustrativa del documento"
              >
                <div className="flex h-full w-full max-w-40 flex-col gap-2 rounded-md border border-slate-200 bg-white p-3 shadow-sm">
                  <div className="flex items-center gap-2 border-b border-slate-100 pb-2">
                    <FileText size={18} className="shrink-0 text-red-500" />
                    <span className="truncate text-[10px] font-semibold text-slate-600">
                      Documento PDF
                    </span>
                  </div>
                  <div className="h-1.5 w-4/5 rounded bg-slate-200" />
                  <div className="h-1.5 w-full rounded bg-slate-100" />
                  <div className="h-1.5 w-5/6 rounded bg-slate-100" />
                  <div className="h-8 w-full rounded bg-slate-50" />
                  <div className="h-1.5 w-3/4 rounded bg-slate-100" />
                </div>
                <span className="mt-2 inline-flex items-center gap-1 text-xs text-slate-400">
                  <Eye size={13} />
                  Vista ilustrativa
                </span>
              </div>

              <p className="break-words font-semibold text-slate-700">
                {document.name}
              </p>
              <p className="mt-1 text-xs text-slate-500">
                {document.groupName}
              </p>
              <div className="mt-3 flex items-center justify-between gap-2">
                <StatusLabel status={document.status} />
                <span className="text-xs text-slate-400">{document.date}</span>
              </div>
            </>
          )}

          {view === "iconos" && (
            <p className="mt-3 text-center text-xs text-slate-500">
              {document.groupName}
            </p>
          )}
        </article>
      ))}
    </div>
  );
}

function StatusLabel({ status }: { status: string }) {
  return (
    <span className="inline-flex items-center rounded-full bg-green-50 px-2.5 py-1 text-xs font-medium text-green-700">
      {status}
    </span>
  );
}

function EmptyState({ message }: { message: string }) {
  return (
    <div className="rounded-2xl border border-dashed border-slate-300 bg-white px-4 py-12 text-center">
      <Folder size={32} className="mx-auto mb-3 text-slate-400" />
      <p className="font-medium text-slate-600">{message}</p>
      <p className="mt-1 text-sm text-slate-400">
        Probá cambiar los filtros o el término de búsqueda.
      </p>
    </div>
  );
}
