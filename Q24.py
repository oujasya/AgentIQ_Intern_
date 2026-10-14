"""Q24: Find aging work and repeated handoffs.
Complexity: O(n) time and worst-case output memory with bounded-size fields.
Lesson: Exactly 7 days or 3 changes does not qualify; avoid elif here.
"""
from Q21 import parse_date


def find_findings(records, reference_date):
    aging = []
    handoff = []
    ref_date = parse_date(reference_date)
    for record in records:
        created_date = parse_date(record["created_at"])
        age = (ref_date - created_date).days
        if record["status"] == "open" and age > 7:
            aging.append({
                "source": record["source"], "id": record["id"],
                "observed_value": age, "threshold": 7,
                "reason": f"Open record is {age} days old",
            })
        # Separate if: a record can produce both findings.
        if record["owner_changes"] > 3:
            handoff.append({
                "source": record["source"], "id": record["id"],
                "observed_value": record["owner_changes"], "threshold": 3,
                "reason": "More than 3 owner changes",
            })
    return {"aging": aging, "handoff": handoff}


# Run this file to see an example. Change the sample input to practice.
if __name__ == "__main__":
    records = [{"id": "A1", "source": "salesforce", "status": "open", "category": "access", "created_at": "2026-09-01", "owner_changes": 4}]
    reference_date = "2026-09-30"
    print("Output:", find_findings(records, reference_date))
