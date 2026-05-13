## Why

Research Helper already parses papers, chunks Markdown, builds local indexes, and answers with citations, but the current RAG flow is still closer to direct retrieval plus answer generation. PaperQA's useful lesson is not its full package or storage stack; it is the staged evidence workflow: retrieve broadly, judge evidence against the question, summarize only useful evidence, then synthesize an answer that cites only accepted sources.

This change extracts those PaperQA-style ideas into the existing FastAPI, SQLite, LanceDB, MinerU, and frontend architecture so literature review answers become more grounded without replacing the current product.

## What Changes

- Add a staged evidence pipeline for library and paper chat questions:
  - broader candidate retrieval;
  - query-aware evidence screening;
  - concise evidence summaries;
  - final synthesis from accepted evidence only.
- Persist retrieval and evidence-evaluation metadata so each answer can explain which chunks were accepted, rejected, or unused.
- Add an optional metadata enrichment step inspired by PaperQA's external metadata workflow:
  - DOI/title lookup hooks;
  - normalized bibliographic metadata;
  - source links and identifiers when available.
- Add an optional figure/table enrichment path for assets extracted by MinerU or future Docling integration:
  - caption-aware asset records;
  - generated table/figure descriptions for retrieval;
  - clear separation between original paper text and generated enrichment text.
- Keep the first implementation local-first and dependency-light:
  - no wholesale PaperQA dependency;
  - no replacement of MinerU parsing;
  - no forced external metadata API keys.

## Capabilities

### New Capabilities

- `paperqa-style-evidence-rag`: Question answering pipeline that screens, summarizes, and cites evidence in stages before final answer synthesis.
- `paper-enrichment-metadata`: Optional enrichment of paper metadata, figures, tables, and generated asset descriptions while preserving provenance.

### Modified Capabilities

## Impact

- Backend services: retrieval orchestration, paper chat, library chat, LLM prompting, metadata storage, and asset indexing.
- Database: new tables or JSON fields for evidence decisions, enriched metadata, and asset descriptions.
- API schemas: answer responses expose evidence summary metadata and provenance/debug information.
- Frontend: answer views can show accepted evidence, rejected/low-confidence evidence, and enriched figure/table references.
- Tests: add unit and integration coverage for evidence screening, citation isolation, metadata enrichment fallbacks, and asset provenance.
