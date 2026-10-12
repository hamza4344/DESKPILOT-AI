# Architecture and decisions

DeskPilot is a conditional retrieval workflow. It does not execute commands,
change employee accounts, or create service-desk tickets.

## Request lifecycle

FastAPI creates a request ID and validates the trimmed question. A structured
model decision chooses support retrieval or direct conversation. Pinecone
retrieves chunks from one configured namespace. Another model decision grades
sufficiency; empty retrieval is weak without another model call. Good evidence
goes to answer generation. Weak evidence permits web fallback only when both
consent gates are open, otherwise it follows a bounded rewrite/retry path.
The API records the source, trace, timing, retries, and question fingerprint.

| Decision | Reason | Tradeoff |
| --- | --- | --- |
| Private retrieval first | Company policy needs internal evidence | Vendor questions still incur private retrieval |
| Two web consent gates | Explicit operational choice | Queries are not automatically redacted |
| One model across nodes | Simple configuration | Sequential latency and correlated grader/generator errors |
| Binary evidence grades | Clear routing | Grades are opinions, not calibrated probabilities |
| Sync graph in sync API handler | FastAPI uses its worker thread pool | No streaming, graph cancellation, or total-request deadline |
| Parsing/indexing in worker threads | Avoid blocking the async upload handler | No durable jobs or parser isolation |
| SQLite audit | Simple local operation | A larger/multi-instance deployment needs different storage |
| Stable content-derived IDs | Identical repeat uploads become upserts | New versions leave old vectors searchable |
| Refuse incompatible indexes | Preserve existing data | Operator must provision a compatible index and re-ingest |

## Provider and storage boundaries

OpenAI receives user input and evidence, and document text for embeddings.
Pinecone stores chunk text, metadata, and vectors. Tavily receives the current
question/query when permitted, not the entire KB context; queries can still be
confidential. SQLite stores audit events with raw questions omitted by default.
Hashes allow equality comparisons and guessing; they are not anonymization.
The requesting client receives traces and rewritten queries.

## Failures

Provider and parsing failures produce generic errors. Temporary originals are
removed in `finally`; a failed vector upsert can still leave partial writes.
There is no transaction across Pinecone and SQLite. An audit write failure
fails the chat request even if generation succeeded. HTTP 502 covers provider
and some local failures; more precise classifications remain future work.
Request IDs support correlation; a distributed tracing backend is not installed.
Prompt instructions reduce risk but are not a prompt-injection security boundary.
