"""Command-line entry points used in the README and walkthrough."""

import argparse
import json
import logging
from pathlib import Path

import httpx

from agentiq.connector import ConnectorError, collect_pages
from agentiq.data import ingest, load_records, sample_records
from agentiq.settings import Settings
from agentiq.storage import Store


def main():
    parser = argparse.ArgumentParser(description="AgentIQ assessment service")
    sub = parser.add_subparsers(dest="command", required=True)
    sample = sub.add_parser("sample")
    sample.add_argument("--output", default="data/sample_records.json")
    ingest_parser = sub.add_parser("ingest")
    ingest_parser.add_argument("file")
    sub.add_parser("analyze")
    sub.add_parser("sync")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s %(message)s")
    # HTTPX's informational request logs can contain URLs; keep them disabled.
    logging.getLogger("httpx").setLevel(logging.CRITICAL)
    logging.getLogger("httpcore").setLevel(logging.CRITICAL)
    try:
        if args.command == "sample":
            path = Path(args.output)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(sample_records(), indent=2) + "\n", encoding="utf-8")
            print(f"Created {path} with 22 records")
            return 0
        settings = Settings.from_env()
        store = Store(settings.database_path)
        if args.command in ("ingest", "sync"):
            if args.command == "ingest":
                records = load_records(args.file)
            else:
                with httpx.Client() as client:
                    records = collect_pages(client, settings.external_api_url, settings.api_token)
            result = ingest(records)
            store.upsert(result["records"])
            print(json.dumps({k: v for k, v in result.items() if k != "records"}, indent=2))
        else:
            print(json.dumps(store.create_run(settings.reference_at, settings.handoff_threshold), indent=2))
        return 0
    except (OSError, ValueError, ConnectorError) as error:
        print(f"Error: {error}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
