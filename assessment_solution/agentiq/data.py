"""Questions 1-5: reproducible samples and a reusable ingestion pipeline."""

import json
import logging
import re
from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger("agentiq")
FIELDS = ("id", "source", "title", "status", "priority", "created_at",
          "resolved_at", "owner_changes", "category")
SOURCES = {"Salesforce", "ServiceNow", "Jira"}
STATUS_MAP = {"closed": "resolved", "resolved": "resolved", "done": "resolved",
              "new": "open", "open": "open", "in progress": "open"}
UTC_PATTERN = re.compile(
    r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,6})?(?:Z|\+00:00)"
)


def sample_records():
    """Q1: 21 base records plus one exact duplicate; four invalid rows."""
    titles = ["Password reset request", "VPN connection failure",
              "Account access request", "Email delivery issue",
              "Software installation request", "Dashboard loading failure",
              "Password reset follow-up"]
    statuses = ["Open", "Resolved", "New", "Closed", "In Progress", "Done", " open "]
    categories = ["Access Management", "Network", "Access Management", "Email",
                  "Software", "Application", "Access Management"]
    records = []
    for source_index, source in enumerate(["Salesforce", "ServiceNow", "Jira"]):
        for index in range(7):
            records.append({
                "id": f"{source_index + 1}00{index + 1}", "source": source,
                "title": titles[index], "status": statuses[index],
                "priority": ["High", "Medium", "Low"][index % 3],
                "created_at": f"2026-10-{10 + index:02d}T09:00:00Z",
                "resolved_at": (f"2026-10-{11 + index:02d}T11:00:00Z"
                                if index in (1, 3, 5) else None),
                "owner_changes": [0, 1, 3, 4, 2, 5, 1][index],
                "category": categories[index],
            })
    records[7]["id"] = records[0]["id"]
    records[14]["id"] = records[0]["id"]
    del records[4]["priority"]
    del records[11]["title"]
    records[16]["created_at"] = "not-a-timestamp"
    records[19]["owner_changes"] = -2
    records.append(records[0].copy())
    return records


def load_records(file_path):
    """Q2: file/JSON failures raise; an empty JSON array returns []."""
    path = Path(file_path)
    try:
        with path.open(encoding="utf-8") as stream:
            records = json.load(stream)
    except FileNotFoundError as error:
        raise FileNotFoundError(f"Records file not found: {path}") from error
    except json.JSONDecodeError as error:
        raise ValueError(f"Invalid JSON at line {error.lineno}, column {error.colno}") from error
    except UnicodeDecodeError as error:
        raise ValueError("Records file must use UTF-8 encoding") from error
    if not isinstance(records, list):
        raise ValueError("Expected a JSON array of records")
    return records


def parse_utc(value):
    """Accept explicit UTC ISO timestamps and reject impossible dates."""
    if not isinstance(value, str) or UTC_PATTERN.fullmatch(value) is None:
        raise ValueError("Expected a UTC timestamp such as 2026-10-10T09:00:00Z")
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    return parsed.astimezone(timezone.utc)


def validate_record(record):
    """Q3: accumulate all structural errors without mutating input."""
    if not isinstance(record, dict):
        return ["Record must be a JSON object"]
    errors = [f"Missing required field: {field}" for field in FIELDS if field not in record]
    for field in ("id", "title", "status", "priority", "category"):
        if field in record:
            value = record[field]
            if not isinstance(value, str) or not value.strip():
                errors.append(f"{field} must be a non-empty string")
    if "source" in record:
        source = record["source"]
        if not isinstance(source, str) or source not in SOURCES:
            errors.append("source must be Salesforce, ServiceNow, or Jira")
    for field in ("created_at", "resolved_at"):
        if field not in record or (field == "resolved_at" and record[field] is None):
            continue
        try:
            parse_utc(record[field])
        except ValueError:
            errors.append(f"{field} must be a valid UTC timestamp")
    if "owner_changes" in record:
        value = record["owner_changes"]
        if isinstance(value, bool) or not isinstance(value, int):
            errors.append("owner_changes must be an integer")
        elif value < 0:
            errors.append("owner_changes must be greater than or equal to 0")
    return errors


def validate_records(records):
    if not isinstance(records, list):
        raise ValueError("Expected a list of records")
    accepted, rejected = [], []
    for index, record in enumerate(records):
        reasons = validate_record(record)
        if reasons:
            rejected.append({"input_index": index, "record": record, "reasons": reasons})
        else:
            accepted.append(record)
    return accepted, rejected


def normalize_status(value):
    """Q4: unknown statuses raise instead of silently assigning a state."""
    if not isinstance(value, str):
        raise ValueError("status must be a string")
    key = value.strip().casefold()
    if key not in STATUS_MAP:
        raise ValueError("Unknown status; expected New, Open, In Progress, Closed, Resolved, or Done")
    return STATUS_MAP[key]


def normalize_record(record):
    normalized = record.copy()
    normalized["status"] = normalize_status(record["status"])
    for field in ("created_at", "resolved_at"):
        if normalized[field] is not None:
            normalized[field] = parse_utc(normalized[field]).isoformat().replace("+00:00", "Z")
    return normalized


def deduplicate(records):
    """Q5: first valid occurrence wins within a batch; preserve input order."""
    seen, unique, duplicates = set(), [], []
    for record in records:
        key = (record["source"], record["id"])
        if key in seen:
            duplicates.append({"source": key[0], "id": key[1]})
        else:
            seen.add(key)
            unique.append(record)
    return unique, duplicates


def ingest(records):
    """Shared CLI/API pipeline: validate -> normalize -> deduplicate."""
    if not isinstance(records, list):
        raise ValueError("Expected a list of records")
    normalized, rejected = [], []
    for index, record in enumerate(records):
        reasons = validate_record(record)
        if not reasons:
            try:
                normalized.append(normalize_record(record))
            except ValueError as error:
                reasons = [str(error)]
        if reasons:
            rejected.append({"input_index": index, "record": record, "reasons": reasons})
            # Log fixed diagnostic text, never the record or raw field values.
            logger.warning("validation_failed input_index=%d reasons=%s", index, "; ".join(reasons))
    unique, duplicates = deduplicate(normalized)
    result = {"records": unique, "rejected": rejected, "duplicates": duplicates,
              "input_count": len(records), "accepted_count": len(unique),
              "valid_count": len(normalized), "rejected_count": len(rejected),
              "duplicate_count": len(duplicates)}
    logger.info("ingestion input=%d accepted=%d rejected=%d duplicates=%d",
                len(records), len(unique), len(rejected), len(duplicates))
    return result
