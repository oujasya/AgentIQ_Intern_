"""Q21: Validate records. Adapted from the shared answer pack.
Complexity: O(n) time and output memory for bounded fields; include text length
for unbounded fields. Lesson: bool is an int subclass, so check exact types.
"""
from datetime import datetime

FIELDS = ("id", "source", "status", "category", "created_at", "owner_changes")
SOURCES = ("salesforce", "jira", "servicenow")
STATUSES = ("open", "closed")


def parse_date(value):
    if not isinstance(value, str):
        raise ValueError("Date must be a string")
    parsed = datetime.strptime(value, "%Y-%m-%d")
    # Parsing alone accepts unpadded months/days. Rebuild the exact format.
    exact = f"{parsed.year:04d}-{parsed.month:02d}-{parsed.day:02d}"
    if exact != value:
        raise ValueError("Expected exact YYYY-MM-DD format")
    return parsed


def validate_records(records):
    valid = []
    rejected = []
    for index, record in enumerate(records):
        reasons = []
        if not isinstance(record, dict):
            rejected.append({"index": index, "reasons": ["Record must be a dictionary"]})
            continue
        for field in FIELDS:
            if field not in record:
                reasons.append(f"Missing field: {field}")
        # Skip before accessing missing dictionary keys.
        if reasons:
            rejected.append({"index": index, "reasons": reasons})
            continue
        if not isinstance(record["id"], str) or not record["id"].strip():
            reasons.append("Invalid id: must be a non-empty string")
        if not isinstance(record["category"], str) or not record["category"].strip():
            reasons.append("Invalid category: must be a non-empty string")
        if record["source"] not in SOURCES:
            reasons.append("Invalid source: expected salesforce, jira, or servicenow")
        if record["status"] not in STATUSES:
            reasons.append("Invalid status: expected open or closed")
        try:
            parse_date(record["created_at"])
        except (ValueError, TypeError):
            reasons.append("Invalid date: expected a real date in exact YYYY-MM-DD format")
        changes = record["owner_changes"]
        if type(changes) is not int or changes < 0:
            reasons.append("Invalid owner_changes: must be a non-negative integer, excluding booleans")
        if reasons:
            rejected.append({"index": index, "reasons": reasons})
        else:
            valid.append(record)
    return {"valid": valid, "rejected": rejected}


# Run this file to see an example. Change the sample input to practice.
if __name__ == "__main__":
    records = [
        {"id": "A1", "source": "salesforce", "status": "open", "category": "access", "created_at": "2026-09-01", "owner_changes": 4},
        {"id": "", "source": "jira", "status": "open", "category": "billing", "created_at": "2026-09-22", "owner_changes": 0},
    ]
    print("Output:", validate_records(records))
