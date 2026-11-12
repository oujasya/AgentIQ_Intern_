import json

import pytest

from agentiq.data import (deduplicate, ingest, load_records, normalize_status,
                         parse_utc, sample_records, validate_record, validate_records)


def test_sample_requirements():
    records = sample_records()
    assert len(records) == 22
    assert {r["source"] for r in records} == {"Salesforce", "ServiceNow", "Jira"}
    assert records[0] == records[-1]
    accepted, rejected = validate_records(records)
    assert len(accepted) == 18
    assert len(rejected) == 4


def test_safe_loading(tmp_path):
    file = tmp_path / "records.json"
    with pytest.raises(FileNotFoundError):
        load_records(file)
    file.write_text("[{]", encoding="utf-8")
    with pytest.raises(ValueError, match="Invalid JSON"):
        load_records(file)
    file.write_text("[]", encoding="utf-8")
    assert load_records(file) == []
    file.write_text("{}", encoding="utf-8")
    with pytest.raises(ValueError, match="array"):
        load_records(file)
    file.write_text(json.dumps(sample_records()), encoding="utf-8")
    assert len(load_records(file)) == 22


def test_valid_input(valid_record):
    accepted, rejected = validate_records([valid_record])
    assert accepted == [valid_record]
    assert rejected == []


@pytest.mark.parametrize("timestamp", ["not-a-date", "2026-02-30T09:00:00Z", "2026-10-10T09:00:00", None, 42])
def test_invalid_timestamps(valid_record, timestamp):
    valid_record["created_at"] = timestamp
    accepted, rejected = validate_records([valid_record])
    assert not accepted
    assert "created_at" in rejected[0]["reasons"][0]


def test_timestamp_offsets():
    assert parse_utc("2026-10-10T09:00:00Z") == parse_utc("2026-10-10T09:00:00+00:00")
    with pytest.raises(ValueError):
        parse_utc("2026-10-10T09:00:00+05:30")


@pytest.mark.parametrize("value", [-1, True, 2.5, "3", None])
def test_invalid_owner_count(valid_record, value):
    valid_record["owner_changes"] = value
    assert any("owner_changes" in e for e in validate_record(valid_record))


def test_multiple_reasons_and_no_mutation(valid_record):
    del valid_record["title"]
    valid_record["source"] = "Other"
    before = valid_record.copy()
    assert len(validate_record(valid_record)) == 2
    assert valid_record == before
    assert validate_record(None) == ["Record must be a JSON object"]


@pytest.mark.parametrize("status,expected", [(" CLOSED ", "resolved"), ("Resolved", "resolved"),
    ("dOnE", "resolved"), (" New ", "open"), ("OPEN", "open"), ("In Progress", "open")])
def test_status_normalization(status, expected):
    assert normalize_status(status) == expected


def test_unknown_status_is_rejected(valid_record):
    valid_record["status"] = "Paused"
    result = ingest([valid_record])
    assert result["accepted_count"] == 0
    assert result["rejected_count"] == 1
    assert "Unknown status" in result["rejected"][0]["reasons"][0]


def test_duplicate_identity(valid_record):
    other_source = {**valid_record, "source": "Jira"}
    records, duplicates = deduplicate([valid_record, valid_record.copy(), other_source])
    assert records == [valid_record, other_source]
    assert duplicates == [{"source": "Salesforce", "id": "1001"}]


def test_empty_input():
    assert validate_records([]) == ([], [])
    assert ingest([])["accepted_count"] == 0
    assert deduplicate([]) == ([], [])


def test_pipeline_sample():
    result = ingest(sample_records())
    assert (result["valid_count"], result["rejected_count"], result["duplicate_count"], result["accepted_count"]) == (18, 4, 1, 17)
    assert {r["source"] for r in result["records"] if r["id"] == "1001"} == {"Salesforce", "ServiceNow", "Jira"}
