# Security boundaries

DeskPilot currently supports local development and a controlled internal pilot. It is
not certified or independently assessed for enterprise production use.

## Implemented controls

- Uploads require a configured non-placeholder admin key, compared with `compare_digest`.
- Uploaded file bytes are bounded, filenames are reduced to basenames, temporary paths are unique, and temporary originals are cleaned up.
- Public search requires server enablement and request consent.
- Existing vector indexes are not deleted on model/index mismatch.
- Provider error payloads are excluded from client errors and application error logs.
- Raw questions are omitted from audit events by default; rewritten query content is omitted from stored traces.
- Browser answer text is escaped, citation links are restricted to HTTP/HTTPS, and the container runs as non-root.

## Required deployment controls

Chat has no application authentication. A namespace is shared knowledge, not a per-user
or per-document access policy. Provide SSO/OIDC, authorization, TLS, rate limits, request
body limits, secret management, and network controls before granting employee access.
Never place the admin key in frontend code or commit it in `.env`.

File extensions are checked; files are not malware-scanned. PDF/DOCX parsing requires
resource isolation for untrusted inputs. A file-size limit does not bound decompressed
DOCX size or parsing CPU time. Prompt instructions do not guarantee prompt-injection
resistance. External-search consent does not redact confidential strings. OpenAI and
Pinecone receive private text as described in the architecture document.

An audit question hash is not anonymization or encryption. API traces and rewritten
queries are visible to the requesting client. Define retention and access rules for
responses, application infrastructure logs, vectors, and audit records.

## Reporting an issue

Contact the repository maintainer privately through an established contact channel.
Do not post API keys, employee data, or sensitive reproduction payloads in public issues.
This release does not configure a dedicated disclosure email or response SLA.
