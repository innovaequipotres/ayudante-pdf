"use client";

import { useState } from "react";
import { Check, Info, Pencil, X } from "lucide-react";
import type { Barrier } from "@/types";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";

const MAX_SUGGESTION_LENGTH = 500;

export interface SuggestionCardProps {
  barrier: Barrier;
  onApply: (barrier: Barrier, acceptedSuggestion: string) => void;
  onDismiss: (barrier: Barrier) => void;
}

export function SuggestionCard({
  barrier,
  onApply,
  onDismiss,
}: SuggestionCardProps) {
  const [isEditing, setIsEditing] = useState(false);
  const [editedSuggestion, setEditedSuggestion] = useState(barrier.suggestion);

  function startEditing() {
    setEditedSuggestion(barrier.suggestion);
    setIsEditing(true);
  }

  function cancelEditing() {
    setEditedSuggestion(barrier.suggestion);
    setIsEditing(false);
  }

  function applySuggestion() {
    const acceptedSuggestion = editedSuggestion.trim();

    if (!acceptedSuggestion) {
      return;
    }

    onApply(barrier, acceptedSuggestion);
    setIsEditing(false);
  }

  const isApplied = barrier.status === "Aplicada";

  return (
    <article className="space-y-4 rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
      <header className="flex flex-wrap items-start justify-between gap-3">
        <h3 className="text-sm font-semibold text-slate-900">{barrier.type}</h3>
        <Badge
          variant={
            isApplied ? "Aplicada" : isEditing ? "En edición" : barrier.severity
          }
        />
      </header>

      <section aria-label="Fragmento detectado">
        <h4 className="mb-1 text-xs font-semibold text-slate-600">
          Fragmento detectado
        </h4>
        <p className="whitespace-pre-wrap wrap-break-word rounded-md border border-red-100 bg-red-50 p-3 text-sm leading-5 text-red-900">
          {barrier.detectedFragment}
        </p>
      </section>

      {isApplied ? (
        <section aria-label="Cambio aplicado">
          <h4 className="mb-1 text-xs font-semibold text-emerald-800">
            Cambio aplicado
          </h4>
          <div className="rounded-md border border-emerald-200 bg-emerald-50 p-3">
            <p className="whitespace-pre-wrap wrap-break-word text-sm leading-5 text-emerald-950">
              {barrier.suggestion}
            </p>
          </div>
        </section>
      ) : isEditing ? (
        <section aria-label="Modificar sugerencia" className="space-y-2">
          <label
            htmlFor={`suggestion-${barrier.id}`}
            className="block text-sm font-medium text-slate-700"
          >
            Modificar sugerencia
          </label>
          <textarea
            id={`suggestion-${barrier.id}`}
            value={editedSuggestion}
            onChange={(event) => setEditedSuggestion(event.target.value)}
            maxLength={MAX_SUGGESTION_LENGTH}
            rows={4}
            className="w-full resize-y rounded-md border border-slate-300 bg-white p-3 text-sm leading-5 text-slate-900 outline-none focus-visible:border-blue-500 focus-visible:ring-2 focus-visible:ring-blue-100"
          />
          <p className="text-right text-xs text-slate-500" aria-live="polite">
            {editedSuggestion.length}/{MAX_SUGGESTION_LENGTH}
          </p>
          <div className="flex items-start gap-2 rounded-md border border-blue-200 bg-blue-50 p-3 text-sm text-blue-800">
            <Info aria-hidden="true" className="mt-0.5 size-4 shrink-0" />
            <p>Tu sugerencia reemplazará la propuesta de la IA.</p>
          </div>
        </section>
      ) : (
        <section aria-label="Sugerencia">
          <h4 className="mb-1 text-xs font-semibold text-slate-600">
            Sugerencia
          </h4>
          <p className="whitespace-pre-wrap wrap-break-word rounded-md border border-blue-100 bg-blue-50 p-3 text-sm leading-5 text-blue-900">
            {barrier.suggestion}
          </p>
        </section>
      )}

      <footer className="flex flex-wrap justify-end gap-2">
        {!isApplied && !isEditing ? (
          <>
            <Button
              variant="outline"
              className="px-3 py-1.5 text-xs"
              onClick={startEditing}
            >
              <Pencil aria-hidden="true" className="size-3.5" />
              Editar
            </Button>
            <Button
              variant="ghost"
              className="px-3 py-1.5 text-xs text-red-700 hover:bg-red-50"
              onClick={() => onDismiss(barrier)}
            >
              <X aria-hidden="true" className="size-3.5" />
              Descartar
            </Button>
            <Button
              variant="primary"
              className="px-3 py-1.5 text-xs"
              onClick={applySuggestion}
            >
              <Check aria-hidden="true" className="size-3.5" />
              Aplicar cambio
            </Button>
          </>
        ) : !isApplied && isEditing ? (
          <>
            <Button
              variant="outline"
              className="px-3 py-1.5 text-xs"
              onClick={cancelEditing}
            >
              Cancelar
            </Button>
            <Button
              variant="primary"
              className="px-3 py-1.5 text-xs"
              onClick={applySuggestion}
              disabled={!editedSuggestion.trim()}
            >
              <Check aria-hidden="true" className="size-3.5" />
              Aplicar cambio
            </Button>
          </>
        ) : null}
      </footer>
    </article>
  );
}
