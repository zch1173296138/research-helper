## Context

The current PDF pipeline writes an uploaded PDF to storage, asks `MinerUClient` to create `full.md`, chunks that Markdown, and indexes the chunks. `MinerUClient` currently tries MinerU API/local modes first and then generates a plain-text `full.md` with PyMuPDF when MinerU is unavailable or fails.

PyMuPDF is also used by the API layer to count pages and render per-page PNG previews for the frontend. That preview path must remain because embedding the original PDF can trigger browser download behavior in the user's environment.

## Goals / Non-Goals

**Goals:**

- Make MinerU the only PDF parser for new uploads.
- Keep the ingestion code small and explicit: configured MinerU path succeeds, or upload records a clear failure.
- Remove PyMuPDF from parsing and fallback Markdown generation.
- Keep PyMuPDF only as a preview renderer for page count and PNG page images.
- Preserve existing Markdown chunking, indexing, summary, and chat behavior after MinerU produces `full.md`.

**Non-Goals:**

- Do not add a replacement PDF renderer such as Poppler, pdf.js, or another Python package.
- Do not migrate historical database records that already have `parser = "pymupdf_fallback"`.
- Do not change vector retrieval, chat, summary, or matrix behavior except for parser metadata and upload failure paths.
- Do not implement background MinerU job orchestration in this change.

## Decisions

### 1. Fail ingestion instead of fallback parsing

`MinerUClient.process()` will only return `mineru_api` or `mineru_local`. If no usable MinerU mode is configured, or configured MinerU fails to produce Markdown, it will raise `MinerUError` with an actionable message.

Alternative considered: keep a tiny fallback that writes an empty Markdown file. That would let uploads appear processed but would weaken retrieval quality and hide configuration problems.

### 2. Keep `auto`, `api`, and `local` modes only

`mineru_mode = "disabled"` exists only to force PyMuPDF. The mode will be removed from settings validation and documentation. In `auto`, the client will try configured API/local paths in order and fail if neither is available.

Alternative considered: keep `disabled` as "do not parse". That adds a mode that cannot ingest papers and complicates UI/docs without helping the requested behavior.

### 3. Keep server-rendered page image preview

The backend will keep `/api/papers/{paper_id}/pdf` for direct access and restore `/pdf-info` plus `/pages/{page}.png` for preview. The frontend preview will request server-rendered page images and keep page navigation plus zoom controls.

Alternative considered: native PDF embedding. That is smaller, but in this environment it downloads the PDF instead of displaying it.

### 4. Leave historical parser values untouched

Existing rows with `pymupdf_fallback` will still display their stored parser string. New ingestion will never create that value. This avoids a migration for metadata that does not affect runtime behavior.

Alternative considered: rewrite historical parser values. That would be misleading because those papers were actually produced by the old fallback.

## Risks / Trade-offs

- MinerU unavailable blocks new uploads -> errors will explicitly say MinerU API token or local MinerU must be configured.
- Preview rendering depends on PyMuPDF remaining installed -> keep it scoped to API preview endpoints and out of MinerU ingestion.
- Server-rendered preview costs CPU per page -> keep scale bounded and cache responses for a short browser lifetime.
- Existing tests may assume PyMuPDF fallback text -> update tests to cover MinerU failure and success paths instead.

## Migration Plan

1. Remove PyMuPDF fallback generation from ingestion.
2. Keep PyMuPDF-backed preview API endpoints.
3. Update frontend API and preview component to use rendered PNG pages.
4. Update README, progress notes, and active OpenSpec design references.
5. Run focused backend tests and frontend build.

Rollback is straightforward: restore the removed ingestion fallback method if PyMuPDF parsing support is needed again. Preview endpoints remain in this change.

## Open Questions

None for this change. A future change can replace the PyMuPDF preview renderer if a different page-image renderer is preferred.
