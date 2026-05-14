## Context

Research Helper already has a local RAG A/B harness that consumes JSONL evaluation cases with fields such as `id`, `category`, `question`, `should_answer`, `expected_points`, `supporting_quotes`, `supporting_chunk_ids`, `tags`, and `notes`. The current starter dataset is useful for smoke testing against locally imported B-rep papers, but it is too small and project-specific to carry much external benchmark credibility.

QASPER is a public research-paper question answering dataset with paper text, questions, answer annotations, evidence snippets, and unanswerable cases. It is available from Hugging Face as `allenai/qasper` with a `qasper` config and `validation` split. The target output should fit the existing evaluator rather than creating a new benchmark runner.

## Goals / Non-Goals

**Goals:**

- Produce a checked-in QASPER-derived validation JSONL file containing 20-50 cases.
- Keep the output compatible with `backend.app.evaluation.cases.load_cases`.
- Preserve enough provenance to trace each converted case back to QASPER.
- Include answerable and unanswerable cases when available in the selected validation sample.
- Prefer evidence annotations as `supporting_quotes` so metrics remain stable after local chunking.
- Document how the dataset was selected and how to regenerate it.

**Non-Goals:**

- Do not change production RAG behavior.
- Do not add a new evaluation runner.
- Do not require the full QASPER corpus to be committed.
- Do not require normal evaluation runs to call Hugging Face.
- Do not solve PDF acquisition for every QASPER paper in this change.
- Do not tune prompts, retrieval, evidence judging, or scoring logic based on QASPER results.

## Decisions

### 1. Store converted QASPER cases as static JSONL

Add a file such as `evals/rag_ab/qasper_validation_cases.jsonl` containing 20-50 converted validation examples.

Rationale: static JSONL keeps evaluation runs deterministic and avoids network dependency during normal A/B runs.

Alternative considered: fetch QASPER dynamically on every evaluation run. That is simpler operationally at first, but makes benchmark runs depend on Hugging Face availability and dataset version drift.

### 2. Keep generation under the evaluation boundary

If a converter is added, place it under `evals/rag_ab/` or `backend.app.evaluation` with no production imports beyond the existing case schema validation path.

Rationale: QASPER is benchmark data plumbing, not product behavior.

Alternative considered: add a general dataset ingestion feature to the application. That is larger than the request and risks mixing benchmark conversion with user-facing paper ingestion.

### 3. Use quote-based support first

Map QASPER answer evidence or highlighted evidence strings into `supporting_quotes`. Leave `supporting_chunk_ids` empty unless the QASPER paper has also been imported and chunked locally.

Rationale: local chunk ids are project-specific and will change across parsing/chunking revisions, while QASPER evidence text is stable enough to test retrieval grounding after import.

Alternative considered: precompute chunk ids during conversion. That would couple the dataset to a single storage snapshot and make it brittle.

### 4. Preserve provenance in `notes` and `tags`

Use stable case ids such as `qasper-val-0001`, include tags like `qasper`, `public-benchmark`, and category tags, and include source identifiers in `notes` or raw fields accepted by the loader.

Rationale: the existing `EvaluationCase` type preserves unknown raw fields during load, but reports only standardized case fields. Keeping concise provenance in `notes` makes reports readable while raw fields can retain exact source ids.

Alternative considered: extend the case dataclass with first-class provenance fields. That is useful later, but unnecessary for the first dataset because the loader already preserves raw payloads.

### 5. Select a balanced deterministic subset

Select 20-50 validation cases deterministically from QASPER using fixed ordering and filters:

- include answerable free-form or extractive cases with non-empty evidence;
- include some unanswerable cases;
- avoid examples where evidence is empty for answerable questions;
- prefer concise questions and evidence strings that fit the existing deterministic metrics;
- avoid cases that require figure/table image reasoning unless the current evaluator can use those assets.

Rationale: the first public dataset should exercise the current text RAG evaluator rather than fail because of unsupported modalities.

Alternative considered: random sample. Random selection is easy but weakens reproducibility and can overrepresent noisy cases.

## Risks / Trade-offs

- QASPER paper ids are not Research Helper `paper_ids` -> Leave `paper_ids` empty until corresponding papers are imported, and record QASPER paper ids in provenance.
- QASPER full text may not be present in the local Research Helper library -> Document that cases are valid schema examples and become end-to-end runnable after importing matching paper text/PDFs.
- Deterministic expected-point scoring can undercount semantically correct answers -> Prefer extractive spans and concise free-form answers for `expected_points`; optional LLM judge can be used separately.
- Evidence snippets may not exactly match MinerU output after PDF parsing -> Use QASPER text evidence as `supporting_quotes` and accept quote-based recall as best-effort.
- Public benchmark cases may not match the user's CAD/B-rep domain -> Treat QASPER as external credibility, not as a replacement for project-local golden cases.

## Migration Plan

- Add the converted JSONL dataset and documentation.
- Add or update validation tests to load the QASPER JSONL through the existing case loader.
- Run the case loader or targeted pytest to verify schema compatibility.
- Rollback is deleting the new QASPER files and tests; no database or API migration is required.

## Open Questions

- Should the first file contain exactly 20, 30, or 50 cases? The requested range is 20-50; implementation can choose a pragmatic default such as 30.
- Should raw QASPER full text be stored locally, or only case metadata and evidence quotes?
- Should a follow-up change add a helper to import QASPER paper full text into Research Helper storage for end-to-end RAG runs?
