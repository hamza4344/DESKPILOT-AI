# Changelog

## 0.2.0 — 2026-10-09

Initial DeskPilot AI release with an evidence-driven IT support workflow.

### Added

- Request-correlated typed chat responses with elapsed time and retry count.
- Per-request external-search consent plus a default-off server gate.
- Upload limits, temporary-file cleanup, document content hashes, stable vector IDs.
- Regression tests and a Python 3.11/3.12 GitHub Actions configuration.
- Architecture, operations, security, contribution, and evaluation documentation.

### Changed

- Pinecone model/index incompatibility now fails without deleting the index.
- Readiness polling is bounded, and OpenAI attempts have configured timeouts.
- Raw audit questions are opt-in; rewritten query content is excluded from stored traces.
- Blank/default upload keys disable ingestion; key comparisons use constant-time comparison.
- Empty retrieval results bypass LLM grading and follow retry/escalation branches.
- Weak-evidence outcomes clear citations, avoiding stale source lists.
- Generation prompts separate system instructions from supplied evidence.
- DOCX tables are extracted; direct PDF/text readers replace community loaders.
- UI presents service-desk guidance, decision history, consent, and request references.
- Docker runs as non-root and includes a liveness health probe.

### Repository hygiene

- Excluded runtime databases and uploaded originals from the source distribution.
- Added credential and runtime-state exclusions for Git and Docker.

## Documentation revision — 2026-10-09

- Organized the README around the support problem, capabilities, and architecture.
- Consolidated third-party attribution in NOTICE and retained file change notices.
- Added engineering notes for implementation choices and operational tradeoffs.
