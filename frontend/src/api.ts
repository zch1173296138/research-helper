export const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

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
};

export type Citation = {
  paper_id: string;
  filename: string;
  chunk_id?: string | null;
  section_title: string;
  quote: string;
  page_start?: number | null;
  page_end?: number | null;
};

export type PaperPdfInfo = {
  paper_id: string;
  page_count: number;
};

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, init);
  if (!response.ok) {
    const detail = await response.text();
    throw new Error(readableError(detail, response.statusText));
  }
  return response.json() as Promise<T>;
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
  paperPdfUrl: (paperId: string) => `${API_BASE}/api/papers/${encodeURIComponent(paperId)}/pdf`,
  paperPdfInfo: (paperId: string) => request<PaperPdfInfo>(`/api/papers/${paperId}/pdf-info`),
  paperPageImageUrl: (paperId: string, pageNumber: number, scale: number) =>
    `${API_BASE}/api/papers/${encodeURIComponent(paperId)}/pages/${pageNumber}.png?scale=${scale.toFixed(2)}`,
  paperContent: (paperId: string) => request<{ paper_id: string; content: string }>(`/api/papers/${paperId}/content`),
  summarize: (paperId: string) =>
    request<{ paper_id: string; summary: Record<string, unknown> }>(`/api/papers/${paperId}/summarize`, {
      method: "POST",
    }),
  chat: (payload: { library_id: string; question: string; paper_ids?: string[]; top_k?: number }) =>
    request<{ answer: string; citations: Citation[]; missing_evidence: boolean }>("/api/chat", {
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
    const response = await fetch(`${API_BASE}/api/export/markdown`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    if (!response.ok) throw new Error(readableError(await response.text(), response.statusText));
    return response.text();
  },
};
