from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from agentiq.analysis import REFERENCE_AT
from agentiq.data import sample_records


def test_idempotent_import_and_status_update(store, clean_records):
    store.upsert(clean_records)
    store.upsert(clean_records)
    assert len(store.all_records()) == 17
    updated = {**clean_records[0], "status": "resolved", "resolved_at": "2026-10-11T09:00:00Z"}
    store.upsert([updated])
    assert len(store.all_records()) == 17
    row = store.list_records(source="Salesforce")["records"][0]
    assert row["status"] == "resolved"


def test_run_isolation(store, valid_record):
    store.upsert([{**valid_record, "owner_changes": 4}])
    first = store.create_run(REFERENCE_AT, 3)
    before = store.get_findings(first["run_id"])
    store.upsert([{**valid_record, "owner_changes": 0}])
    second = store.create_run(REFERENCE_AT, 3)
    assert first["run_id"] != second["run_id"]
    assert store.get_findings(first["run_id"]) == before
    assert any(f["type"] == "handoff_friction" for f in before["findings"])
    assert not any(f["type"] == "handoff_friction" for f in store.get_findings(second["run_id"])["findings"])
    assert store.get_findings("unknown") is None


def test_sql_queries(store, clean_records):
    store.upsert(clean_records)
    sql = (Path(__file__).resolve().parents[1] / "queries.sql").read_text(encoding="utf-8")
    statements = [s.strip() for s in sql.split(";") if s.strip()]
    with store.connect() as connection:
        open_counts, top_five, repeated = [connection.execute(s).fetchall() for s in statements]
    assert {r["source"]: r["open_count"] for r in open_counts} == {"Jira": 3, "Salesforce": 3, "ServiceNow": 3}
    assert len(top_five) == 5
    assert top_five[0]["owner_changes"] == 5
    assert repeated[0]["category"] == "Access Management"
    assert repeated[0]["record_count"] == 8


def test_api_end_to_end(app):
    with TestClient(app) as client:
        assert client.get("/health").json() == {"status": "ok"}
        response = client.post("/records", json=sample_records())
        assert response.status_code == 200
        result = response.json()
        assert (result["accepted_count"], result["rejected_count"], result["duplicate_count"]) == (17, 4, 1)
        assert len(result["rejected"]) == 4
        client.post("/records", json=sample_records())
        assert client.get("/records").json()["total"] == 17
        filtered = client.get("/records", params={"source": "Jira", "status": "open"}).json()
        assert filtered["total"] == 3
        pages = [client.get("/records", params={"limit": 4, "offset": offset}).json()["records"] for offset in [0, 4]]
        assert not ({(r["source"], r["id"]) for r in pages[0]} & {(r["source"], r["id"]) for r in pages[1]})
        run_response = client.post("/runs")
        assert run_response.status_code == 201
        run = run_response.json()
        response = client.get(f"/runs/{run['run_id']}/findings")
        assert response.status_code == 200
        assert response.json()["findings"] == run["findings"]
        for finding in response.json()["findings"]:
            assert {"type", "explanation", "rule_threshold", "observed_value", "supporting_records"} <= finding.keys()
        assert client.get("/runs/unknown/findings").status_code == 404


@pytest.mark.parametrize("query", [{"limit": 0}, {"limit": 101}, {"offset": -1}, {"source": "Other"}, {"status": "Paused"}])
def test_api_invalid_filters_and_pagination(app, query):
    with TestClient(app) as client:
        assert client.get("/records", params=query).status_code == 422


def test_api_invalid_batch_and_empty_batch(app):
    with TestClient(app) as client:
        assert client.post("/records", json={}).status_code == 422
        assert client.post("/records", json=[]).json()["accepted_count"] == 0
        result = client.post("/records", json=[None, {"id": "x"}]).json()
        assert result["rejected_count"] == 2
