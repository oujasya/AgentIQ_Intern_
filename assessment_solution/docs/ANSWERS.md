# Answers and coding explanations: Questions 1-25

These answers follow the supplied AgentIQ assessment. Complete executable code
is in the linked source modules; the snippets below explain the important parts.
Run all commands from `assessment_solution` after following the README setup.

## Q1. Create the sample dataset

**Answer:** [data/sample_records.json](../data/sample_records.json) contains 22
entries across Salesforce, ServiceNow, and Jira. The generator is
`sample_records()` in [agentiq/data.py](../agentiq/data.py).

```python
for source_index, source in enumerate(["Salesforce", "ServiceNow", "Jira"]):
    for index in range(7):
        # Build and append a dictionary containing the nine record fields.
        ...
```

The outer loop selects a system and the inner loop creates seven records for it,
giving 21 records. An exact copy of the first record is appended to make 22.
Each dictionary represents a support ticket. JSON serializes the list as an array
of objects. Python `None` becomes JSON `null`, used for unresolved tickets.
Dates use explicit UTC. The fixed analysis reference is November 10, 2026 at
00:00 UTC; calculations do not depend on today's date.

Intentional anomalies are Salesforce `1005` without `priority`, ServiceNow `2005`
without `title`, Jira `3003` with `created_at="not-a-timestamp"`, Jira `3006` with
`owner_changes=-2`, and a second exact copy of Salesforce `1001`. The three systems
also each have a record with ID `1001`, demonstrating that IDs are scoped to a
system. Open and resolved statuses are both present. Run `python -m agentiq sample`
to regenerate this same dataset.

## Q2. Read the file safely

**Answer:** `load_records(path)` in [data.py](../agentiq/data.py) opens UTF-8 text
with a context manager and parses it using `json.load`.

```python
with path.open(encoding="utf-8") as stream:
    records = json.load(stream)
```

`with` closes the file even if parsing fails. A missing file raises a clear
`FileNotFoundError`; malformed JSON becomes a `ValueError` containing its line and
column. Invalid UTF-8 also becomes a `ValueError`. Other file-access errors remain
`OSError` subclasses for the CLI to handle. A top-level value that is not a list is
rejected because the dataset contract is an array. A file containing `[]` returns
an empty list successfully. Returning `[]` for errors would conceal the difference
between an empty dataset and a failed read, so errors are not silently swallowed.

`demo.py` demonstrates all three requested cases. `test_safe_loading` verifies
them using temporary files. An invalid date inside a correctly quoted JSON string
does not make the JSON malformed; the loader accepts it for Q3 to validate.

## Q3. Validate individual records

**Answer:** `validate_record()` returns every structural error for one record;
`validate_records()` returns `(accepted, rejected)`. A rejected entry includes its
zero-based input position, original record, and list of reasons.

```python
reasons = validate_record(record)
if reasons:
    rejected.append({"input_index": index, "record": record, "reasons": reasons})
else:
    accepted.append(record)
```

The validator first checks for a dictionary so that strings, numbers, and null
elements do not crash field access. It requires all nine keys. Text fields must
be non-empty strings. The source must exactly match one of the three supported
systems. Creation time must be a valid UTC timestamp; resolution time must be
either a valid UTC timestamp or null. A regular expression checks the timestamp
shape, and `datetime.fromisoformat` rejects impossible dates such as February 30.

`owner_changes` must be a non-negative integer. Booleans are explicitly rejected
because `isinstance(True, int)` is true in Python. The validator gathers all
problems rather than forcing the user to fix one error at a time. It does not
mutate input. For the Q1 dataset, structural validation accepts 18 entries and
rejects four; the duplicate still counts as accepted until Q5.

## Q4. Normalize inconsistent values

**Answer:** `normalize_status()` strips surrounding spaces and uses `casefold()`
for case-insensitive matching, then looks up the value in `STATUS_MAP`.

```python
key = value.strip().casefold()
# closed/resolved/done -> resolved
# new/open/in progress -> open
```

For example, `" CLOSED "` becomes `"resolved"`, and `" open "` becomes `"open"`.
An unknown status such as `Paused` raises `ValueError`. The shared ingestion
pipeline records that failure as a rejection rather than guessing that the record
is open or resolved. This preserves trustworthy analysis counts.
`normalize_record()` copies the dictionary before changing it. It also serializes
valid timestamps consistently with a trailing `Z`, so equivalent UTC formats do
not remain inconsistent. Source names and categories retain their original values.

## Q5. Remove duplicates correctly

**Answer:** `deduplicate()` uses a set of `(source, id)` tuples.

```python
key = (record["source"], record["id"])
if key not in seen:
    seen.add(key)
    unique.append(record)
```

A set provides efficient membership checks. The first valid occurrence in a batch
is retained, input order is preserved, and subsequent occurrences are reported as
duplicates. Salesforce `1001`, ServiceNow `1001`, and Jira `1001` all remain because
their composite keys differ. The second Salesforce `1001` is removed.
`ingest()` composes validation, normalization, and deduplication so the CLI and API
share exactly the same behavior. The sample finishes with 17 unique records.

## Q6. Generate a summary

**Answer:** `summarize()` in [analysis.py](../agentiq/analysis.py) returns total,
open, resolved, source counts, and priority counts for accepted unique records.

```python
Counter(record["source"] for record in records)
```

`Counter` groups equal values and counts occurrences. Status totals use boolean
expressions inside `sum`: true contributes one and false contributes zero. The
sample result is 17 total, 9 open, and 8 resolved. Counts by source are Jira 5,
Salesforce 6, and ServiceNow 6. Counts by priority are High 9, Medium 4, and Low 4.
An empty list returns zero totals and empty grouping dictionaries. Rejections and
duplicates do not inflate summary denominators.

## Q7. Calculate resolution time

**Answer:** `resolution_times()` processes records whose normalized status is
`resolved` and calculates elapsed hours:

```python
hours = (resolved_at - created_at).total_seconds() / 3600
```

Both operands are timezone-aware UTC datetimes. `total_seconds()` includes whole
days, unlike the timedelta `.seconds` attribute alone. Dividing by 3,600 converts
seconds to hours. Open records are skipped. Missing resolution timestamps are
returned in an `issues` list. Dates earlier than creation are also reported as
issues, never converted into positive durations. Equal timestamps produce zero
hours. All eight resolved records in the baseline sample have a duration of 26
hours. The tests separately demonstrate missing, earlier, and equal timestamps.

## Q8. Identify aging work

**Answer:** `aging_work()` compares open records against the fixed reference:

```python
age_days = (reference - created_at).total_seconds() / 86400
if age_days > 7:
    ...
```

A day has 86,400 seconds. The comparison is strictly greater than seven, so a
record exactly seven days old is excluded. Future records have negative ages and
are also excluded. Results contain the source, ID, creation time, and precise age
in days. Sorting by negative age puts the oldest first, with source and ID as
deterministic tie-breakers. Nine baseline records qualify. Fractional ages are
retained for accurate threshold comparisons rather than rounded prematurely.

## Q9. Identify handoff friction

**Answer:** `handoff_friction()` flags `owner_changes > threshold`, defaulting to 3.
Each result includes source, ID, and observed owner-change count.

```python
percentage = 100 * flagged_count / len(records) if records else 0.0
```

The denominator is all accepted unique records, not just open work or the flagged
subset. Five of the 17 sample records qualify, approximately 29.41%. Exactly three
changes is not flagged. An empty dataset returns 0.0% instead of dividing by zero.
The `analyze()` function converts these observations into findings with the rule,
threshold, explanation, and supporting record identity.

## Q10. Identify repeated work

**Answer:** `repeated_work()` groups records by category with `defaultdict(list)`
and retains groups containing at least five records. The list stores source/ID
pairs, so evidence remains unambiguous across systems. The output includes the
category, count, contributing identities, and an explanation. Access Management
has eight records in the sample; other categories do not reach five.

Frequency suggests a worthwhile investigation but does not prove suitability for
automation. The work may involve different causes, human judgment, sensitive
permissions, or costly exceptions. Before automating, investigate repeatable steps,
available integrations, exception rates, failure consequences, and expected time
savings. The code therefore calls these findings investigation candidates.

## Q11. Create a basic API

**Answer:** [api.py](../agentiq/api.py) provides an application factory and a
`GET /health` endpoint returning `{"status": "ok"}` with HTTP 200.

```powershell
python -m uvicorn agentiq.api:create_app --factory --reload
```

FastAPI associates decorated functions with HTTP routes and generates OpenAPI
documentation at `/docs`. The factory loads configuration once and creates the
database store. Tests inject a temporary database using the same factory, keeping
test data isolated from development data. `--reload` is for local development.

## Q12. Add a record ingestion endpoint

**Answer:** `POST /records` accepts a top-level JSON array. Its elements are typed
as `Any` deliberately: a malformed individual element should receive a per-record
rejection, while valid neighbors can still be accepted.

```python
result = ingest(records)
store.upsert(result["records"])
```

The endpoint reuses the Q3-Q5 pipeline and persists only clean unique records. Its
response includes input count, valid count, accepted count, rejected count,
duplicate count, duplicate identities, and rejected records with reasons. Here,
`accepted_count` means unique accepted records in this request, not newly inserted
database rows. A non-array request body returns HTTP 422. An empty array is valid
and returns zero counts. The sample response reports 17 accepted, 4 rejected, and
1 duplicate.

## Q13. Add filtering and pagination

**Answer:** `GET /records` supports optional `source` and `status`, plus `limit`
and `offset`. FastAPI validates source/status using `Literal` and pagination using
`Query(ge=1, le=100)` and `Query(ge=0)`. Invalid values return HTTP 422.

```sql
ORDER BY source, id LIMIT ? OFFSET ?
```

Stable ordering prevents arbitrary row order between pages when data is unchanged.
Filters use SQL placeholders; user values are never concatenated into SQL. The
response contains total matching count, requested limit/offset, and page records.
For example, `?source=Jira&status=open&limit=2&offset=0` returns the first two of
three matching baseline records. Concurrent writes may shift offsets; this is
documented as a limitation of offset pagination.

## Q14. Handle a paginated external API

**Answer:** `collect_pages()` in [connector.py](../agentiq/connector.py) requests
`?page=1`, reads `next_page`, and continues until it is null. The external response
contract is `{"records": [...], "next_page": 2}`. Tests and `demo.py` use
`httpx.MockTransport` to serve three pages without a live service.

The connector extends a single list with every page's records. It does no
normalization or analysis; callers pass the final list to `ingest()`. Separating
these responsibilities allows the same analysis to work with files, APIs, or
future adapters. A visited-page set detects cycles, a 100-page bound prevents
unlimited traversal, and malformed page structures fail clearly. Numeric cursors
remain parameters on the configured endpoint rather than arbitrary URLs.

## Q15. Handle integration failures

**Answer:** The connector uses at most three attempts per page and a ten-second
request timeout. `sleep` is injectable, so tests capture retry delays without
actually waiting.

| Failure | Behavior | Reason |
| --- | --- | --- |
| Timeout/transport failure | Retry up to three total attempts | May be transient for this read-only GET |
| HTTP 401 | Fail after one attempt | Repeating the same credentials will not fix authorization |
| HTTP 429 | Retry with bounded delay | Rate limiting may clear |
| HTTP 500 | Retry with bounded delay | The server may recover |
| HTTP 403/404 and other non-retryable codes | Fail immediately | Require correction rather than blind retries |

Fallback delays are one second then two seconds. A valid `Retry-After` value,
including an HTTP date, is honored with a maximum delay of 30 seconds. Repeated
transient failures raise a sanitized `ConnectorError` after the third attempt.
Tests demonstrate both recovery and exhaustion. Automatic redirects are disabled,
and neither response bodies nor tokens appear in error messages.

## Q16. Store records in SQLite

**Answer:** [storage.py](../agentiq/storage.py) creates a `records` table with all
nine fields and a composite primary key:

```sql
PRIMARY KEY (source, id)
```

This enforces uniqueness in the database even across repeated imports. Source and
status have allowed-value checks, and owner counts have a non-negative check.
Dates are stored as canonical UTC text after application validation. SQLite SQL
uses named or positional parameters for values. `Store.connect()` enables foreign
keys and wraps operations in a transaction, committing on success and rolling
back on failure. Its `finally` block closes the connection, releasing resources.

## Q17. Make repeated imports safe

**Answer:** `Store.upsert()` uses `INSERT ... ON CONFLICT(source,id) DO UPDATE`.
New identities insert rows; existing identities update their mutable values. The
same clean dataset imported twice leaves 17 rows rather than 34.

If an existing record arrives with an updated status, the latest accepted import
replaces the stored status, resolution timestamp, and other supplied fields.
Validation rejects incomplete records before persistence, so this is full-record
replacement rather than a partial patch. Within one batch, Q5's first occurrence
wins; across separate imports, the latest accepted batch wins. The tests update
an open record to resolved and verify that the row count remains unchanged.
Without an upstream version or update timestamp, older imports cannot be detected.

## Q18. Write three SQL queries

**Answer:** [queries.sql](../queries.sql) contains:

```sql
SELECT source, COUNT(*) AS open_count
FROM records
WHERE status = 'open'
GROUP BY source
ORDER BY source;

SELECT source, id, owner_changes
FROM records
ORDER BY owner_changes DESC, source ASC, id ASC
LIMIT 5;

SELECT category, COUNT(*) AS record_count
FROM records
GROUP BY category
HAVING COUNT(*) >= 5
ORDER BY record_count DESC, category ASC;
```

`WHERE` filters individual rows before grouping. `GROUP BY` combines rows with the
same source or category. `HAVING` filters the resulting groups by their aggregate
count. `LIMIT 5` restricts the second query to five rows, with stable tie-breaking.
Baseline open counts are three for each source. Access Management has eight
records. Sources with zero open work are omitted by the first query.

## Q19. Keep analysis runs separate

**Answer:** Each `Store.create_run()` generates a UUID with `uuid4()` and stores
run metadata, the accepted input snapshot, the analysis report, and individual
findings. Each finding has a foreign-key `run_id` and an ordinal within that run.

```sql
SELECT finding_json FROM findings
WHERE run_id = ? ORDER BY ordinal
```

The snapshot and findings are saved in one transaction, so a run cannot contain
partially saved results. Later imports update live records but cannot rewrite
historical findings. `demo.py` creates a first run, changes a record's status and
owner count, and creates a second run. It verifies different IDs and different
findings, then retrieves the first run again and confirms it is unchanged.
Execution timestamps use actual UTC, while calculations use the fixed reference.

## Q20. Make findings explainable

**Answer:** `GET /runs/{run_id}/findings` returns only the selected run's findings.
Each contains `type`, `explanation`, `rule_threshold`, `observed_value`, and
`supporting_records`. For example, a handoff finding can contain:

```json
{
  "type": "handoff_friction",
  "explanation": "Owner changes exceed the configured threshold.",
  "rule_threshold": {"operator": ">", "value": 3, "unit": "owner_changes"},
  "observed_value": 4,
  "supporting_records": [{"source": "Salesforce", "id": "1004"}]
}
```

The operator makes boundary behavior explicit. Units distinguish days from counts.
Source/ID pairs identify evidence without confusing equal IDs from different
systems. The response also includes the reference time and handoff threshold.
An unknown run returns HTTP 404 with `Analysis run not found`. An existing run
with no findings returns HTTP 200 and an empty list.

## Q21. Write meaningful automated tests

**Answer:** [tests](../tests) contains 59 collected test cases. Run
`python -m pytest -q`. The required cases and expected results are:

| Case | Expected result |
| --- | --- |
| Valid record | One accepted record and no rejection |
| Invalid or impossible timestamp | Rejected with a timestamp reason |
| Duplicate source/ID | Keep the first and report one duplicate |
| Equal ID, different sources | Keep both records |
| Empty input | Empty accepted/rejected lists, zero analysis counts |
| Exactly three owner changes at threshold 3 | Not flagged |
| Four owner changes at threshold 3 | Flagged |
| Exactly five owner changes at threshold 5 | Not flagged |
| Six owner changes at threshold 5 | Flagged |
| Two runs with changed input | Different IDs; earlier results unchanged |

Additional tests cover loading failures, boolean/float counts, missing fields,
unknown statuses, resolution anomalies, the exact age/category boundaries,
idempotent updates, SQL queries, API validation, connector recovery/exhaustion,
pagination errors, and safe logging. Temporary file-backed databases isolate
tests. Mock transports prevent real external HTTP requests.

## Q22. Debug the incorrect calculation

**Answer:** The original code divides by `len(records) - 1`. An arithmetic mean
uses the number of records, so the correct denominator is `len(records)`.

```python
def average_owner_changes(records):
    return (
        sum(record["owner_changes"] for record in records) / len(records)
        if records
        else 0.0
    )
```

The empty-list convention is explicitly 0.0, avoiding division by zero. With one
record containing 4 changes, the result is 4.0. With counts 1, 3, and 5, the total
is 9 and the mean is `9 / 3 = 3.0`. The original denominator would produce 4.5
for that example and crash for one record. The function expects already validated
records; it does not duplicate field-validation logic.

## Q23. Move settings out of the code

**Answer:** [settings.py](../agentiq/settings.py) reads `DATABASE_PATH`,
`EXTERNAL_API_URL`, and `API_TOKEN` from the environment. It also exposes
`REFERENCE_AT` and `HANDOFF_THRESHOLD`. `.env.example` documents placeholders,
and `python-dotenv` loads an optional local `.env` without overriding existing
environment variables.

The frozen dataclass provides one startup configuration object. The token field
uses `repr=False`, so printing that object does not expose credentials. The
reference timestamp and non-negative integer threshold are validated at startup.
`.gitignore` excludes real environment files, databases, logs, bytecode, test
caches, and virtual environments while retaining `.env.example`. Configuration
changes require a new CLI invocation or API restart.

## Q24. Add useful logging

**Answer:** The `agentiq` logger records ingestion counts, validation failures,
connector failures, and analysis completion. Analysis logs contain their `run_id`.
Ingestion happens before a run is created, so it does not invent an unrelated run ID.

```text
WARNING agentiq validation_failed input_index=4 reasons=Missing required field: priority
INFO agentiq ingestion input=22 accepted=17 rejected=4 duplicates=1
WARNING agentiq connector_failure page=1 attempt=1 status=401
INFO agentiq analysis_completed run_id=... accepted=17 findings=15
```

Validation messages use fixed field descriptions, never submitted values. Connector
messages record page, attempt, and status rather than URLs, credentials, exception
bodies, or payloads. HTTPX request logging is disabled in the CLI/API entry points.
`test_logs_omit_token_and_record_payload` supplies a sentinel secret and private
title, triggers all four log categories, and asserts neither sentinel appears.
It also checks the run ID is present and the token is absent from settings repr.
Rejected records remain in API responses for review, which is separate from logging.

## Q25. Deliver and demonstrate the application

**Answer:** The deliverable includes the integrated package, sample data, automated
tests, environment example, SQL queries, this answer guide, README setup/API
instructions, and generated walkthrough evidence. Git commits separate the core
data/analysis code, API/persistence/integration code, and tests/documentation.

For a 20-minute walkthrough:

1. Run `python -m agentiq sample`, inspect a valid record and each deliberate error.
2. Run ingestion twice and show the database stays at 17 rows.
3. Trace Salesforce `1004` through validation, normalization, persistence, and its
   finding with observed owner changes 4 and threshold `> 3`.
4. Start the API and demonstrate ingestion, a filtered page, and an unknown run.
5. Run `python demo.py` to show three external pages and the four failure cases.
6. Run the tests, then set `HANDOFF_THRESHOLD=5` and execute a new analysis.
7. Compare thresholds: five flagged records at 3, none at 5. Show boundary tests
   for both configurations and confirm older runs retain their original results.

The setting changes the threshold without editing production code. Tests exercise
both values rather than relying on a global constant. See the README for exact
PowerShell commands, limitations, and AI assistance disclosure. Full implementation
code is in the linked modules, not only illustrative snippets in this guide.
