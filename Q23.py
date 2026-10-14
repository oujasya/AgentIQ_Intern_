"""Q23: Summarize validated, deduplicated records.
Complexity: O(n) time and O(c) output memory for c bounded-size categories.
Lesson: Empty input still needs all predefined zero-valued keys.
"""


def summarize(records):
    by_status = {"open": 0, "closed": 0}
    by_source = {"salesforce": 0, "jira": 0, "servicenow": 0}
    by_category = {}
    for record in records:
        status = record["status"]
        source = record["source"]
        category = record["category"]
        by_status[status] += 1
        by_source[source] += 1
        # get uses zero the first time this category appears.
        by_category[category] = by_category.get(category, 0) + 1
    return {"total": len(records), "by_status": by_status,
            "by_source": by_source, "by_category": by_category}


# Run this file to see an example. Change the sample input to practice.
if __name__ == "__main__":
    records = [
        {"source": "salesforce", "status": "open", "category": "access"},
        {"source": "jira", "status": "closed", "category": "billing"},
    ]
    print("Output:", summarize(records))
