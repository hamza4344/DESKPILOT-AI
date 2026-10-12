# Operations

Use a dedicated Pinecone index and namespace for initial evaluation. Default
small embeddings need 1,536 dimensions and cosine similarity. Fixture ingestion
writes vectors and can create a missing index. Production knowledge must be
approved separately. `run.py` binds to localhost:8080 with development reload.

`GET /api/health` checks liveness only. It does not verify provider connectivity,
credentials, ingestion privileges, or audit write access.

| Symptom | Check |
| --- | --- |
| Chat 502 | Capture the response reference; application error logs contain ID and exception type, not provider payloads. Check provider settings/connectivity. |
| Upload 503 | Configure a non-placeholder `ADMIN_API_KEY`; restart. |
| Upload 401 | Supply a matching `X-Admin-Key`. |
| Upload 413 | Reduce/split file or review `MAX_UPLOAD_BYTES`. |
| Upload 422 | No extractable text; OCR scanned PDFs separately. |
| Index mismatch | Use a new compatible index and re-ingest; existing index is preserved. |
| Old document still retrieved | Changed content creates new IDs; manually manage old-version deletion. |
| No public search | Check both consent gates, Tavily key, and whether internal evidence already sufficed. |
| Audit permission/locking errors | Check writable storage; consider managed DB for scale. |

## Retention

Events use the new `support_events` table. Reusing a legacy audit DB does not
migrate or scrub old `query_audit` data. Use a fresh database or explicitly review
legacy data. This source package excludes the prior database and uploaded original.
No retention scheduler or backup automation is implemented. Define retention,
backup protection, encryption, access, and deletion procedures before real use.
Deleting a local original does not delete its text/vectors from Pinecone.

## Capacity

No rate limiter, whole-request timeout, or durable ingestion queue is installed.
OpenAI timeouts apply per attempt; a graph makes several calls. Index polling
is bounded, but SDK request duration may exceed that budget. Put TLS, identity,
rate limits, and full-body limits at a reverse proxy. The application file-byte
limit operates after framework multipart processing and is not complete DoS
protection. Compressed DOCX contents and parser CPU/memory need additional limits.

Local checks are recorded in VALIDATION.md. Live provider calls, hosted CI,
container build/run, and identity integration need separate validation.
