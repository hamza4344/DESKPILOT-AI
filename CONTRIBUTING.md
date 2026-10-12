# Contributing

Create a branch for each change and keep the change tied to a reproducible behavior.
Install `requirements-dev.txt`; run the lint, formatting, dependency, and pytest checks
listed in the README before submitting a pull request.

For retrieval or workflow changes, include a regression case showing the route before
and after the change. Do not run tests against real company indexes. API contract changes
must update the README and any affected browser code. Record user-visible changes in
`CHANGELOG.md` and keep license/provenance notices intact.

Never commit `.env`, provider keys, runtime databases, uploaded originals, or private KB
documents. The sample KB is fictional. Put organization-specific knowledge in approved
storage outside this source repository.

Pull requests should explain the problem, resulting behavior, checks performed, and
known limitations. Do not claim live evaluation results without a reproducible record.
