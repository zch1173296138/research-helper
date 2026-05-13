## ADDED Requirements

### Requirement: Optional Paper Metadata Enrichment
The system SHALL support optional enrichment of imported papers with normalized bibliographic metadata while keeping upload and parsing usable without external providers.

#### Scenario: Metadata provider succeeds
- **WHEN** enrichment finds a confident metadata match for a paper
- **THEN** the system stores normalized title, authors, venue, year, DOI or external identifiers, source URL, provider name, and confidence metadata

#### Scenario: Metadata provider unavailable
- **WHEN** no provider key is configured or a provider call fails
- **THEN** the system records enrichment status without failing paper ingestion or existing question answering

#### Scenario: Existing parser metadata remains
- **WHEN** enrichment adds normalized metadata
- **THEN** the original filename, parser, Markdown path, and existing paper record remain unchanged

### Requirement: Reference Metadata Provenance
The system SHALL preserve provenance for references or bibliographic records extracted from GROBID, external metadata APIs, or local parsing.

#### Scenario: References are extracted
- **WHEN** a provider returns a paper's reference list
- **THEN** each reference stores its provider/source and available identifiers separately from the main paper text chunks

#### Scenario: Duplicate reference metadata appears
- **WHEN** multiple providers return the same reference
- **THEN** the system merges identifiers where possible while preserving provider provenance

### Requirement: Asset Caption And Description Enrichment
The system SHALL support enrichment of figure and table assets with captions, page information, and optional generated descriptions.

#### Scenario: Caption is available
- **WHEN** MinerU, Docling, GROBID, or Markdown parsing identifies a figure or table caption
- **THEN** the system stores the caption with the associated asset path, page metadata when available, and extraction source

#### Scenario: Generated description is created
- **WHEN** an LLM or vision model creates a figure or table description
- **THEN** the system stores the description as generated enrichment with source metadata and does not mark it as original paper text

### Requirement: Enrichment Retrieval Provenance
The system SHALL make enriched metadata and asset descriptions retrievable without allowing generated enrichment to become the sole source for factual citations.

#### Scenario: Asset description helps retrieval
- **WHEN** a user asks about a figure or table and generated enrichment matches the query
- **THEN** the retrieval metadata identifies the generated enrichment source and links it to the parent paper asset or original caption

#### Scenario: Final answer cites evidence
- **WHEN** a final answer uses information found through generated enrichment
- **THEN** the citation points to original paper evidence, caption text, page metadata, or the associated asset record rather than treating generated text as original evidence

### Requirement: Enrichment Rebuildability
The system SHALL allow enrichment outputs to be rebuilt without re-uploading the original PDF.

#### Scenario: Rebuild requested
- **WHEN** a user or backend task reruns metadata or asset enrichment for a processed paper
- **THEN** the system updates enrichment records from existing PDF, Markdown, and asset files without creating duplicate paper records
