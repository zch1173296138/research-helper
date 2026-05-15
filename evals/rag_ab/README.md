# RAG A/B Evaluation

This directory contains local JSONL datasets for comparing the previous hybrid RAG path with the current PaperQA-style evidence RAG path.

## Datasets

- `starter_cases.jsonl`: small local smoke set for papers already imported in the development library.
- `qasper_validation_cases.jsonl`: 30 cases converted from the public Hugging Face dataset `allenai/qasper`, config `qasper`, split `validation`.
- `qasper_validation_local_subset.jsonl`: 12 high-quality QASPER cases mapped to the locally imported papers in the development library.
- `qasper_validation_local_subset_chunked.jsonl`: the same local subset with QASPER support quotes fuzzy-aligned to local `paper_chunks` so chunk-level recall metrics are available.

The QASPER file is checked in so normal evaluation runs do not need network access. It preserves source provenance fields such as `source_dataset`, `source_config`, `source_split`, `source_paper_id`, `source_question_id`, `source_annotation_ids`, and `source_title`.

QASPER cases leave `paper_ids` and `supporting_chunk_ids` empty because QASPER paper ids are public source identifiers, not Research Helper local paper ids. To run these cases end-to-end against local retrieval, first import the corresponding QASPER paper text or PDFs into a Research Helper library, then add local `library_id` or `paper_ids` if you want to constrain retrieval.

## Case Format

Each line is one JSON object:

```json
{
  "id": "brepmfr-method-001",
  "category": "method",
  "library_id": "library_cc251fc963174eb6",
  "paper_ids": ["paper_0a722d8e689b4f0d"],
  "question": "What is the core method of BrepMFR?",
  "should_answer": true,
  "expected_points": ["B-rep", "graph", "Transformer"],
  "supporting_quotes": ["The original B-rep model is converted into a graph representation"],
  "supporting_chunk_ids": [],
  "tags": ["method"],
  "notes": "Single-paper method question."
}
```

Required fields are `id`, `category`, `question`, and `should_answer`.

Use `supporting_quotes` when chunk ids may change after re-indexing. Use `supporting_chunk_ids` when you want exact recall metrics for a fixed database snapshot.

Deterministic metrics run by default. Add `--llm-judge` only when you want an optional model-graded pass recorded separately under each strategy's `llm_judge` metric field. `--deterministic-local` disables the judge and all configured model clients for repeatable smoke runs.

## Run

```powershell
.\.venv\Scripts\python -m backend.app.evaluation.runner `
  --cases evals/rag_ab/starter_cases.jsonl `
  --output-dir evals/rag_ab/runs/latest `
  --baseline baseline-current `
  --comparison current-evidence `
  --deterministic-local `
  --top-k 8
```

Run with the QASPER public validation cases:

```powershell
.\.venv\Scripts\python -m backend.app.evaluation.runner `
  --cases evals/rag_ab/qasper_validation_cases.jsonl `
  --output-dir evals/rag_ab/runs/qasper_validation `
  --baseline baseline-current `
  --comparison current-evidence `
  --deterministic-local `
  --top-k 8
```

Run the locally imported QASPER subset with chunk-level recall metrics:

```powershell
.\.venv\Scripts\python -m backend.app.evaluation.runner `
  --cases evals/rag_ab/qasper_validation_local_subset_chunked.jsonl `
  --output-dir evals/rag_ab/runs/qasper_old_local_vs_current_chunked `
  --baseline old-code-api `
  --old-code-api-url http://127.0.0.1:8002 `
  --comparison current-evidence `
  --deterministic-local `
  --top-k 8
```

Optional old-code API baseline:

```powershell
.\.venv\Scripts\python -m backend.app.evaluation.runner `
  --baseline old-code-api `
  --old-code-api-url http://127.0.0.1:8001 `
  --comparison current-evidence
```

Outputs:

- `case_results.jsonl`: raw case-level strategy outputs and metrics.
- `aggregate_metrics.json`: aggregate metrics by strategy.
- `report.md`: human-readable comparison report.
- `run_config.json`: reproducibility metadata.

## Current Citation Mode

`precision` is the default `rag_citation_selection_mode`. It keeps citations tied to claim-level answer sources and filters them to high-confidence accepted direct/partial evidence. On the 12-case chunk-aligned QASPER subset it matches `answer_linked` on citation F1 while preserving a stricter confidence requirement.

The other modes remain available for ablation:

- `answer_linked`: cites the selected claim source chunks directly. It has the same aggregate QASPER citation F1 as `precision`, but less filtering.
- `strict`: remains conservative and can return only one fallback citation, which lowers citation recall.
- `current`: can include slightly broader supplemental evidence, but its lower precision makes it unsuitable as the default.

Claim-level answer-source attribution now selects up to three extracted claims from distinct final-context chunks. The selector scores candidate sentences with question overlap, modest answer-intent boosts, evidence support priority, and a guarded reserve slot for close high-confidence claims. Current-evidence metadata preserves `answer_source_chunk_ids`, `answer_claims`/`claim_sources`, `claim_count`, `claim_candidates`, and `citation_selection_mode`.

Latest 12-case chunked QASPER results:

| mode | avg_citation_count | avg_citation_recall | avg_citation_precision | citation F1 | avg_answer_source_count | avg_answer_source_recall | avg_answer_source_precision | avg_final_context_recall | avg_expected_point_coverage | avg_quote_support_recall | error_count |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| strict | 1.0000 | 0.2083 | 0.2500 | 0.2273 | 3.0000 | 0.7083 | 0.3055 | 0.7917 | 0.3194 | 0.2222 | 0 |
| answer_linked | 3.0000 | 0.7083 | 0.3055 | 0.4269 | 3.0000 | 0.7083 | 0.3055 | 0.7917 | 0.3194 | 0.2222 | 0 |
| precision | 3.0000 | 0.7083 | 0.3055 | 0.4269 | 3.0000 | 0.7083 | 0.3055 | 0.7917 | 0.3194 | 0.2222 | 0 |
| current | 3.2500 | 0.7083 | 0.2778 | 0.3991 | 3.0000 | 0.7083 | 0.3055 | 0.7917 | 0.3194 | 0.2222 | 0 |

Known remaining issues:

- `qasper-val-0022` and `qasper-val-0024`: gold evidence is absent from final context because the evidence judge rejected or ranked it outside the accepted context.
- `qasper-val-0009`: one answer-source regression from the claim selector remains and should be inspected separately.

Recommended follow-ups are to inspect the `qasper-val-0009` regression and, later, consider a conservative evidence-judge rescue path for `qasper-val-0022` and `qasper-val-0024`.

## Regenerate QASPER Cases

The QASPER conversion command uses the Hugging Face Dataset Viewer API and selects cases deterministically by validation row order. It prefers answerable questions with non-empty text evidence, excludes figure/table-only support, includes no-answer coverage when available, and writes stable ids such as `qasper-val-0001`.

```powershell
.\.venv\Scripts\python -m backend.app.evaluation.qasper `
  --output evals/rag_ab/qasper_validation_cases.jsonl `
  --limit 30 `
  --no-answer-target 5
```

The generated file should contain 20-50 cases. Answerable cases include `expected_points` and `supporting_quotes`; no-answer cases set `should_answer` to `false` and do not require expected points or support quotes.

## Align Local QASPER Chunk Evidence

After importing matching QASPER PDFs locally and filling `library_id`/`paper_ids`, generate a chunk-aligned copy:

```powershell
.\.venv\Scripts\python -m backend.app.evaluation.qasper_align `
  --input evals/rag_ab/qasper_validation_local_subset.jsonl `
  --output evals/rag_ab/qasper_validation_local_subset_chunked.jsonl `
  --report-output evals/rag_ab/qasper_validation_local_subset_chunked_alignment.json `
  --fail-on-unmatched
```

The aligner keeps the source subset unchanged and resolves each QASPER support quote to one primary local evidence chunk. It also writes an alignment report with scores and alternate candidate chunks for review.
