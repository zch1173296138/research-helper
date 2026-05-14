## ADDED Requirements

### Requirement: QASPER Validation Case Dataset
The system SHALL provide a QASPER-derived validation case dataset in the existing RAG A/B JSONL case format.

#### Scenario: Load converted QASPER cases
- **WHEN** the existing evaluation case loader reads the QASPER validation JSONL file
- **THEN** every non-comment line SHALL parse as a valid evaluation case with `id`, `category`, `question`, and `should_answer`

#### Scenario: Provide requested sample size
- **WHEN** the QASPER validation dataset is created
- **THEN** it SHALL contain at least 20 and no more than 50 validation cases

#### Scenario: Use public benchmark provenance
- **WHEN** a QASPER case is converted
- **THEN** the converted case SHALL preserve source provenance identifying the `allenai/qasper` dataset, `qasper` config, `validation` split, and source paper or question identifiers where available

### Requirement: QASPER Field Mapping
The system SHALL map QASPER fields into Research Helper evaluation case fields without changing the existing case schema.

#### Scenario: Map answerable question
- **WHEN** a QASPER validation question has at least one answer annotation with evidence
- **THEN** the converted case SHALL set `should_answer` to true, map the QASPER question to `question`, include expected answer strings or spans in `expected_points`, and include evidence strings in `supporting_quotes`

#### Scenario: Map unanswerable question
- **WHEN** a QASPER validation question is marked unanswerable
- **THEN** the converted case SHALL set `should_answer` to false and SHALL NOT require `expected_points` or `supporting_quotes`

#### Scenario: Avoid local chunk coupling
- **WHEN** QASPER cases are converted before the source papers are imported into local storage
- **THEN** the converted cases SHALL leave local `supporting_chunk_ids` empty rather than inventing Research Helper chunk ids

### Requirement: QASPER Selection Rules
The system SHALL select QASPER validation cases deterministically and prefer cases suitable for text-only RAG evaluation.

#### Scenario: Deterministic selection
- **WHEN** the QASPER validation dataset is regenerated from the same source split and selection settings
- **THEN** the output case ids and selected source examples SHALL remain stable

#### Scenario: Prefer text evidence
- **WHEN** selecting answerable QASPER examples
- **THEN** examples with non-empty text evidence SHALL be preferred over examples requiring figure-only or table-only visual reasoning

#### Scenario: Include no-answer coverage
- **WHEN** suitable unanswerable QASPER examples are present in the validation split
- **THEN** the selected dataset SHALL include at least one no-answer case

### Requirement: QASPER Dataset Documentation
The system SHALL document how to use and regenerate the QASPER validation cases.

#### Scenario: Document evaluation use
- **WHEN** a developer reads the RAG A/B evaluation documentation
- **THEN** the documentation SHALL identify the QASPER validation case file and show how to pass it to the existing evaluation runner

#### Scenario: Document conversion constraints
- **WHEN** a developer reads the QASPER dataset notes
- **THEN** the documentation SHALL explain that normal evaluation uses the checked-in JSONL file and that regeneration requires access to the Hugging Face `allenai/qasper` validation split
