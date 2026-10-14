"""Q22: Deduplicate validated records using (source, id).
Complexity: Expected O(n) time and O(u) memory for u unique bounded-size keys.
Lesson: An id alone cannot distinguish records from different systems.
"""


def deduplicate(records):
    seen = set()
    result = []
    duplicates_removed = 0
    for record in records:
        key = (record["source"], record["id"])
        if key in seen:
            duplicates_removed += 1
        else:
            seen.add(key)
            result.append(record)
    return {"records": result, "duplicates_removed": duplicates_removed}


# Run this file to see an example. Change the sample input to practice.
if __name__ == "__main__":
    records = [
        {"source": "salesforce", "id": "A1", "owner_changes": 4},
        {"source": "jira", "id": "A1", "owner_changes": 1},
        {"source": "salesforce", "id": "A1", "owner_changes": 9},
    ]
    print("Output:", deduplicate(records))
