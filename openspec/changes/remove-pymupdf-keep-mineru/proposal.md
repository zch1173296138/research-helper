## Why

Research Helper currently has two PDF parsing paths: MinerU for structured output and PyMuPDF as a fallback. Maintaining both paths adds code, dependency, and behavior surface while the desired product direction is to rely on MinerU only.

This change removes PyMuPDF from ingestion so document parsing is aligned around MinerU-produced Markdown and assets. PyMuPDF remains available only for server-side PDF page preview rendering.

## What Changes

- **BREAKING**: PDF ingestion no longer falls back to PyMuPDF when MinerU is unavailable or fails.
- MinerU API and local MinerU remain the only supported document parsing backends.
- Uploads fail with a clear error if the configured MinerU path cannot produce Markdown.
- The backend keeps PyMuPDF-backed PDF page metadata and PNG page rendering endpoints for preview only.
- The frontend PDF preview uses server-rendered page images to avoid browser PDF download behavior.
- Project dependencies and docs identify PyMuPDF as preview-only.

## Capabilities

### New Capabilities

- `mineru-only-pdf-processing`: PDF ingestion behavior when MinerU is the only parser and PyMuPDF is limited to preview rendering.

### Modified Capabilities

None.

## Impact

- Backend services: `MinerUClient`, paper upload flow, PDF-serving API endpoints.
- Frontend: PDF preview component and API client methods.
- Dependencies: keep `PyMuPDF` only for PDF preview rendering.
- Documentation and progress notes: update parser configuration and supported modes.
- Existing records with `parser = "pymupdf_fallback"` remain historical data, but new uploads cannot create that parser value.
