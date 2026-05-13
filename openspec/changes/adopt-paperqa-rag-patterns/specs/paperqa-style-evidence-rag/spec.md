## ADDED Requirements

### Requirement: Broad Candidate Retrieval
The system SHALL retrieve a candidate evidence pool larger than the final answer citation set before generating an answer.

#### Scenario: Candidate pool exceeds answer context
- **WHEN** a user asks a paper-chat or library-chat question with `top_k` set to 8
- **THEN** the evidence pipeline retrieves at least 16 non-reference candidate chunks before evidence judging

#### Scenario: Candidate metadata is persisted
- **WHEN** the evidence pipeline completes retrieval
- **THEN** the answer metadata includes the candidate chunk ids and the final accepted chunk ids separately

### Requirement: Query-Aware Evidence Judging
The system SHALL evaluate retrieved candidate chunks against the user's question before final answer synthesis.

#### Scenario: Directly supporting chunk is accepted
- **WHEN** a candidate chunk directly answers the user's question
- **THEN** the evidence decision for that chunk is `accept` with a non-empty concise summary

#### Scenario: Irrelevant chunk is rejected
- **WHEN** a candidate chunk does not support the user's question
- **THEN** the evidence decision for that chunk is `reject` and the chunk is excluded from the final answer context

#### Scenario: LLM judge is unavailable
- **WHEN** no LLM client is configured or the judge call fails
- **THEN** the system falls back to ranked non-reference chunks and records the judge source as fallback metadata

### Requirement: Evidence Summary Synthesis
The system SHALL synthesize final answers from accepted evidence summaries and source snippets, not from the full unfiltered candidate pool.

#### Scenario: Accepted evidence exists
- **WHEN** one or more candidate chunks are accepted
- **THEN** the final LLM prompt includes only accepted evidence identifiers as citable sources

#### Scenario: No accepted evidence exists
- **WHEN** no candidate chunk is accepted by the judge or fallback
- **THEN** the answer states that no sufficient evidence was found and returns no citations

### Requirement: Citation Isolation
The system SHALL cite only accepted evidence chunk ids in generated answers.

#### Scenario: Model cites an unaccepted chunk
- **WHEN** the final answer includes a citation id that is not in the accepted evidence set
- **THEN** the backend rejects that citation and returns a constrained fallback or missing-evidence answer

#### Scenario: Conversation memory exists
- **WHEN** paper-chat memory or recent history helps clarify the question
- **THEN** the system uses memory only for intent and never treats memory as citable evidence

### Requirement: Evidence Debug Metadata
The system SHALL expose evidence-stage metadata for debugging and UI inspection.

#### Scenario: Answer returns retrieval metadata
- **WHEN** a paper-chat or library-chat answer is returned
- **THEN** the response metadata includes candidate ids, accepted ids, rejected ids, judge source, evidence summaries, and final context ids

#### Scenario: Debug metadata omits oversized text
- **WHEN** evidence metadata is persisted
- **THEN** stored snippets are capped so retrieval metadata remains bounded
