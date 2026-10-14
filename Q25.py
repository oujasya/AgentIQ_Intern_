"""Q25: Runnable JSON report generator.
Complexity: Expected O(n + b) time and O(n + b) memory for n bounded-size rows
and b input/output JSON characters; the full input and report reside in memory.
Lesson: Validate input before opening the destination; otherwise errors can
destroy a previous report. Atomic replacement also protects against write errors.
"""
import json
import os
from pathlib import Path
import sys
import tempfile

from Q21 import validate_records
from Q22 import deduplicate
from Q23 import summarize
from Q24 import find_findings

REFERENCE_DATE = "2026-09-30"


def build_report(records):
    if not isinstance(records, list):
        raise ValueError("top-level JSON value must be an array")
    validation = validate_records(records)
    valid_records = validation["valid"]
    rejected_records = validation["rejected"]
    deduplication = deduplicate(valid_records)
    unique_records = deduplication["records"]
    duplicates_removed = deduplication["duplicates_removed"]
    summary = summarize(unique_records)
    findings = find_findings(unique_records, REFERENCE_DATE)
    return {
        "input_count": len(records),
        "valid_count": len(valid_records),
        "rejected_count": len(rejected_records),
        "duplicates_removed": duplicates_removed,
        "summary": summary,
        "findings": findings,
        "rejections": rejected_records,
    }


def write_report(input_path, output_path):
    with open(input_path, encoding="utf-8") as stream:
        records = json.load(stream)
    report = build_report(records)
    destination = Path(output_path)
    temporary_path = None
    try: 
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=destination.parent,
                                         prefix=".report-", suffix=".tmp", delete=False) as stream:
            temporary_path = stream.name
            json.dump(report, stream, indent=4, ensure_ascii=False)
            stream.write("\n")
        os.replace(temporary_path, destination)
    finally:
        if temporary_path is not None and os.path.exists(temporary_path):
            os.unlink(temporary_path)
    return report


def main(argv=None):
    # Exclude sys.argv[0], which is the program name.
    arguments = sys.argv[1:] if argv is None else argv
    if len(arguments) != 2:
        print("Usage: python Q25.py records.json output.json", file=sys.stderr)
        return 1
    input_file = arguments[0]
    output_file = arguments[1]
    try:
        write_report(input_file, output_file)
    except FileNotFoundError as error:
        print(f"Error: File or directory not found: {error.filename}", file=sys.stderr)
        return 1
    except json.JSONDecodeError:
        print("Error: Input file contains malformed JSON.", file=sys.stderr)
        return 1
    except (OSError, ValueError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1
    print(f"Report written to {output_file}")
    return 0


if __name__ == "__main__":
    if len(sys.argv) == 1:
        # Simple sample: run Q25.py without typing any command-line arguments.
        records = [
            {"id": "A1", "source": "salesforce", "status": "open",
             "category": "access", "created_at": "2026-09-01", "owner_changes": 4},
            {"id": "A1", "source": "salesforce", "status": "closed",
             "category": "access", "created_at": "2026-09-01", "owner_changes": 9},
        ]
        print("Output:")
        print(json.dumps(build_report(records), indent=4))
    else:
        sys.exit(main())
