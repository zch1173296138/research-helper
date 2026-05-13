## 1. Evidence Pipeline Foundation

- [ ] 1.1 Add `EvidenceDecision` and `EvidenceRagResult` data structures for candidate ids, accepted ids, rejected ids, summaries, and judge metadata.
- [ ] 1.2 Add an `EvidenceRagService` wrapper that calls `HybridRetriever` with a larger candidate pool while preserving current retriever behavior.
- [ ] 1.3 Add deterministic fallback evidence selection that accepts ranked non-reference chunks when the LLM judge is unavailable.
- [ ] 1.4 Store candidate ids, accepted ids, rejected ids, final context ids, and judge source in answer retrieval metadata.

## 2. LLM Evidence Judging And Synthesis

- [ ] 2.1 Add `LLMService.judge_evidence` with structured JSON parsing and validation for `accept`, `maybe`, and `reject` decisions.
- [ ] 2.2 Add bounded prompt construction for evidence judging so chunk snippets and stored metadata cannot grow without limit.
- [ ] 2.3 Add an answer synthesis method that receives accepted evidence summaries plus compact source snippets.
- [ ] 2.4 Enforce citation validation against accepted evidence ids only, including fallback behavior when the model cites an unaccepted id.

## 3. Paper Chat Integration

- [ ] 3.1 Route `PaperChatService.ask` through `EvidenceRagService` after the existing memory-aware query rewrite.
- [ ] 3.2 Preserve current paper-chat memory metadata while adding evidence-stage metadata to assistant messages.
- [ ] 3.3 Keep no-LLM mode working with ranked fallback evidence and extractive answers.
- [ ] 3.4 Add tests for paper-chat direct evidence acceptance, irrelevant evidence rejection, missing evidence, and invalid citation handling.

## 4. Library Chat And Matrix Reuse

- [ ] 4.1 Route library-level `/api/chat` answers through the evidence pipeline without breaking existing response schemas.
- [ ] 4.2 Reuse accepted evidence summaries when generating review matrix fields where possible.
- [ ] 4.3 Add tests that verify library-level answers expose candidate and accepted evidence metadata.
- [ ] 4.4 Add regression tests proving reference-section chunks remain excluded from evidence candidates.

## 5. Metadata Enrichment

- [ ] 5.1 Add a `PaperEnrichmentService` boundary that can run independently from PDF upload.
- [ ] 5.2 Add storage for normalized title, authors, venue, year, DOI or external identifiers, provider, confidence, and enrichment status.
- [ ] 5.3 Implement a no-key fallback that marks enrichment as skipped or unavailable without failing ingestion.
- [ ] 5.4 Add tests for successful metadata enrichment, unavailable provider behavior, and rebuilding enrichment for an existing paper.

## 6. Figure And Table Enrichment

- [ ] 6.1 Extend asset records or add related enrichment records for asset type, caption, page metadata, source, and generated-description provenance.
- [ ] 6.2 Parse available captions from Markdown or parser outputs and associate them with image/table assets where possible.
- [ ] 6.3 Add optional generated descriptions for figures/tables while marking them as non-original text.
- [ ] 6.4 Ensure retrieval metadata identifies generated asset enrichment and links it back to original caption, page, or asset evidence.

## 7. Frontend And UX

- [ ] 7.1 Update frontend API types for evidence-stage metadata and enrichment metadata.
- [ ] 7.2 Add a compact evidence inspection view showing accepted evidence first and low-confidence or rejected evidence behind a debug affordance.
- [ ] 7.3 Show enriched figure/table references without presenting generated descriptions as original paper text.

## 8. Verification And Documentation

- [ ] 8.1 Add focused unit tests for evidence judging fallback, JSON parsing failure, and metadata size caps.
- [ ] 8.2 Add integration tests covering paper upload, paper chat, library chat, and enriched evidence metadata.
- [ ] 8.3 Run backend tests with `python -m pytest`.
- [ ] 8.4 Run frontend build with `npm.cmd run build`.
- [ ] 8.5 Update `PROJECT_PROGRESS.md` and README notes with the PaperQA-style staged evidence workflow and remaining risks.
