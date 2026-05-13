## ADDED Requirements

### Requirement: MinerU-only ingestion
The system SHALL parse newly uploaded PDFs only through configured MinerU API or local MinerU processing.

#### Scenario: MinerU API succeeds
- **WHEN** a PDF is uploaded and MinerU API processing returns a Markdown result
- **THEN** the paper is marked processed with parser `mineru_api`
- **AND** the resulting Markdown is cleaned, chunked, and indexed through the existing ingestion flow

#### Scenario: Local MinerU succeeds
- **WHEN** a PDF is uploaded and local MinerU processing returns a Markdown result
- **THEN** the paper is marked processed with parser `mineru_local`
- **AND** the resulting Markdown is cleaned, chunked, and indexed through the existing ingestion flow

### Requirement: No PyMuPDF fallback
The system MUST NOT use PyMuPDF to extract text or generate Markdown fallback content.

#### Scenario: MinerU is unavailable
- **WHEN** a PDF is uploaded without a configured MinerU API token or enabled local MinerU path
- **THEN** the paper is marked failed with an error explaining that MinerU must be configured
- **AND** no `pymupdf_fallback` Markdown is generated

#### Scenario: MinerU processing fails
- **WHEN** all configured MinerU processing attempts fail or produce no Markdown
- **THEN** the paper is marked failed with the MinerU failure detail
- **AND** no PyMuPDF parser path is attempted

### Requirement: Rendered PDF preview
The system SHALL preview PDFs with backend-rendered page images while keeping the original PDF endpoint available for direct access.

#### Scenario: User opens paper detail
- **WHEN** a user views a paper detail page
- **THEN** the frontend requests PDF page metadata and PNG page images from the backend
- **AND** it does not embed the original PDF in an iframe

#### Scenario: Original PDF is missing
- **WHEN** the original PDF file is unavailable
- **THEN** the PDF preview endpoints return a not-found response
- **AND** the frontend presents the preview as unavailable
