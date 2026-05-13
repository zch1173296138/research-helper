## Why

The project now has two meaningful RAG strategies to compare: the previous hybrid retrieval plus direct citation answer flow, and the current PaperQA-style staged evidence flow. We need a repeatable evaluation harness before tuning retrieval, evidence judging, prompts, or cost/latency trade-offs.

## What Changes

- Add a local RAG A/B evaluation capability that can run equivalent question sets against a baseline strategy and the current strategy.
- Define a JSONL evaluation dataset format with question metadata, target papers, expected answer points, support quotes or chunk ids, and no-answer cases.
- Add evaluators for retrieval quality, evidence quality, answer quality, citation grounding, missing-evidence behavior, latency, and token/cost metadata when available.
- Support using `old_code` as the baseline runtime when present, while also allowing an in-process baseline adapter that bypasses `EvidenceRagService`.
- Produce machine-readable results and a compact human-readable report for comparing A vs B.
- No breaking production API changes.

## Capabilities

### New Capabilities
- `rag-ab-evaluation`: Defines repeatable A/B evaluation of baseline and PaperQA-style RAG behavior, including datasets, runners, metrics, and reports.

### Modified Capabilities
- None.

## Impact

- Adds evaluation scripts or modules under a non-production evaluation boundary.
- Adds fixture datasets and documentation for constructing question sets.
- Reads existing SQLite/LanceDB storage and may call local API servers or in-process services, depending on selected mode.
- Does not change upload, parsing, indexing, chat, or paper QA behavior for users.
