# Verification record

Verified on November 12, 2026 using Python 3.12 on Windows.

## Automated checks

Command: `python -m pytest -q`

Result: **59 passed, 1 warning**.

The warning is an upstream Starlette deprecation notice about using its test
client with HTTPX. It does not affect the current test results. Exact tested
dependency versions are recorded in `requirements-tested.txt`.

The desktop sandbox blocks the local socket pair used by asyncio, even though
the API tests use an in-process test client. Tests were therefore run with normal
local socket access and an explicit temporary directory inside the workspace.
This is an execution-environment constraint rather than an application setting.

## Executed walkthrough

Command: `python demo.py`

Observed results:

- 22 inputs, 18 structurally valid, 4 rejected, 1 duplicate, 17 unique accepted.
- Missing file and malformed JSON raise distinct exceptions; an empty array loads.
- 9 open and 8 resolved records; all 8 baseline durations equal 26 hours.
- 9 aging findings, 5 handoff findings, and 1 repeated-category finding.
- Two identical imports leave 17 database rows.
- Updating an existing identity changes its values without inserting a new row.
- Two runs with different input receive distinct IDs. The first run's stored
  findings remain unchanged and can be retrieved independently.
- Three-page collection follows pages 1, 2, and 3. A timeout, HTTP 429, and HTTP
  500 recover after a retry. HTTP 401 fails immediately.
- The tests additionally verify retry exhaustion after three attempts.
- API health/ingestion/filtering/run retrieval succeed. Invalid pagination returns
  422, and an unknown run returns 404.
- Changing the handoff threshold from 3 to 5 changes flagged records from 5 to 0.
- The logging test confirms sentinel API tokens and private record text are absent.

Full generated evidence is in [examples/walkthrough.json](../examples/walkthrough.json).
UUIDs vary when the walkthrough is rerun; the baseline calculations remain fixed.

## Scope

Tests use mocked external responses; no live enterprise platform was contacted.
The original repository root exercises were preserved and are not part of this
new package's test suite. Run tests from `assessment_solution` as documented.
