import type {
  SessionResponse,
  ExtractedContent,
  ContentBlock,
  Diagnosis,
  Observation,
  Category,
  Severity,
  Adaptation,
} from "./api";
import type { LumiDocument, Barrier, DiagnosticResult } from "@/types";

const CATEGORY_LABELS: Record<Category, string> = {
  comprehension: "Comprensión",
  structure: "Estructura",
  visual: "Visual",
  representation: "Representación",
  multimedia: "Multimedia",
  navigation: "Navegación",
};

const SEVERITY_MAP: Record<Severity, Barrier["severity"]> = {
  high: "Alta",
  medium: "Media",
  low: "Baja",
};

function formatBytes(bytes: number | null): string {
  if (bytes === null || bytes === undefined) return "—";
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function formatDate(isoString: string): string {
  const date = new Date(isoString);
  return date.toLocaleDateString("es-AR", {
    day: "numeric",
    month: "long",
    year: "numeric",
  });
}

function blocksToHtml(
  blocks: ContentBlock[],
  pages: { page: number; width: number; height: number }[],
): string {
  const pageMap = new Map(pages.map((p) => [p.page, p]));

  return blocks
    .map((block) => {
      const page = block.page ? pageMap.get(block.page) : null;

      switch (block.type) {
        case "heading": {
          const level = block.level ?? 1;
          return `<h${level}>${escapeHtml(block.text ?? "")}</h${level}>`;
        }
        case "paragraph":
          return `<p>${escapeHtml(block.text ?? "")}</p>`;
        case "list":
          if (!block.items?.length) return "";
          return (
            "<ul>" +
            block.items.map((item) => `<li>${escapeHtml(item)}</li>`).join("") +
            "</ul>"
          );
        case "image":
          if (block.width && block.height && page) {
            const aspectRatio = block.height / block.width;
            const maxWidth = Math.min(block.width, page.width * 0.9);
            const height = maxWidth * aspectRatio;
            return (
              `<figure>` +
              `<img src="/placeholder-image.png" alt="${escapeHtml(block.alt_text ?? "Imagen")}" width="${maxWidth}" height="${height}" />` +
              (block.alt_text
                ? `<figcaption>${escapeHtml(block.alt_text)}</figcaption>`
                : "") +
              `</figure>`
            );
          }
          return `<figure><img src="/placeholder-image.png" alt="${escapeHtml(block.alt_text ?? "Imagen")}" /><figcaption>${escapeHtml(block.alt_text ?? "Imagen")}</figcaption></figure>`;
        default:
          return "";
      }
    })
    .join("\n");
}

function escapeHtml(text: string): string {
  return text
    .replace(/&/g, "&")
    .replace(/</g, "<")
    .replace(/>/g, ">")
    .replace(/"/g, '"')
    .replace(/'/g, "&#039;");
}

function mapObservationToBarrier(
  obs: Observation,
  blocks: ContentBlock[],
): Barrier {
  const block = obs.block_id ? blocks.find((b) => b.id === obs.block_id) : null;

  return {
    id: obs.id,
    type: CATEGORY_LABELS[obs.category] ?? obs.category,
    severity: SEVERITY_MAP[obs.severity],
    detectedFragment: obs.excerpt ?? block?.text ?? obs.title,
    originalText: block?.text ?? obs.excerpt ?? obs.title,
    suggestion: "",
    status: "Pendiente",
    title: obs.title,
    detail: obs.detail,
    whyItMatters: obs.why_it_matters,
    recommendation: obs.recommendation,
    ruleId: obs.rule_id,
    category: obs.category,
    blockId: obs.block_id,
  };
}

export function mapSessionToDocument(
  session: SessionResponse,
  extracted?: ExtractedContent,
): LumiDocument {
  const subject =
    session.filename
      ?.replace(/\.pdf$/i, "")
      ?.split(/[_-]/)
      .map((w) => w.charAt(0).toUpperCase() + w.slice(1).toLowerCase())
      .join(" ") ?? "Sin asunto";

  const originalContent = extracted
    ? blocksToHtml(extracted.blocks, extracted.pages)
    : "";

  return {
    id: session.session_id,
    name: session.filename ?? "Documento sin nombre",
    subject,
    size: formatBytes(session.size_bytes),
    date: formatDate(session.created_at),
    status: mapSessionStatus(session.status),
    folderId: null,
    originalContent,
    modifiedContent: originalContent,
  };
}

function mapSessionStatus(
  status: SessionResponse["status"],
): LumiDocument["status"] {
  switch (status) {
    case "uploaded":
    case "extracted":
      return "Procesando";
    case "analyzed":
    case "completed":
      return "Analizado";
    default:
      return "Procesando";
  }
}

export function mapDiagnosisToResult(
  diagnosis: Diagnosis,
  extracted: ExtractedContent,
): DiagnosticResult {
  const barriers = diagnosis.observations.map((obs) =>
    mapObservationToBarrier(obs, extracted.blocks),
  );

  return {
    documentId: diagnosis.session_id,
    globalScore: diagnosis.score,
    readabilityPercentage: calculateReadability(diagnosis),
    barriers,
  };
}

function calculateReadability(diagnosis: Diagnosis): number {
  const totalPenalty = diagnosis.categories.reduce((sum, cat) => {
    return (
      sum +
      cat.barrier_count * 10 +
      cat.review_count * 4 +
      cat.suggestion_count * 1
    );
  }, 0);
  return Math.max(0, Math.min(100, 100 - totalPenalty));
}

export function mapAdaptationToSuggestion(adaptation: Adaptation): {
  adaptedText: string | null;
  notes: string | null;
} {
  return {
    adaptedText: adaptation.adapted_text,
    notes: adaptation.notes,
  };
}

export function createExportEditsFromBarriers(
  barriers: Barrier[],
  adaptedTexts: Map<string, string>,
): { block_id: string; text: string }[] {
  return barriers
    .filter((b) => b.status === "Aplicada" && adaptedTexts.has(b.id))
    .map((b) => ({
      block_id: b.id,
      text: adaptedTexts.get(b.id)!,
    }));
}
