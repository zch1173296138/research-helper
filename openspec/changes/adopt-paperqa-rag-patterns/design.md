## Context

Research Helper's current paper pipeline is:

```text
PDF -> MinerU full.md -> section chunks -> SQLite + FTS + LanceDB -> hybrid retrieval -> LLM answer with citations
```

The code already has useful foundations:

- `HybridRetriever` combines vector, FTS/keyword, structure-biased retrieval, second-pass queries, and neighbor chunks.
- `PaperChatService` rewrites follow-up questions using chat memory before retrieval.
- `LLMService` validates paper-chat citations against retrieved chunk ids and falls back to extractive answers when no API key is configured.
- MinerU already extracts Markdown plus image assets; future Docling/GROBID work can improve asset and metadata extraction.

PaperQA's most useful pattern for this project is the evidence discipline around RAG, not its package boundary. The project should adopt the workflow in small, testable layers while preserving the existing storage, API, and UI.

## Goals / Non-Goals

**Goals:**

- Add a PaperQA-style answer pipeline that separates candidate retrieval, evidence judging, evidence summarization, and final synthesis.
- Preserve local-first behavior and deterministic fallbacks when no LLM or external metadata API is configured.
- Persist enough metadata to debug why an answer cited particular chunks.
- Allow figure/table and metadata enrichment to improve retrieval without mixing generated text with original paper text.
- Keep the implementation compatible with current MinerU output and future Docling/GROBID additions.

**Non-Goals:**

- Do not replace the current FastAPI, SQLite, LanceDB, or frontend architecture with PaperQA's runtime.
- Do not replace MinerU as the main parser.
- Do not require Crossref, Semantic Scholar, Unpaywall, or other external APIs for core use.
- Do not make generated image/table descriptions citable as if they were original paper text.
- Do not implement a full agentic literature search workflow in the first pass.

## Decisions

### 1. Add a staged evidence service above `HybridRetriever`

Introduce a narrow backend service, tentatively `EvidenceRagService`, that orchestrates:

1. query preparation;
2. broad candidate retrieval;
3. evidence judging;
4. evidence summary generation;
5. final answer synthesis;
6. citation validation and metadata persistence.

The service should call `HybridRetriever` instead of replacing it. For paper chat, it should accept the already rewritten query from `PaperChatService`; for library chat, it can start with the raw question and later add a query rewrite step.

Alternative considered: replace `HybridRetriever` with a PaperQA-like retriever. That would discard working vector, FTS, section, and neighbor logic. A wrapper service keeps the change smaller and measurable.

### 2. Retrieve more candidates than the final answer uses

The first phase should request a larger candidate pool, for example `candidate_k = max(top_k * 3, 20)`, then let evidence judging reduce it to the final answer context. This matches the PaperQA idea that recall comes before precision.

The existing retriever's `top_k` currently limits returned chunks. This change can add a separate `candidate_k` parameter or call the retriever with a larger `top_k` internally, while still returning only accepted evidence to the final synthesis step.

Alternative considered: keep `top_k` unchanged and only re-rank those chunks. That is cheaper, but it limits the value of evidence judging because weak first-pass chunks crowd out better later candidates.

### 3. Evidence judging returns structured decisions

Add an LLM method such as `judge_evidence(question, candidates)` that returns structured JSON per chunk:

- `chunk_id`;
- `decision`: `accept`, `maybe`, or `reject`;
- `reason`;
- `support_level`: `direct`, `partial`, `background`, or `none`;
- `answerable_claims`;
- `concise_summary`.

When the LLM is unavailable, deterministic fallback should accept the highest-ranked non-reference chunks and mark `judge_source = "fallback_ranked"`.

Alternative considered: ask the final answer prompt to self-select evidence. That hides important decisions inside one generation step and makes debugging harder.

### 4. Final synthesis sees only accepted evidence summaries plus source snippets

The final answer prompt should receive:

- original question;
- accepted evidence summaries;
- compact source snippets for citation grounding;
- explicit rule that only accepted chunk ids may be cited.

`maybe` evidence may be included only in a clearly labeled "context, not citation" section or omitted in v1. The final answer should preserve the existing missing-evidence behavior when no accepted evidence is available.

Alternative considered: include all retrieved chunks and tell the model to be careful. The current system already does that; the point of this change is to make evidence acceptance explicit.

### 5. Persist evidence metadata separately from chat text

For v1, store evidence decisions inside existing answer retrieval metadata JSON where possible:

- `candidate_chunk_ids`;
- `accepted_chunk_ids`;
- `rejected_chunk_ids`;
- `evidence_decisions`;
- `evidence_summary_source`;
- `judge_source`;
- `final_context_chunk_ids`.

If metadata grows too large or must be queried independently, add a dedicated `answer_evidence` table later. Start with JSON to reduce migration risk.

Alternative considered: add full normalized evidence tables immediately. That is cleaner for analytics, but the product first needs stable behavior and prompt contracts.

### 6. Metadata enrichment is optional and provenance-first

Add a service boundary, tentatively `PaperEnrichmentService`, that can enrich a paper with:

- normalized title, authors, venue, year, DOI, arXiv id, and source URLs;
- lookup provider and confidence;
- extracted references when available from GROBID or external metadata sources.

The service must work with no external keys. If a provider is unavailable, it should record skipped/unavailable status and leave ingestion unaffected.

Alternative considered: couple metadata lookup to upload ingestion. That risks making PDF import slow and brittle. Enrichment should be a separate action or background task.

### 7. Figure/table enrichment creates non-original retrieval records

MinerU and future Docling output can produce image files and Markdown references. Enrichment should attach captions and optional generated descriptions to `PaperAsset` or a related table, with provenance fields:

- `asset_id` or path;
- `asset_type`: figure, table, page_image, unknown;
- `caption`;
- `page_start/page_end`;
- `source`: mineru, docling, grobid, llm_generated;
- `is_original_text`: false for generated descriptions.

Generated descriptions can be indexed for discovery, but final answers must distinguish them from original paper chunks. If cited, they should cite the parent paper chunk/caption/page, not the generated description alone.

Alternative considered: append generated image descriptions directly into `full.md`. That would make ingestion simple but pollute original text and weaken citation integrity.

### 8. Rollout in four steps

1. Add evidence judging and summaries for single-paper chat.
2. Reuse the same service for library-level chat.
3. Add metadata enrichment hooks and stored provenance.
4. Add figure/table enrichment once asset extraction metadata is reliable.

This order upgrades answer quality first, then enriches retrieval inputs.

## Risks / Trade-offs

- LLM cost and latency increase because judging adds an extra call -> batch candidates into one structured prompt, cap candidate count, and keep fallback behavior.
- Evidence judge may reject useful chunks too aggressively -> keep `maybe` decisions in metadata and add tests for overview/method/result/limitation questions.
- Structured JSON can fail to parse -> validate and fall back to ranked candidates rather than failing the user request.
- Metadata providers can be rate limited or unavailable -> keep enrichment optional, asynchronous-friendly, and non-blocking.
- Generated figure/table descriptions can hallucinate -> store provenance, keep them separate from original text, and do not allow them as sole citations.
- JSON metadata in chat messages can become large -> cap stored snippets and move to a normalized table if answer metadata becomes too heavy.

## Migration Plan

- Phase 1 requires no mandatory database migration if evidence decisions are stored in existing retrieval metadata JSON.
- Add nullable enrichment fields or a small enrichment table only when implementing metadata and asset enrichment.
- Existing papers and chat sessions remain valid; new evidence metadata appears only on new answers.
- Rollback path is to route chat/library answer calls back to `LLMService.answer_with_citations` and ignore the new metadata.

## Open Questions

- Should evidence judging be enabled by default for all questions, or only for high-quality mode?
- Should the frontend show rejected evidence by default, or hide it behind a debug control?
- Which metadata provider should be first: DOI/title lookup via Crossref, arXiv id parsing, Semantic Scholar, or GROBID-only local extraction?
- Should generated table/figure descriptions be indexed in the same LanceDB table with a provenance flag, or in a separate asset index?
