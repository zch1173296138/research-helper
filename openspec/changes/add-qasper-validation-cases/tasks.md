## 1. Source Data Inspection

- [x] 1.1 Confirm Hugging Face access to `allenai/qasper`, config `qasper`, split `validation`.
- [x] 1.2 Inspect QASPER validation row structure for paper id, questions, answers, evidence, unanswerable flags, and annotation ids.
- [x] 1.3 Define deterministic filtering and ordering rules for selecting 20-50 text-suitable validation cases.

## 2. Conversion Implementation

- [x] 2.1 Add a QASPER conversion script or command under the evaluation boundary.
- [x] 2.2 Map QASPER answerable examples to `question`, `should_answer=true`, `expected_points`, `supporting_quotes`, `tags`, and provenance metadata.
- [x] 2.3 Map QASPER unanswerable examples to `should_answer=false` with no required expected points or support quotes.
- [x] 2.4 Ensure converted cases use stable ids such as `qasper-val-0001` and preserve source dataset/config/split/paper/question identifiers.
- [x] 2.5 Leave `supporting_chunk_ids` empty unless local Research Helper chunk ids are available.

## 3. Dataset Artifact

- [x] 3.1 Generate a checked-in JSONL file containing 20-50 converted QASPER validation cases.
- [x] 3.2 Verify the generated JSONL contains at least one no-answer case when suitable source examples exist.
- [x] 3.3 Verify answerable cases include non-empty `expected_points` and `supporting_quotes` where QASPER evidence is available.

## 4. Documentation

- [x] 4.1 Update RAG A/B evaluation documentation with the QASPER validation case file path.
- [x] 4.2 Document the generation source, selection constraints, provenance fields, and regeneration command.
- [x] 4.3 Document that end-to-end local RAG evaluation requires the corresponding QASPER paper text/PDFs to be available in Research Helper storage.

## 5. Validation

- [x] 5.1 Add or update tests proving the QASPER JSONL loads through the existing evaluation case loader.
- [x] 5.2 Add or update tests for the converter mapping of answerable and unanswerable QASPER examples.
- [x] 5.3 Run the targeted evaluation tests with `python -m pytest`.
- [x] 5.4 Run a schema/load smoke check against the generated QASPER JSONL file.
