export const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";
const API_BASE_CANDIDATES = Array.from(
  new Set([
    API_BASE,
    "http://localhost:8000",
    "http://127.0.0.1:8000",
    "http://localhost:8765",
    "http://127.0.0.1:8765",
    "http://localhost:8001",
    "http://127.0.0.1:8001",
  ]),
);
let activeApiBase = API_BASE;

export type Library = {
  id: string;
  name: string;
  description: string;
  paper_count: number;
};

export type Paper = {
  id: string;
  library_id: string;
  original_filename: string;
  status: string;
  parser: string;
  error?: string | null;
  needs_ocr: boolean;
  md_path?: string | null;
  normalized_title?: string | null;
  normalized_authors?: unknown[];
  normalized_venue?: string | null;
  normalized_year?: number | null;
  doi?: string | null;
  external_ids?: Record<string, unknown>;
  source_url?: string | null;
  enrichment_status: string;
  enrichment_metadata: Record<string, unknown>;
};

export type Citation = {
  citation_id?: string | null;
  paper_id: string;
  filename: string;
  chunk_id?: string | null;
  asset_id?: number | null;
  asset_type?: string | null;
  provenance?: string | null;
  section_title: string;
  section_path: string;
  section_type: string;
  quote: string;
  page_start?: number | null;
  page_end?: number | null;
};

export type EvidenceDecision = {
  chunk_id: string;
  decision: "accept" | "maybe" | "reject" | string;
  reason?: string;
  support_level?: string;
  answerable_claims?: string[];
  concise_summary?: string;
  judge_source?: string;
};

export type EvidenceMetadata = {
  evidence_pipeline?: string;
  candidate_chunk_ids?: string[];
  accepted_chunk_ids?: string[];
  rejected_chunk_ids?: string[];
  final_context_chunk_ids?: string[];
  judge_source?: string;
  evidence_decisions?: EvidenceDecision[];
};

export type ChatSession = {
  id: string;
  library_id: string;
  paper_id?: string | null;
  title: string;
  memory_summary: string;
  compressed_until_message_id?: number | null;
  memory_updated_at?: string | null;
  context_mode: string;
};

export type ChatMessage = {
  id: number;
  session_id: string;
  role: "user" | "assistant" | string;
  content: string;
  citations: Citation[];
  retrieval_metadata: Record<string, unknown>;
  created_at: string;
};

export type PaperPdfInfo = {
  paper_id: string;
  page_count: number;
};

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const tried: string[] = [];
  let lastError: Error | null = null;

  for (const base of orderedApiBases()) {
    tried.push(base);
    try {
      const response = await fetch(`${base}${path}`, init);
      if (response.ok) {
        activeApiBase = base;
        return response.json() as Promise<T>;
      }
      const detail = await response.text();
      lastError = new Error(readableError(detail, response.statusText));
      if (response.status !== 404) {
        break;
      }
    } catch (error) {
      lastError = error instanceof Error ? error : new Error(String(error));
    }
  }
  throw new Error(`${lastError?.message ?? "Request failed"} (tried: ${tried.join(", ")})`);
}

function orderedApiBases(): string[] {
  return [activeApiBase, ...API_BASE_CANDIDATES.filter((base) => base !== activeApiBase)];
}

function readableError(detail: string, fallback: string): string {
  if (!detail) return fallback;
  try {
    const parsed = JSON.parse(detail) as { detail?: unknown };
    if (typeof parsed.detail === "string") return parsed.detail;
    if (parsed.detail) return JSON.stringify(parsed.detail);
  } catch {
    // FastAPI may also return plain text.
  }
  return detail;
}

export const api = {
  libraries: () => request<Library[]>("/api/libraries"),
  createLibrary: (payload: { name: string; description?: string }) =>
    request<Library>("/api/libraries", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    }),
  papers: (libraryId: string) => request<Paper[]>(`/api/libraries/${libraryId}/papers`),
  upload: (libraryId: string, formData: FormData) =>
    request<Paper[]>(`/api/libraries/${libraryId}/papers/upload`, {
      method: "POST",
      body: formData,
    }),
  deletePaper: (paperId: string) =>
    request<{ success: boolean; paper_id: string }>(`/api/papers/${encodeURIComponent(paperId)}`, {
      method: "DELETE",
    }),
  paperPdfInfo: (paperId: string) => request<PaperPdfInfo>(`/api/papers/${encodeURIComponent(paperId)}/pdf-info`),
  paperPageImageUrl: (paperId: string, pageNumber: number, scale: number) =>
    `${activeApiBase}/api/papers/${encodeURIComponent(paperId)}/pages/${pageNumber}.png?scale=${scale.toFixed(2)}`,
  paperContent: (paperId: string) => request<{ paper_id: string; content: string }>(`/api/papers/${paperId}/content`),
  summarize: (paperId: string) =>
    request<{ paper_id: string; summary: Record<string, unknown> }>(`/api/papers/${paperId}/summarize`, {
      method: "POST",
    }),
  enrichPaper: (paperId: string) =>
    request<Paper>(`/api/papers/${encodeURIComponent(paperId)}/enrich`, {
      method: "POST",
    }),
  chat: (payload: { library_id: string; question: string; paper_ids?: string[]; top_k?: number }) =>
    request<{ answer: string; citations: Citation[]; missing_evidence: boolean; retrieval_metadata: Record<string, unknown> }>("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    }),
  paperChatSession: (paperId: string) =>
    request<ChatSession>(`/api/papers/${encodeURIComponent(paperId)}/chat/session`),
  paperChatMessages: (sessionId: string, params?: { limit?: number; before_id?: number }) => {
    const search = new URLSearchParams();
    if (params?.limit) search.set("limit", String(params.limit));
    if (params?.before_id) search.set("before_id", String(params.before_id));
    const suffix = search.toString() ? `?${search.toString()}` : "";
    return request<ChatMessage[]>(`/api/chat/sessions/${encodeURIComponent(sessionId)}/messages${suffix}`);
  },
  sendPaperChatMessage: (sessionId: string, payload: { question: string; top_k?: number; context_mode?: string }) =>
    request<{
      user_message: ChatMessage;
      assistant_message: ChatMessage;
      answer: string;
      citations: Citation[];
      missing_evidence: boolean;
      memory_summary: string;
      compressed_until_message_id?: number | null;
      memory_updated_at?: string | null;
      retrieval_metadata: Record<string, unknown>;
    }>(`/api/chat/sessions/${encodeURIComponent(sessionId)}/messages`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    }),
  matrix: (payload: { library_id: string; topic?: string; paper_ids?: string[] }) =>
    request<{ id: string; rows: Array<Record<string, unknown>> }>("/api/review/matrix", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    }),
  exportMarkdown: async (payload: { library_id: string; matrix_id?: string }) => {
    const response = await fetch(`${activeApiBase}/api/export/markdown`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    if (!response.ok) throw new Error(readableError(await response.text(), response.statusText));
    return response.text();
  },
};
