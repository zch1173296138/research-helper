## Why

The current RAG A/B evaluation has a small project-local starter dataset, but it does not provide the external credibility of a recognized public benchmark. QASPER validation cases are a good fit because they are research-paper question answering examples with evidence annotations and unanswerable questions that can be converted into the existing JSONL case format.

## What Changes

- Add a QASPER-derived validation dataset for local RAG A/B evaluation.
- Convert 20-50 QASPER validation examples into the existing evaluation case JSONL shape.
- Preserve QASPER provenance in case metadata, including source dataset, split, paper id, and source question or annotation identifiers where available.
- Populate `question`, `should_answer`, `expected_points`, `supporting_quotes`, `tags`, and `notes` from QASPER fields.
- Document selection criteria and conversion rules so the sample can be regenerated or expanded later.
- No production chat, upload, retrieval, or public API behavior changes.

## Capabilities

### New Capabilities

- `qasper-validation-dataset`: Defines the QASPER validation case dataset, conversion rules, provenance requirements, and acceptance criteria for using it in RAG A/B evaluation.

### Modified Capabilities

- None.

## Impact

- Adds a public-benchmark evaluation dataset under `evals/rag_ab/`.
- May add a small conversion script or documented generation command under the evaluation boundary.
- May add fixture validation tests to ensure converted QASPER cases conform to the existing evaluator schema.
- Requires network access only when regenerating the dataset from Hugging Face; normal evaluation runs consume the checked-in JSONL cases.
