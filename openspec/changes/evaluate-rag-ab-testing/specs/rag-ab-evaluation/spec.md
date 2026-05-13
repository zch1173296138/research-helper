## ADDED Requirements

### Requirement: Evaluation Cases
The system SHALL support a versioned JSONL evaluation case format for RAG A/B tests.

#### Scenario: Load valid evaluation cases
- **WHEN** the runner receives a JSONL file containing case ids, questions, paper ids, expected answer points, evidence expectations, and should-answer flags
- **THEN** the runner SHALL parse the cases and preserve their metadata in the result output

#### Scenario: Reject invalid evaluation cases
- **WHEN** a case is missing a required id, question, or should-answer flag
- **THEN** the runner SHALL fail before executing model calls and report the invalid case location

### Requirement: Strategy Adapters
The system SHALL evaluate at least one baseline RAG strategy and the current PaperQA-style evidence RAG strategy through a common adapter interface.

#### Scenario: Run current baseline adapter
- **WHEN** the baseline adapter is `baseline-current`
- **THEN** the runner SHALL bypass `EvidenceRagService` and use the current hybrid retrieval plus direct citation answer path

#### Scenario: Run current evidence adapter
- **WHEN** the comparison adapter is `current-evidence`
- **THEN** the runner SHALL use `EvidenceRagService` and include evidence metadata such as candidate ids, accepted ids, judge source, and final context ids when available

#### Scenario: Run old-code API adapter
- **WHEN** the baseline adapter is `old-code-api` and an old-code API URL is provided
- **THEN** the runner SHALL call the configured old-code chat endpoint and record the API URL and health-check result in the report

### Requirement: Retrieval Metrics
The system SHALL calculate retrieval metrics separately from answer metrics.

#### Scenario: Score supporting evidence recall
- **WHEN** a case provides supporting chunk ids or supporting quotes
- **THEN** the runner SHALL report whether each strategy returned those supports in candidates, final context, or citations when the corresponding metadata is available

#### Scenario: Detect reference contamination
- **WHEN** returned chunks or citations identify reference-section content
- **THEN** the runner SHALL report reference contamination for the affected strategy and case

### Requirement: Evidence Metrics
The system SHALL evaluate evidence-stage behavior when a strategy exposes evidence decisions.

#### Scenario: Score accepted evidence
- **WHEN** a strategy returns accepted and rejected evidence ids
- **THEN** the runner SHALL report accepted evidence precision and recall against the case evidence expectations

#### Scenario: Handle strategies without evidence decisions
- **WHEN** a baseline strategy does not expose evidence decisions
- **THEN** the runner SHALL mark evidence-stage metrics as not applicable rather than failing the run

### Requirement: Answer Metrics
The system SHALL score answer correctness and citation grounding for each strategy.

#### Scenario: Score expected answer points
- **WHEN** a case includes expected answer points
- **THEN** the runner SHALL report expected-point coverage for each strategy answer

#### Scenario: Score no-answer behavior
- **WHEN** a case has `should_answer` set to false
- **THEN** the runner SHALL report whether each strategy avoided unsupported answers and signaled missing or insufficient evidence

#### Scenario: Validate citations
- **WHEN** a strategy returns citations
- **THEN** the runner SHALL report whether citations reference returned evidence and whether cited text supports the expected evidence when support annotations exist

### Requirement: Reports
The system SHALL write both machine-readable and human-readable A/B results.

#### Scenario: Write raw results
- **WHEN** an evaluation run completes
- **THEN** the runner SHALL write per-case JSONL containing inputs, strategy outputs, metadata, metrics, timings, and errors

#### Scenario: Write aggregate report
- **WHEN** an evaluation run completes
- **THEN** the runner SHALL write aggregate metrics and a Markdown or HTML report that compares A and B by category and highlights failed cases

### Requirement: Reproducible Run Configuration
The system SHALL record enough configuration to reproduce a RAG A/B evaluation run.

#### Scenario: Record run configuration
- **WHEN** the runner starts an evaluation
- **THEN** it SHALL record the case file, strategy names, API URLs or in-process mode, top_k, timestamp, git revision when available, and output directory

#### Scenario: Avoid implicit service selection
- **WHEN** the runner uses API mode
- **THEN** it SHALL require explicit current and baseline API URLs rather than silently choosing localhost ports
