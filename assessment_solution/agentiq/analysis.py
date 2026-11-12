"""Questions 6-10 and 22: pure, deterministic analysis of clean records."""

from collections import Counter, defaultdict

from agentiq.data import parse_utc

REFERENCE_AT = "2026-11-10T00:00:00Z"


def identity(record):
    return {"source": record["source"], "id": record["id"]}


def summarize(records):
    return {
        "total": len(records),
        "open": sum(r["status"] == "open" for r in records),
        "resolved": sum(r["status"] == "resolved" for r in records),
        "by_source": dict(sorted(Counter(r["source"] for r in records).items())),
        "by_priority": dict(sorted(Counter(r["priority"] for r in records).items())),
    }


def resolution_times(records):
    results, issues = [], []
    for record in records:
        if record["status"] != "resolved":
            continue
        if record["resolved_at"] is None:
            issues.append({**identity(record), "reason": "Missing resolution timestamp"})
            continue
        hours = (parse_utc(record["resolved_at"]) - parse_utc(record["created_at"])).total_seconds() / 3600
        if hours < 0:
            issues.append({**identity(record), "reason": "Resolution timestamp precedes creation"})
        else:
            results.append({**identity(record), "resolution_hours": hours})
    return {"records": results, "issues": issues}


def aging_work(records, reference_at=REFERENCE_AT, days=7):
    reference = parse_utc(reference_at)
    results = []
    for record in records:
        if record["status"] == "open":
            age = (reference - parse_utc(record["created_at"])).total_seconds() / 86400
            if age > days:
                results.append({**identity(record), "created_at": record["created_at"], "age_days": age})
    return sorted(results, key=lambda r: (-r["age_days"], r["source"], r["id"]))


def handoff_friction(records, threshold=3):
    flagged = [{**identity(r), "owner_changes": r["owner_changes"]}
               for r in records if r["owner_changes"] > threshold]
    return {"threshold": threshold, "records": flagged,
            "flagged_count": len(flagged),
            "percentage": 100 * len(flagged) / len(records) if records else 0.0}


def repeated_work(records, minimum=5):
    groups = defaultdict(list)
    for record in records:
        groups[record["category"]].append(identity(record))
    return [{"category": category, "count": len(evidence), "supporting_records": evidence,
             "explanation": "Repeated work deserves investigation; check repeatability, exceptions, risk, and cost before automating."}
            for category, evidence in sorted(groups.items()) if len(evidence) >= minimum]


def average_owner_changes(records):
    """Q22: the denominator is n, not n - 1; empty input returns 0.0."""
    return sum(r["owner_changes"] for r in records) / len(records) if records else 0.0


def analyze(records, reference_at=REFERENCE_AT, handoff_threshold=3):
    handoffs = handoff_friction(records, handoff_threshold)
    aging = aging_work(records, reference_at)
    repeated = repeated_work(records)
    findings = []
    for row in aging:
        findings.append({"type": "aging_work", "explanation": "Open work is older than seven days.",
                         "rule_threshold": {"operator": ">", "value": 7, "unit": "days"},
                         "observed_value": row["age_days"],
                         "supporting_records": [{"source": row["source"], "id": row["id"]}]})
    for row in handoffs["records"]:
        findings.append({"type": "handoff_friction", "explanation": "Owner changes exceed the configured threshold.",
                         "rule_threshold": {"operator": ">", "value": handoff_threshold, "unit": "owner_changes"},
                         "observed_value": row["owner_changes"],
                         "supporting_records": [{"source": row["source"], "id": row["id"]}]})
    for row in repeated:
        findings.append({"type": "repeated_work", "explanation": row["explanation"],
                         "rule_threshold": {"operator": ">=", "value": 5, "unit": "records"},
                         "observed_value": row["count"], "category": row["category"],
                         "supporting_records": row["supporting_records"]})
    return {"summary": summarize(records), "resolution_times": resolution_times(records),
            "aging_work": aging, "handoff_friction": handoffs, "repeated_work": repeated,
            "average_owner_changes": average_owner_changes(records), "findings": findings}
