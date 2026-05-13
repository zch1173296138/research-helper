## 1. Backend Parser Simplification

- [x] 1.1 Remove PyMuPDF imports, dependency declarations, and fallback Markdown generation.
- [x] 1.2 Make `MinerUClient.process()` fail clearly when no configured MinerU path produces Markdown.
- [x] 1.3 Remove the `disabled` MinerU mode from settings and documentation.

## 2. Backend PDF Preview Scope

- [x] 2.1 Keep the inline original PDF endpoint.
- [x] 2.2 Keep PyMuPDF-backed PDF page info and PNG page rendering endpoints for preview only.

## 3. Frontend Rendered Preview

- [x] 3.1 Keep API client methods and types for PDF page info and rendered page images.
- [x] 3.2 Use backend-rendered PNG pages in the paper preview instead of embedding the original PDF.
- [x] 3.3 Keep citation page clicks wired to page navigation controls.

## 4. Documentation And Existing OpenSpec Notes

- [x] 4.1 Update README and progress notes to describe MinerU-only parsing.
- [x] 4.2 Update active OpenSpec design references that still mention the PyMuPDF fallback.

## 5. Verification

- [x] 5.1 Run backend tests covering ingestion and affected services.
- [x] 5.2 Run the frontend build.
