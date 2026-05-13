## ADDED Requirements

### Requirement: Sliding-window memory compression
The paper chat system SHALL keep complete chat messages in storage while compressing older conversation turns into a session-level memory summary once the uncompressed history exceeds the configured recent-message window.

#### Scenario: Recent history remains uncompressed
- **GIVEN** a paper chat session has no more messages than the configured recent-message window
- **WHEN** the user sends a new question
- **THEN** the system SHALL include the recent messages directly in the answer context
- **AND** it SHALL NOT update `memory_summary`
- **AND** it SHALL NOT advance `compressed_until_message_id`

#### Scenario: Older history is compressed once
- **GIVEN** a paper chat session has more messages than the configured recent-message window
- **WHEN** the user sends a new question
- **THEN** the system SHALL summarize messages older than the recent window into `memory_summary`
- **AND** it SHALL set `compressed_until_message_id` to the newest message included in that summary
- **AND** it SHALL avoid re-summarizing messages whose id is less than or equal to `compressed_until_message_id`

#### Scenario: Existing memory is extended
- **GIVEN** a paper chat session already has a `memory_summary`
- **AND** new messages have accumulated after `compressed_until_message_id`
- **WHEN** the memory compression threshold is reached again
- **THEN** the system SHALL merge the existing memory with the newly compressed messages
- **AND** it SHALL preserve stable user preferences, unresolved questions, cited topics, and prior clarifications

### Requirement: Memory is prepended before recent messages
The paper chat system SHALL build the LLM answer context as structured conversation messages where the compressed memory summary is inserted before the recent uncompressed chat messages.

#### Scenario: Memory appears before the recent window
- **GIVEN** a paper chat session has a non-empty `memory_summary`
- **WHEN** the system prepares the LLM answer request
- **THEN** the request SHALL include the memory summary before recent user/assistant messages
- **AND** recent messages SHALL preserve their original roles and order
- **AND** the current user question SHALL remain the final user turn before evidence instructions are applied

#### Scenario: Memory is absent
- **GIVEN** a paper chat session has no `memory_summary`
- **WHEN** the system prepares the LLM answer request
- **THEN** the request SHALL omit the memory block
- **AND** it SHALL still include recent messages and the current question in a valid order

### Requirement: Memory-informed retrieval query rewrite
The paper chat system SHALL rewrite follow-up questions into standalone retrieval queries using memory and recent messages before running paper retrieval.

#### Scenario: Follow-up question is disambiguated
- **GIVEN** the recent conversation discussed a specific method, dataset, metric, or result
- **WHEN** the user asks a follow-up question with pronouns or vague references
- **THEN** the system SHALL produce a rewritten retrieval query that includes the relevant resolved entities
- **AND** hybrid retrieval SHALL use the rewritten query instead of only the raw user question
- **AND** retrieval metadata SHALL include both the original question and rewritten query

#### Scenario: Rewrite model is unavailable
- **GIVEN** the configured LLM service cannot rewrite the query
- **WHEN** the user asks a follow-up question
- **THEN** the system SHALL fall back to a deterministic rewrite using memory, recent turns, and the raw question
- **AND** retrieval metadata SHALL mark the rewrite source as `fallback`

### Requirement: Memory is not evidence
The paper chat system SHALL use conversation memory only to understand user intent, never as evidence for factual claims about the paper.

#### Scenario: Memory mentions an unsupported fact
- **GIVEN** the memory summary contains a claim from a previous answer
- **AND** current retrieval does not return chunks that support that claim
- **WHEN** the LLM generates the answer
- **THEN** the answer SHALL NOT cite memory as a source
- **AND** it SHALL either omit the unsupported claim or return `missing_evidence=true`

#### Scenario: Invalid citation is returned
- **GIVEN** the LLM returns a citation id that is not present in the retrieved chunks
- **WHEN** the backend validates the answer
- **THEN** the backend SHALL reject that citation
- **AND** it SHALL downgrade the answer to a missing-evidence response or regenerate a constrained fallback answer

### Requirement: Memory observability
The paper chat API SHALL expose enough memory metadata to debug compression and retrieval behavior.

#### Scenario: Session response includes memory state
- **WHEN** the frontend loads a paper chat session
- **THEN** the response SHALL include `memory_summary`, `compressed_until_message_id`, and `memory_updated_at`

#### Scenario: Answer response includes retrieval memory metadata
- **WHEN** the frontend sends a paper chat question
- **THEN** the response SHALL include retrieval metadata with the original question, rewritten query, rewrite source, recent message ids, and compressed boundary used for the answer

### Requirement: Backward-compatible sessions
The paper chat system SHALL continue to read and answer from existing sessions that were created before compressed memory boundaries existed.

#### Scenario: Old session has no compression boundary
- **GIVEN** an existing chat session has `memory_summary` but no `compressed_until_message_id`
- **WHEN** the user sends a new question
- **THEN** the system SHALL treat the missing boundary as no compressed messages
- **AND** it SHALL produce an answer without data loss
- **AND** it SHALL populate the boundary the next time compression runs
