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
