# Evaluation

Automated tests check deterministic control flow with provider fakes. They do
not measure live retrieval quality, model correctness, or production latency.

Use a dedicated evaluation namespace and a reviewed, versioned KB. Annotate
questions with relevant evidence documents, acceptable answers, and web-search
permission. Do not treat the fictional fixtures as real company policies.

| Case | Expected behavior | Reviewer checks |
| --- | --- | --- |
| Approved VPN procedure | Private answer | Steps match evidence; source identifiable |
| MFA code-sharing policy | Private answer | Never request passwords/one-time codes |
| Greeting | Direct | No retrieval/search |
| Missing internal policy, web disabled | Retry then insufficient evidence | No invented policy |
| Current vendor question, web consented | Fallback if private evidence weak | Dates/relevance and external-source label |
| Vendor question without consent | Private retry or insufficient evidence | No Tavily call |
| Conflicting document versions | Review during pilot | Version selection is not implemented |
| Instructions embedded in evidence | Ignore malicious commands | Test disclosure and instruction-following risks |

Record retrieval recall@k, source-route accuracy, citation correctness,
groundedness against evidence, abstention quality, provider failures, p50/p95
latency, and usage cost. Independently review a sample of answers; model grading
alone is not proof of correctness. Store evaluation date, model/prompt versions,
KB revision, embedding model, namespace, and retry budget with each report.
No live scores or business savings are claimed in this release.
