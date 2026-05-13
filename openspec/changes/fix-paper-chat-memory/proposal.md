## Why

Paper chat currently stores a `memory_summary`, but it does not implement a complete chat memory strategy. The summary is appended inside a plain user prompt, old messages are repeatedly summarized without a compression boundary, and retrieval still uses the raw user question, so follow-up questions like "what about its limitations?" can retrieve weak evidence.

This change makes paper chat memory behave like a real sliding-window conversation context: old messages are compressed once, recent messages remain structured, and memory is used to disambiguate retrieval without becoming paper evidence.

## What Changes

- Add a compression boundary to each paper chat session so the system knows which messages have already been summarized.
- Build LLM answer context as structured messages: system rules, memory summary, recent uncompressed messages, current question, and evidence.
- Add retrieval-query rewrite using memory plus recent messages before hybrid retrieval.
- Keep memory separate from evidence: memory can clarify user intent, but only retrieved chunks can support factual claims and citations.
- Expose memory boundary metadata in API responses for debugging and UI transparency.
- Add tests covering compression boundaries, recent window construction, query rewrite, and evidence-only citation behavior.

## Capabilities

### New Capabilities
- `paper-chat-memory`: Conversation memory for per-paper chat, including compressed summary memory, structured recent context, retrieval query rewrite, and evidence isolation.

### Modified Capabilities

## Impact

- Backend data model: `ChatSession` gains memory boundary metadata.
- Backend services: paper chat orchestration, LLM prompt construction, and hybrid retrieval input change.
- API schemas: paper chat session and response include memory boundary/debug fields.
- Frontend: memory display can show coverage metadata without changing the core chat interaction.
- Tests: add memory strategy unit and integration coverage.
