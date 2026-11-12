# AgentIQ: complete 25-question assessment solution

A runnable support-record service covering Python, JSON, validation, analysis,
FastAPI, pagination, retries, SQLite, explainable findings, testing, and logging.

**Read [the detailed answers to Questions 1-25](docs/ANSWERS.md).**
The implementation is one integrated project. The original repository's root
`Q*.py` files are earlier exercises and remain separate from this solution.

## Setup

Requires Python 3.11 or newer. From the repository root:

```powershell
cd assessment_solution
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[test]"
Copy-Item .env.example .env
```

On macOS/Linux, activate with `source .venv/bin/activate` and copy settings with
`cp .env.example .env`. If PowerShell activation is restricted, use
`.\.venv\Scripts\python.exe` in place of `python` without activating the environment.

For the exact dependency versions used during verification:

```powershell
python -m pip install -r requirements-tested.txt
python -m pip install -e . --no-deps
```

`python-dotenv` reads `.env`; existing environment variables take precedence.
The checked-in token is a placeholder. A real token is only needed for `sync`.

## Run the project

```powershell
python -m agentiq sample
python -m agentiq ingest data/sample_records.json
python -m agentiq analyze
python -m pytest -q
python demo.py
```

The sample command writes 22 JSON entries. Ingestion accepts 18 structurally valid
entries, rejects 4 invalid entries, removes 1 duplicate, and persists 17 unique
records. Running ingestion twice leaves 17 rows. `analyze` saves a new immutable
run for the records currently in the database. `demo.py` uses isolated temporary
databases and mocked HTTP responses; it requires no external API credentials.

The checked-in [walkthrough evidence](examples/walkthrough.json) contains actual
results, including loading failures, summaries, analysis, pagination, retry cases,
repeated imports, SQL results, two runs, and the threshold comparison.

## Start the API

```powershell
python -m uvicorn agentiq.api:create_app --factory --reload
```

Open <http://127.0.0.1:8000/docs> for interactive API documentation.

| Method | Endpoint | Purpose |
| --- | --- | --- |
| GET | `/health` | Health response |
| POST | `/records` | Ingest a JSON array, return counts and rejection reasons |
| GET | `/records` | Filter and paginate persisted records |
| POST | `/runs` | Save a new analysis of the current database snapshot |
| GET | `/runs/{run_id}/findings` | Retrieve only that run's evidence |

### Example requests

These commands use `curl.exe` on Windows to avoid PowerShell's `curl` alias.
Use `curl` on macOS/Linux. Start the API in a separate terminal first.

```powershell
curl.exe http://127.0.0.1:8000/health
curl.exe -X POST http://127.0.0.1:8000/records -H "Content-Type: application/json" --data-binary "@data/sample_records.json"
curl.exe "http://127.0.0.1:8000/records?source=Jira&status=open&limit=2&offset=0"
curl.exe -X POST http://127.0.0.1:8000/runs
curl.exe http://127.0.0.1:8000/runs/REPLACE_WITH_RETURNED_RUN_ID/findings
```

Filters require canonical source names and `open`/`resolved`. `limit` must be
1-100 and `offset` must be non-negative; invalid inputs return HTTP 422. Records
are ordered by `(source, id)`. An unknown run returns HTTP 404.

### External connector

Configure `EXTERNAL_API_URL` and `API_TOKEN`, then run:

```powershell
python -m agentiq sync
```

The mock external protocol is `GET ?page=N` returning
`{"records": [...], "next_page": 2}`, with `next_page: null` on the last page.
The connector retries timeouts/transport failures and HTTP 429/500/502/503/504,
at most three attempts per page. HTTP 401 is not retried. `Retry-After` is honored
up to 30 seconds. Pages are bounded at 100 and repeated cursors are rejected.
No credentials are sent to a cursor-supplied URL or redirect.

## Verified baseline

| Measure | Result |
| --- | --- |
| Input entries | 22 |
| Structurally valid entries, including duplicate | 18 |
| Rejected entries | 4 |
| Duplicate entries removed | 1 |
| Unique accepted records | 17 |
| Open / resolved | 9 / 8 |
| Jira / Salesforce / ServiceNow | 5 / 6 / 6 |
| High / Medium / Low | 9 / 4 / 4 |
| Resolved-record durations | 8 records, each 26 hours |
| Open records older than seven days | 9 |
| Owner changes > 3 | 5 of 17, approximately 29.41% |
| Categories with at least five records | Access Management: 8 |
| Total findings at threshold 3 | 15 |
| Owner changes > 5 | 0 |

The reference date is fixed at `2026-11-10T00:00:00Z`, regardless of the day the
program runs. Run IDs and execution times intentionally change on every run.
See [verification notes](docs/VERIFICATION.md) for the executed checks.

## Walkthrough: change the handoff threshold

```powershell
python -m pytest tests/test_analysis.py -q
$env:HANDOFF_THRESHOLD = "5"
python -m agentiq analyze
Remove-Item Env:HANDOFF_THRESHOLD
```

At the default threshold 3, five sample records qualify. At threshold 5, none do,
because the highest valid sample count is 5 and the comparison is strictly `>`.
The parameterized boundary test checks both `3 -> excluded, 4 -> included` and
`5 -> excluded, 6 -> included`. The sample threshold test checks `5 -> 0` flagged
records. Existing runs retain their original threshold and findings.
Restart the API after changing its environment settings.

## Project structure

```text
agentiq/
    data.py          # Q1-5: sample, loading, validation, normalization, deduplication
    analysis.py      # Q6-10 and Q22: calculations and explainable findings
    connector.py     # Q14-15: external pagination and bounded retries
    storage.py       # Q16-20: SQLite records and immutable analysis runs
    api.py           # Q11-13 and Q20: FastAPI application factory
    settings.py      # Q23: environment configuration
    __main__.py      # sample / ingest / analyze / sync commands
data/sample_records.json
tests/               # Q21 plus integration, boundary, and logging checks
queries.sql          # Q18: three runnable SQL queries
demo.py              # Reproducible demonstrations
docs/ANSWERS.md      # Question-by-question coding explanations
docs/VERIFICATION.md
examples/walkthrough.json
.env.example
.gitignore
```

## Assumptions and limitations

- All nine schema keys are required. `resolved_at` may be null. IDs are non-empty
  strings and source names match Salesforce, ServiceNow, or Jira exactly.
- UTC timestamps require `Z` or `+00:00`. Source names, priority labels, and
  category names are not silently normalized. Unknown statuses are rejected.
- Within a batch, the first valid record for a source/ID wins. Across imports,
  the latest accepted record replaces the stored values. Without an upstream
  version field, stale imports cannot be detected.
- Resolution anomalies are reported by the duration calculation rather than
  rejecting otherwise structurally valid records. Invalid timestamps are rejected
  during validation.
- Findings analyze the current persisted dataset, not just the latest batch.
  Each run stores its own input snapshot and findings.
- Category frequency is a signal for investigation, not proof of automation
  suitability. Category comparisons are exact and case-sensitive.
- This is a local assessment service without authentication, authorization,
  distributed workers, or a live Salesforce/ServiceNow/Jira adapter. Do not expose
  the development server as a production deployment.
- Offset pagination has deterministic ordering for unchanged data. Concurrent
  imports may shift offsets. Runs hold full JSON snapshots, suitable for this
  small dataset rather than large-scale workloads.
- Application logs omit raw payloads and tokens. Rejection API responses include
  the original rejected record as requested evidence; these responses are not logs.

## AI assistance disclosure

OpenAI Codex assisted with implementing the integrated solution, writing the
question-by-question explanations and tests, and executing validation. The person
submitting this assessment should review the code and be prepared to explain and
modify it during the walkthrough.
