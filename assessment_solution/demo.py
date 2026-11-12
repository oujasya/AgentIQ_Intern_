"""Reproduce the assessment walkthrough without a live external service."""

import argparse
import json
import logging
from pathlib import Path
from tempfile import TemporaryDirectory

import httpx
from fastapi.testclient import TestClient

from agentiq.analysis import REFERENCE_AT, analyze, average_owner_changes, handoff_friction
from agentiq.api import create_app
from agentiq.connector import ConnectorError, collect_pages
from agentiq.data import ingest, load_records, sample_records
from agentiq.settings import Settings
from agentiq.storage import Store


def connector_demonstration(kind):
    calls, delays = [], []
    def handler(request):
        page = int(request.url.params["page"])
        calls.append(page)
        if kind != "three_pages" and len(calls) == 1:
            if kind == "timeout":
                raise httpx.ReadTimeout("mock timeout", request=request)
            return httpx.Response(int(kind), headers={"Retry-After": "2"})
        return httpx.Response(200, json={"records": [{"page": page}], "next_page": page + 1 if page < 3 else None})
    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        try:
            rows = collect_pages(client, "https://mock.example/records", sleep=delays.append)
            result = {"collected_records": rows}
        except ConnectorError as error:
            result = {"error": str(error)}
    return {"requested_pages": calls, "retry_delays_seconds": delays, **result}


def build_evidence():
    raw = sample_records()
    result = ingest(raw)
    clean = result["records"]
    with TemporaryDirectory(prefix="agentiq-demo-") as directory:
        directory = Path(directory)
        loading = {}
        for name, content in (("missing", None), ("invalid", "[{]"), ("empty", "[]")):
            file = directory / f"{name}.json"
            if content is not None:
                file.write_text(content, encoding="utf-8")
            try:
                loading[name] = {"records": load_records(file)}
            except (OSError, ValueError) as error:
                # Record stable evidence without a machine-specific temporary path.
                loading[name] = {"error_type": type(error).__name__}
        store = Store(directory / "demo.sqlite3")
        store.upsert(clean)
        first_count = len(store.all_records())
        store.upsert(clean)
        second_count = len(store.all_records())
        first_run = store.create_run(REFERENCE_AT, 3)
        first_findings = store.get_findings(first_run["run_id"])
        updated = {**clean[0], "status": "resolved", "resolved_at": "2026-10-11T09:00:00Z", "owner_changes": 6}
        store.upsert([updated])
        second_run = store.create_run(REFERENCE_AT, 3)
        selected = store.get_findings(first_run["run_id"])
        assert selected == first_findings
        assert first_run["findings"] != second_run["findings"]
        queries = (Path(__file__).parent / "queries.sql").read_text(encoding="utf-8")
        # Execute SQL on the original data for comparison with the baseline report.
        store.upsert(clean)
        with store.connect() as connection:
            sql_results = [[dict(row) for row in connection.execute(statement)]
                           for statement in queries.split(";") if statement.strip()]
        settings = Settings(database_path=str(directory / "api.sqlite3"))
        with TestClient(create_app(settings)) as client:
            health = client.get("/health").json()
            ingestion = client.post("/records", json=raw).json()
            api_run = client.post("/runs").json()
            api_evidence = {"health": health, "ingestion_counts": {
                key: ingestion[key] for key in ("accepted_count", "rejected_count", "duplicate_count")},
                "filtered_page": client.get("/records", params={"source": "Jira", "status": "open", "limit": 2}).json(),
                "invalid_pagination_status": client.get("/records", params={"limit": 0}).status_code,
                "findings_status": client.get(f"/runs/{api_run['run_id']}/findings").status_code,
                "unknown_run_status": client.get("/runs/unknown/findings").status_code}
        evidence = {
            "reference_at": REFERENCE_AT,
            "q2_loading": loading,
            "ingestion": {k: v for k, v in result.items() if k != "records"},
            "baseline_analysis": analyze(clean),
            "api": api_evidence,
            "connector": {kind: connector_demonstration(kind) for kind in ("three_pages", "timeout", "401", "429", "500")},
            "repeated_import": {"first_count": first_count, "second_count": second_count},
            "sql_results": sql_results,
            "runs": {"first_run_id": first_run["run_id"], "second_run_id": second_run["run_id"],
                     "first_findings_count": len(first_run["findings"]), "second_findings_count": len(second_run["findings"]),
                     "selected_first_run_findings": selected, "first_run_unchanged": selected == first_findings},
            "q22_average": {"empty": average_owner_changes([]),
                            "one": average_owner_changes([{"owner_changes": 4}]),
                            "several": average_owner_changes([{"owner_changes": n} for n in (1, 3, 5)])},
            "q25_threshold_change": {
                "threshold_3": handoff_friction(clean, 3),
                "threshold_5": handoff_friction(clean, 5),
            },
        }
    return evidence


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="examples/walkthrough.json")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s %(message)s")
    logging.getLogger("httpx").setLevel(logging.CRITICAL)
    logging.getLogger("httpcore").setLevel(logging.CRITICAL)
    evidence = build_evidence()
    path = Path(args.output)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
    print(f"Walkthrough written to {path}")
    print("Input=22; valid=18; rejected=4; duplicates=1; accepted unique=17")
    print("Repeated imports: 17 -> 17 rows")
    print("Handoff threshold 3 -> 5: flagged records 5 -> 0")
    print("Two distinct analysis runs: earlier findings remain unchanged")


if __name__ == "__main__":
    main()
