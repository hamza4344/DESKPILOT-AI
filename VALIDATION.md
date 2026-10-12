# Validation record

Date: 2026-10-09
Environment: Linux, Python 3.12, isolated virtual environment

| Check | Result |
| --- | --- |
| Runtime and development dependency installation | Passed |
| `python -m pip check` | No broken requirements |
| Ruff lint | Passed |
| Ruff formatting check | 20 Python files formatted |
| `pytest -q` | 21 passed |
| `node --check static/js/app.js` | Passed |
| `git diff --check` | Passed |
| Relative documentation links | Passed |
| License file | Apache-2.0 license text preserved |

The tests use provider fakes and temporary audit/upload directories. No live
OpenAI, Pinecone, or Tavily calls were made during validation. Dependency
installation required network access. One third-party Starlette/AnyIO
BlockingPortal deprecation warning remains; it did not fail the suite.

The app home/liveness, chat contract, privacy defaults, provider errors,
uploads, parser failures, vector IDs, index guards, retry/consent paths,
private evidence preference, external fallback, greetings, and DOCX tables
are covered. These checks do not establish model answer accuracy or security
certification. Browser rendering, Docker build/run, hosted CI, Python 3.11,
and real-provider end-to-end behavior have not been validated here.

## Documentation revision

Product documentation and source change notices were revised on 2026-10-09.
Runtime logic and the OpenAI embedding configuration were unchanged. Relative
links, source formatting, change-notice coverage, and archive contents were
checked for this revision; the earlier runtime test results above remain applicable.
