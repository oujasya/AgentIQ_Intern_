import pytest

from agentiq.analysis import (REFERENCE_AT, aging_work, analyze, average_owner_changes,
                             handoff_friction, repeated_work, resolution_times, summarize)


def test_summary_and_resolution(clean_records):
    summary = summarize(clean_records)
    assert summary == {"total": 17, "open": 9, "resolved": 8,
                       "by_source": {"Jira": 5, "Salesforce": 6, "ServiceNow": 6},
                       "by_priority": {"High": 9, "Low": 4, "Medium": 4}}
    result = resolution_times(clean_records)
    assert len(result["records"]) == 8
    assert all(r["resolution_hours"] == 26 for r in result["records"])
    assert result["issues"] == []


def test_bad_resolution_dates(valid_record):
    missing = {**valid_record, "status": "resolved", "resolved_at": None}
    earlier = {**missing, "resolved_at": "2026-10-09T09:00:00Z"}
    same_time = {**missing, "resolved_at": valid_record["created_at"]}
    result = resolution_times([missing, earlier, same_time])
    assert len(result["issues"]) == 2
    assert result["records"][0]["resolution_hours"] == 0


def test_aging_exact_boundary_and_sort(valid_record):
    exact = {**valid_record, "created_at": "2026-11-03T00:00:00Z"}
    older = {**valid_record, "id": "older", "created_at": "2026-11-02T00:00:00Z"}
    oldest = {**valid_record, "id": "oldest", "created_at": "2026-10-01T00:00:00Z"}
    future = {**valid_record, "created_at": "2026-11-11T00:00:00Z"}
    rows = aging_work([exact, older, future, oldest], REFERENCE_AT)
    assert [r["id"] for r in rows] == ["oldest", "older"]
    assert rows[-1]["age_days"] == 8


@pytest.mark.parametrize("threshold,values,expected", [(3, [3, 4], [4]), (5, [5, 6], [6])])
def test_handoff_exact_threshold(valid_record, threshold, values, expected):
    records = [{**valid_record, "id": str(i), "owner_changes": value} for i, value in enumerate(values)]
    result = handoff_friction(records, threshold)
    assert [r["owner_changes"] for r in result["records"]] == expected
    assert result["percentage"] == 50


def test_repeated_work_exact_minimum(valid_record):
    four = [{**valid_record, "id": str(i)} for i in range(4)]
    assert repeated_work(four) == []
    five = four + [{**valid_record, "id": "4"}]
    result = repeated_work(five)
    assert result[0]["count"] == 5
    assert len(result[0]["supporting_records"]) == 5


def test_empty_analysis():
    result = analyze([])
    assert result["summary"]["total"] == 0
    assert result["findings"] == []
    assert result["handoff_friction"]["percentage"] == 0
    assert result["average_owner_changes"] == 0


def test_average_owner_changes():
    assert average_owner_changes([]) == 0.0
    assert average_owner_changes([{"owner_changes": 4}]) == 4.0
    assert average_owner_changes([{"owner_changes": n} for n in [1, 3, 5]]) == 3.0


def test_sample_threshold_walkthrough(clean_records):
    assert handoff_friction(clean_records, 3)["flagged_count"] == 5
    assert handoff_friction(clean_records, 5)["flagged_count"] == 0
