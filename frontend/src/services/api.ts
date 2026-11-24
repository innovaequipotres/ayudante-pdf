const API_BASE =
  process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000/api/v1";
const USE_MOCKS = process.env.NEXT_PUBLIC_USE_MOCKS === "true";

export interface ErrorResponse {
  code: string;
  message: string;
}

export interface SessionResponse {
  session_id: string;
  source_type: "pdf" | "text";
  filename: string | null;
  size_bytes: number | null;
  status: "uploaded" | "extracted" | "analyzed" | "completed";
  created_at: string;
}

export interface TextInput {
  title: string | null;
  text: string;
}

export interface BBox {
  x0: number;
  top: number;
  x1: number;
  bottom: number;
}

export interface PageSize {
  page: number;
  width: number;
  height: number;
}

export interface ContentSummary {
  word_count: number;
  heading_count: number;
  paragraph_count: number;
  list_count: number;
  image_count: number;
  images_without_alt: number;
}

export type BlockType = "heading" | "paragraph" | "list" | "image";

export interface ContentBlock {
  id: string;
  type: BlockType;
  page: number | null;
  text: string | null;
  level: number | null;
  items: string[] | null;
  word_count: number;
  alt_text: string | null;
  width: number | null;
  height: number | null;
  bbox: BBox | null;
  font_size: number | null;
}

export interface ExtractedContent {
  session_id: string;
  source_type: "pdf" | "text";
  title: string | null;
  page_count: number | null;
  pages: PageSize[];
  summary: ContentSummary;
  blocks: ContentBlock[];
}

export type Severity = "high" | "medium" | "low";
export type ObservationSource = "rule" | "ai";
export type Category =
  | "comprehension"
  | "structure"
  | "visual"
  | "representation"
  | "multimedia"
  | "navigation";
export type DiagnosisLevel = "ok" | "review" | "barrier";
export type AiStatus = "ok" | "unavailable" | "skipped";

export interface Observation {
  id: string;
  rule_id: string;
  category: Category;
  severity: Severity;
  source: ObservationSource;
  title: string;
  detail: string | null;
  why_it_matters: string;
  recommendation: string;
  block_id: string | null;
  page: number | null;
  excerpt: string | null;
}

export interface CategoryResult {
  category: Category;
  severity: DiagnosisLevel;
  barrier_count: number;
  review_count: number;
  suggestion_count: number;
}

export interface Diagnosis {
  session_id: string;
  score: number;
  level: DiagnosisLevel;
  disclaimer: string;
  categories: CategoryResult[];
  observations: Observation[];
  created_at: string;
  ai_status: AiStatus;
  ai_notice: string | null;
  ai_truncated: boolean;
}

export type AdaptationType =
  "simplify" | "clarify" | "describe" | "alt_text" | "sequence";
export type AdaptationSource = "ai" | "local";

export interface AdaptationRequest {
  type: AdaptationType;
  original_text: string;
  rule_id?: string | null;
  category?: Category | null;
  title?: string | null;
  detail?: string | null;
  recommendation?: string | null;
  context_before?: string | null;
  context_after?: string | null;
}

export interface Adaptation {
  id: string;
  type: AdaptationType;
  rule_id: string | null;
  original_text: string;
  adapted_text: string | null;
  notes: string | null;
  source: AdaptationSource | null;
  ai_status: AiStatus;
  ai_notice: string | null;
  provider: string | null;
  created_at: string;
}

export interface ExportEdit {
  block_id: string;
  text: string;
}

export interface ExportRequest {
  edits: ExportEdit[];
}

class ApiError extends Error {
  constructor(
    public readonly code: string,
    public readonly status: number,
    message: string,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

async function fetchApi<T>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  const url = `${API_BASE}${path}`;

  const headers: HeadersInit = {
    ...(options.headers ?? {}),
  };

  if (!(options.body instanceof FormData)) {
    (headers as Record<string, string>)["Content-Type"] = "application/json";
  }

  const response = await fetch(url, {
    ...options,
    headers,
  });

  if (!response.ok) {
    let errorData: ErrorResponse;
    try {
      errorData = await response.json();
    } catch {
      errorData = {
        code: "UNKNOWN_ERROR",
        message: `HTTP ${response.status}: ${response.statusText}`,
      };
    }
    throw new ApiError(errorData.code, response.status, errorData.message);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  const contentType = response.headers.get("content-type");
  if (contentType?.includes("application/json")) {
    return response.json();
  }

  return response.blob() as Promise<T>;
}

export const api = {
  createSessionFromFile: (file: File): Promise<SessionResponse> => {
    const formData = new FormData();
    formData.append("file", file);
    return fetchApi<SessionResponse>("/sessions/file", {
      method: "POST",
      body: formData,
    });
  },

  createSessionFromText: (input: TextInput): Promise<SessionResponse> => {
    return fetchApi<SessionResponse>("/sessions/text", {
      method: "POST",
      body: JSON.stringify(input),
    });
  },

  getSession: (sessionId: string): Promise<SessionResponse> => {
    return fetchApi<SessionResponse>(`/sessions/${sessionId}`);
  },

  extractContent: (sessionId: string): Promise<ExtractedContent> => {
    return fetchApi<ExtractedContent>(`/sessions/${sessionId}/extract`, {
      method: "POST",
    });
  },

  getContent: (sessionId: string): Promise<ExtractedContent> => {
    return fetchApi<ExtractedContent>(`/sessions/${sessionId}/content`);
  },

  analyzeSession: (
    sessionId: string,
    useAi: boolean = true,
  ): Promise<Diagnosis> => {
    return fetchApi<Diagnosis>(
      `/sessions/${sessionId}/analyze?use_ai=${useAi}`,
      {
        method: "POST",
      },
    );
  },

  getDiagnosis: (sessionId: string): Promise<Diagnosis> => {
    return fetchApi<Diagnosis>(`/sessions/${sessionId}/diagnosis`);
  },

  exportPdf: (sessionId: string, edits: ExportEdit[]): Promise<Blob> => {
    return fetchApi<Blob>(`/sessions/${sessionId}/export`, {
      method: "POST",
      body: JSON.stringify({ edits }),
    });
  },

  adaptBarrier: (request: AdaptationRequest): Promise<Adaptation> => {
    return fetchApi<Adaptation>("/adaptations", {
      method: "POST",
      body: JSON.stringify(request),
    });
  },
};

export { ApiError, USE_MOCKS, API_BASE };
