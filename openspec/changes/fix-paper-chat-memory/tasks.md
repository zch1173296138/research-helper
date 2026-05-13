## 1. Data Model And Schemas

- [x] Add `compressed_until_message_id` and `memory_updated_at` to the chat session model and SQLite initialization path.
- [x] Update paper chat Pydantic schemas to expose memory boundary metadata on session and answer responses.
- [x] Keep existing chat sessions backward-compatible when the new fields are null or absent.

## 2. Memory Compression And Context Assembly

- [x] Implement a paper chat memory compaction helper that compresses only messages newer than the existing boundary and older than the recent-message window.
- [x] Update the memory summarization prompt so it merges existing memory with newly compressed turns and preserves user preferences, unresolved questions, prior clarifications, and cited topics.
- [x] Build answer context with memory first, then recent structured messages, then the current question.
- [x] Store memory boundary metadata in retrieval metadata for each assistant answer.

## 3. Retrieval Query Rewrite

- [x] Add an LLM query rewrite method for paper chat follow-up questions.
- [x] Add a deterministic fallback rewrite when the LLM is unavailable.
- [x] Route hybrid retrieval through the rewritten query while preserving the raw user question in metadata.
- [x] Include rewrite source, rewritten query, recent message ids, and compressed boundary in persisted retrieval metadata.

## 4. Evidence Isolation And Citations

- [x] Update paper chat answer prompting so memory is explicitly marked as non-evidence.
- [x] Validate that citations returned by the LLM map only to retrieved paper chunks.
- [x] Return or persist a missing-evidence fallback when the model cites unknown ids or retrieval lacks supporting chunks.

## 5. Frontend And Progress Tracking

- [x] Update paper chat API usage/types to handle memory boundary fields and retrieval rewrite metadata.
- [x] Add a small debug/display affordance for memory coverage if it fits the current paper chat panel without crowding the UI.
- [x] Update `PROJECT_PROGRESS.md` after implementation with the completed memory strategy, validation commands, and remaining risks.
- [x] Keep `openspec/changes/fix-paper-chat-memory/tasks.md` checkboxes current as tasks are completed.

## 6. Verification

- [x] Add backend tests for no-compression, first compression, repeated compression, and old-session compatibility.
- [x] Add backend tests that verify memory is prepended before recent messages.
- [x] Add backend tests for retrieval query rewrite metadata and fallback behavior.
- [x] Add backend tests proving memory cannot be used as citation evidence.
- [x] Run backend tests and frontend build before marking the change complete.
