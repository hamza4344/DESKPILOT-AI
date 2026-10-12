# Engineering notes

DeskPilot uses a conditional retrieval workflow to make support answers auditable.
The following implementation choices affect reliability, cost, and operation.

| Area | Implementation | Reason / tradeoff |
| --- | --- | --- |
| Workflow | LangGraph conditional routes with a bounded retry budget | Explicit decisions are testable; sequential model calls add latency |
| Embeddings | OpenAI text-embedding-3-small, 1,536 dimensions by default | Hosted embeddings simplify setup; document text leaves the application boundary |
| Retrieval | Pinecone cosine similarity and a configured namespace | Centralized knowledge storage; document-level access controls remain future work |
| Index safety | Check model dimensions and index metric before use | Preserve existing vectors; incompatible model changes require re-ingestion into a new index |
| Ingestion | Content hashes and deterministic chunk IDs | Identical uploads upsert existing IDs; changed document versions require lifecycle cleanup |
| Public search | Server enablement plus request consent | Explicit permission; consent does not automatically redact sensitive queries |
| Evidence checks | Structured sufficient/weak grades and explicit abstention | Clear branching; live evaluation is needed to assess model grading quality |
| API | Validated requests, typed responses, request IDs, generic errors | Predictable integration and error correlation without exposing provider payloads |
| Uploads | Admin credential, file-byte limit, unique temporary paths, cleanup | Bounded application handling; parser isolation and reverse-proxy limits are still needed |
| Audit | Source, retries, timing, sanitized trace, and question fingerprint | Diagnosis with less stored text; fingerprints are not anonymization |
| Container | Non-root user and liveness healthcheck | Reduced runtime privilege; container operation still needs deployment validation |
| Quality | Provider-fake regression tests and Python CI matrix | Repeatable behavior checks; does not establish real model accuracy |

See [architecture](ARCHITECTURE.md) for request flow and failure semantics,
[operations](OPERATIONS.md) for deployment considerations, and
[evaluation](EVALUATION.md) for measuring retrieval and answer quality.
