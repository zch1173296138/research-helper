# RAG A/B Evaluation

This directory contains local JSONL datasets for comparing the previous hybrid RAG path with the current PaperQA-style evidence RAG path.

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
