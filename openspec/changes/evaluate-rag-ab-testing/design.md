## Context

Research Helper currently has two relevant RAG execution paths:

```text
Baseline path:
question -> HybridRetriever(top_k) -> answer_with_citations / answer_paper_chat

Current path:
question -> EvidenceRagService -> HybridRetriever(candidate_k) -> evidence judge -> accepted evidence -> evidence-only answer
```

The `old_code` directory appears to contain an older runtime where `/api/chat` and paper chat use the baseline path, but it is not a clean fully passing old checkout because some OpenSpec and test artifacts from the PaperQA-style work are present. The evaluation design must therefore support both a live old-code API adapter and an in-process baseline adapter that reconstructs the old runtime behavior from the current services.

## Goals / Non-Goals

**Goals:**

- Make RAG quality changes measurable before further tuning.
- Compare baseline and current strategies on the same papers, questions, and expected evidence.
- Separate retrieval quality from answer generation quality.
- Include no-answer and citation-grounding checks, not just subjective answer preference.
- Produce reports that explain why a strategy won or lost for each question.
- Keep the harness local-first and deterministic where possible.

**Non-Goals:**

- Do not change production chat behavior or public user-facing APIs.
- Do not require external judge services for basic retrieval metrics.
- Do not require `old_code` to be clean or fully test-passing.
- Do not build a general experiment platform beyond RAG A/B evaluation.
- Do not automatically decide product rollout from a single score.

## Decisions

### 1. Treat strategy selection as an adapter boundary

Create small strategy adapters with a common output shape:

- `baseline_current_adapter`: runs current `HybridRetriever.search(top_k)` and `LLMService.answer_with_citations` or `answer_paper_chat`, bypassing `EvidenceRagService`.
- `current_evidence_adapter`: runs the current `EvidenceRagService`.
- `old_code_api_adapter`: optionally calls an already running `old_code` backend API when the user wants a live old-code comparison.

Rationale: the older directory is useful, but not clean enough to be the only baseline. The in-process baseline is simpler and more reproducible.

Alternative considered: check out old code into the current worktree for every run. That makes experiments slower and risks losing local work.

### 2. Store evaluation cases as JSONL

Use a versioned JSONL format such as:

```json
{
  "id": "brepmfr-method-001",
  "category": "method",
  "question": "BrepMFR 的核心方法是什么？",
  "paper_ids": ["paper_..."],
  "expected_points": ["uses B-rep graph representation", "uses Transformer/graph attention"],
  "supporting_quotes": ["The original B-rep model is converted into a graph representation"],
  "supporting_chunk_ids": [],
  "should_answer": true
}
```

Rationale: JSONL is diffable, append-friendly, easy to run in CLI scripts, and can include both exact chunk ids and quote-based expected evidence.

Alternative considered: store cases in SQLite. That is better for a large benchmark but unnecessary for the first local harness.

### 3. Score retrieval and answer separately

The runner should produce at least these metric groups:

- Retrieval: candidate recall, final context recall, reference contamination, strategy metadata, latency.
- Evidence: accepted evidence precision/recall when current strategy exposes decisions.
- Answer: expected-point coverage, missing-evidence accuracy, citation precision, unsupported-claim flags where judge support exists.
- Operations: latency, errors, token/cost metadata when available.

Rationale: answer-only scoring hides whether failures come from retrieval, evidence judging, or synthesis.

Alternative considered: ask an LLM to grade the final answer only. That is faster to build but less useful for debugging RAG.

### 4. Prefer deterministic metrics first, optional LLM judge second

Initial scoring should work without model keys by using:

- expected phrase or regex matching for answer points;
- supporting quote containment against returned chunks;
- citation chunk validation;
- missing-evidence behavior for no-answer cases.

An optional LLM judge can later grade semantic answer correctness and faithfulness, but it must be recorded as a separate judge source.

Rationale: local repeatability matters because this project already supports no-key mode.

Alternative considered: make LLM-as-judge mandatory. That would block local A/B runs and make regressions harder to reproduce.

### 5. Generate both machine-readable and human-readable reports

Each run should write:

- raw per-case JSONL with both A and B outputs;
- aggregate metrics JSON;
- a compact Markdown or HTML report with score tables and failed cases.

Rationale: raw JSON supports future analysis; a human report makes immediate tuning decisions easier.

Alternative considered: print only terminal output. That loses evidence needed to compare runs over time.

### 6. Keep data and runtime configuration explicit

The runner should require explicit inputs for:

- case file path;
- current project API URL or in-process mode;
- baseline mode (`baseline-current` or `old-code-api`);
- optional old-code API URL;
- output directory;
- top_k and optional paper/library ids.

Rationale: A/B results are only meaningful when the tested strategies and data are visible in the report.

Alternative considered: infer running ports automatically. That is convenient but can silently test the wrong service.

## Risks / Trade-offs

- Baseline drift from true historical code -> use `old-code-api` mode when the old backend is runnable and record the baseline mode in every report.
- Quote-based expected evidence can be brittle after re-chunking -> allow either exact chunk ids or quote/regex evidence checks.
- LLM output variability can obscure retrieval changes -> record retrieval metrics independently and support no-key deterministic answer scoring.
- Metrics can encourage gaming short answers -> inspect failed cases and include expected-point coverage plus citation precision rather than one score.
- Running two API servers can be confusing -> require explicit URLs and include health checks before executing cases.
- `old_code` has residual PaperQA artifacts -> do not rely on its tests; only call the specific baseline chat endpoints used for A/B.

## Migration Plan

- Add evaluation files and scripts without changing production service paths.
- Start with a small sample dataset from the current two imported papers.
- Run the harness locally against `baseline-current` and `current-evidence`.
- Optionally start `old_code` on a separate port and run `old-code-api` mode.
- Rollback is deleting or ignoring the evaluation directory; no database or API migration is required.

## Open Questions

- Should the first evaluation dataset live under `evals/` or `tests/fixtures/rag_eval/`?
- Should reports be Markdown first or HTML first?
- Should semantic LLM grading be included in the first implementation or deferred until deterministic metrics are stable?
- Should the runner query existing SQLite chunks directly for support quote matching, or rely only on returned citation metadata?
