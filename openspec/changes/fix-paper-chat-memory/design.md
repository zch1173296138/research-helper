## Context

Paper chat already stores full messages and a `memory_summary`, but the current strategy is incomplete:

- there is no durable compression boundary, so the service cannot know which messages were already summarized;
- the summary is passed as plain prompt text instead of being inserted as structured context before recent messages;
- retrieval uses the raw user question, so memory does not help follow-up questions resolve "it", "that method", or "the previous result";
- memory can influence wording, but the system must keep it separate from paper evidence because answers require real citations.

The corrected model is a sliding-window chat memory:

```text
full message log in SQLite
        |
        v
messages <= compressed_until_message_id
        |
        v
session.memory_summary
        |
        v
[system rules]
[memory summary]
[recent uncompressed messages]
[current user question]
[retrieved paper evidence]
```

## Goals

- Compress only old chat turns while preserving all raw messages in `chat_messages`.
- Insert compressed memory before recent uncompressed messages in the LLM request.
- Use memory and recent turns to rewrite retrieval queries for follow-up questions.
- Keep citations grounded only in retrieved paper chunks.
- Expose memory and rewrite metadata for debugging.
- Keep the first implementation local and per-paper; do not add cross-paper or cross-user long-term memory.

## Non-Goals

- No manual memory editor in the first pass.
- No streaming response changes.
- No cross-library user profile memory.
- No vector index for chat history; conversation memory remains session-level text plus recent structured turns.

## Decisions

### Add a compression boundary to chat sessions

Add nullable memory metadata to `chat_sessions`:

- `compressed_until_message_id`: newest chat message id included in `memory_summary`;
- `memory_updated_at`: timestamp for the last memory refresh.

Existing sessions treat a missing boundary as "nothing has been compressed yet". The boundary is advanced only after a successful summary update.

### Use fixed first-pass thresholds

Use simple service constants first:

- keep the most recent 6 messages uncompressed in the answer context;
- trigger compression when more than 10 uncompressed messages exist before the current question;
- cap each message excerpt passed into the memory summarizer to avoid large prompts.

These constants should live near the paper chat memory service so tests can reason about them. They can become settings later if needed.

### Compact before answering the new question

For each `ask` call:

1. Load the session and messages before the current question.
2. Compress old messages that are outside the recent window and newer than `compressed_until_message_id`.
3. Save the current user message.
4. Build recent context from uncompressed messages before the current question.
5. Rewrite the retrieval query using memory plus recent context.
6. Retrieve paper chunks with the rewritten query.
7. Ask the LLM with system rules, memory, recent context, current question, and retrieved evidence.
8. Save the assistant answer with citations and retrieval metadata.

This keeps the current user turn outside the compression input and makes the answer context deterministic.

### Build structured LLM messages

The LLM answer request should stop treating the whole chat as one large prompt string. Instead, build structured messages:

- system: citation rules, evidence-only constraints, missing-evidence behavior;
- system or developer-style context: compressed memory marked as conversation memory, not evidence;
- user/assistant messages: recent uncompressed turns in chronological order;
- user: current question plus retrieved evidence instructions.

If the existing LLM wrapper cannot accept structured messages cleanly, add a narrow method for paper chat rather than changing unrelated LLM calls.

### Rewrite retrieval queries before hybrid retrieval

Add a `rewrite_paper_chat_query` step to the LLM service. It receives:

- raw question;
- memory summary;
- recent messages;
- paper title and optional section hints.

The output is a concise standalone search query. If the model call fails or no API key is configured, use a fallback that appends high-signal terms from memory/recent messages to the raw question.

Store rewrite metadata in `retrieval_metadata`:

- `original_question`;
- `rewritten_query`;
- `rewrite_source`;
- `recent_message_ids`;
- `compressed_until_message_id`.

### Keep memory isolated from evidence

Prompt rules and backend validation must state that memory is not a citable source. Citations are valid only when they map to retrieved chunk ids. If the model cites an unknown id, the backend should reject it and return a constrained missing-evidence answer or a local fallback.

## Risks and Trade-offs

- Summary drift: compressed memory can lose nuance. Keeping the last 6 messages raw reduces the risk for current follow-ups.
- Prompt size: adding memory and recent turns increases tokens. Fixed windows keep cost predictable.
- Migration simplicity: this project currently initializes SQLite from SQLAlchemy models; the first pass can add startup-safe column creation rather than introduce Alembic immediately.
- Query rewrite cost: LLM rewrite adds one small call. The deterministic fallback keeps local/offline mode working.

## Migration Plan

- Add new nullable columns to `chat_sessions`.
- Ensure startup database initialization creates missing columns for existing SQLite databases.
- Leave existing `chat_messages` untouched.
- Treat missing `compressed_until_message_id` as no compressed boundary.

## Open Questions

- Whether the frontend should display memory metadata by default or hide it behind a debug affordance.
- Whether memory thresholds should later move to environment settings after behavior stabilizes.
