## 1. Evaluation Case Format

- [x] 1.1 Define a JSONL schema for RAG evaluation cases with required fields for id, category, question, should_answer, and optional library_id, paper_ids, expected_points, supporting_quotes, supporting_chunk_ids, tags, and notes.
- [x] 1.2 Add a loader and validator that reports line numbers and missing fields before any model or API calls run.
- [x] 1.3 Add a small starter dataset covering method, result, comparison, follow-up-style, identifier, and no-answer questions for the currently available sample papers.
- [x] 1.4 Document how to add new cases and how to choose supporting quotes or chunk ids.

## 2. Strategy Adapters

- [x] 2.1 Create a common strategy output shape for answer text, citations, retrieved chunk ids, candidate ids, final context ids, evidence decisions, missing_evidence, latency, errors, and raw metadata.
- [x] 2.2 Implement `baseline-current` in-process adapter using `HybridRetriever.search(top_k)` plus `LLMService.answer_with_citations` or the existing paper-chat answer method, bypassing `EvidenceRagService`.
- [x] 2.3 Implement `current-evidence` in-process adapter using `EvidenceRagService` and preserving evidence-stage metadata.
- [x] 2.4 Implement optional `old-code-api` adapter that calls an explicitly configured old-code backend URL and records health-check status.
- [x] 2.5 Add adapter-level tests proving the baseline adapter does not emit evidence decisions and the current adapter does.

## 3. Runner CLI

- [x] 3.1 Add an evaluation runner entry point that accepts case file path, output directory, baseline strategy, comparison strategy, current API URL or in-process mode, optional old-code API URL, top_k, and case filters.
- [x] 3.2 Require explicit API URLs when API mode is selected and fail fast if a configured service health check fails.
- [x] 3.3 Execute every selected case against both strategies and capture per-case raw outputs without aborting the full run on one case failure.
- [x] 3.4 Record reproducibility metadata including timestamp, git revision when available, strategy names, URLs or mode, top_k, case file hash, and environment notes.

## 4. Retrieval and Evidence Metrics

- [x] 4.1 Compute supporting evidence recall for candidate ids, final context ids, and citation ids when chunk ids are available.
- [x] 4.2 Compute quote-based support matching against returned chunks and citations when supporting quotes are provided.
- [x] 4.3 Detect reference contamination from citation metadata, section metadata, and reference-like section names.
- [x] 4.4 Compute accepted evidence precision and recall when evidence decisions are available, and mark these metrics as not applicable for baseline outputs.
- [x] 4.5 Capture latency and per-strategy error counts in aggregate metrics.

## 5. Answer and Citation Metrics

- [x] 5.1 Compute expected-point coverage using deterministic phrase or regex matching against each answer.
- [x] 5.2 Compute no-answer behavior for `should_answer=false` cases by checking missing_evidence flags and insufficient-evidence wording.
- [x] 5.3 Validate that returned citations refer to known chunks or accepted evidence when metadata is available.
- [x] 5.4 Add an optional LLM-as-judge extension point that records judge source separately and can be disabled for local deterministic runs.

## 6. Reports

- [x] 6.1 Write per-case raw result JSONL with inputs, both strategy outputs, metrics, timings, and errors.
- [x] 6.2 Write aggregate metrics JSON grouped by strategy and category.
- [x] 6.3 Generate a Markdown or HTML report summarizing A/B wins, metric deltas, failed cases, and representative evidence/citation examples.
- [x] 6.4 Include the exact run configuration and baseline mode in every report.

## 7. Validation

- [x] 7.1 Add unit tests for case validation, metric calculations, no-answer scoring, and report generation.
- [x] 7.2 Add integration tests with fake adapters to verify the runner handles success, partial failure, and not-applicable evidence metrics.
- [x] 7.3 Run backend tests with `python -m pytest`.
- [x] 7.4 Run a smoke evaluation against the starter dataset using `baseline-current` vs `current-evidence`.
- [x] 7.5 Update README or project progress notes with instructions for running RAG A/B evaluation.
