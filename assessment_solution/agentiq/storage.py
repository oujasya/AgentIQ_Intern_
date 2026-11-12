"""Q16-20: SQLite upserts and immutable per-run findings."""

import json
import logging
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from agentiq.analysis import analyze

logger = logging.getLogger("agentiq")

SCHEMA = """
CREATE TABLE IF NOT EXISTS records (
    source TEXT NOT NULL CHECK (source IN ('Salesforce','ServiceNow','Jira')),
    id TEXT NOT NULL,
    title TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('open','resolved')),
    priority TEXT NOT NULL,
    created_at TEXT NOT NULL,
    resolved_at TEXT,
    owner_changes INTEGER NOT NULL CHECK (owner_changes >= 0),
    category TEXT NOT NULL,
    PRIMARY KEY (source, id)
);
CREATE TABLE IF NOT EXISTS runs (
    run_id TEXT PRIMARY KEY,
    executed_at TEXT NOT NULL,
    reference_at TEXT NOT NULL,
    handoff_threshold INTEGER NOT NULL,
    records_json TEXT NOT NULL,
    report_json TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS findings (
    run_id TEXT NOT NULL REFERENCES runs(run_id) ON DELETE CASCADE,
    ordinal INTEGER NOT NULL,
    finding_json TEXT NOT NULL,
    PRIMARY KEY (run_id, ordinal)
);
"""


class Store:
    def __init__(self, path):
        if str(path) == ":memory:":
            raise ValueError("Use a file-backed database; each operation opens its own connection")
        self.path = str(path)
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as connection:
            connection.executescript(SCHEMA)

    @contextmanager
    def connect(self):
        connection = sqlite3.connect(self.path, timeout=10)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        try:
            with connection:
                yield connection
        finally:
            connection.close()

    def upsert(self, records):
        """Latest accepted import replaces mutable values for an existing key."""
        sql = """
        INSERT INTO records
        (source,id,title,status,priority,created_at,resolved_at,owner_changes,category)
        VALUES (:source,:id,:title,:status,:priority,:created_at,:resolved_at,:owner_changes,:category)
        ON CONFLICT(source,id) DO UPDATE SET
            title=excluded.title, status=excluded.status, priority=excluded.priority,
            created_at=excluded.created_at, resolved_at=excluded.resolved_at,
            owner_changes=excluded.owner_changes, category=excluded.category
        """
        with self.connect() as connection:
            connection.executemany(sql, records)

    def list_records(self, source=None, status=None, limit=50, offset=0):
        if not 1 <= limit <= 100 or offset < 0:
            raise ValueError("limit must be 1-100 and offset must be non-negative")
        clauses, parameters = [], []
        for column, value in (("source", source), ("status", status)):
            if value is not None:
                clauses.append(f"{column} = ?")
                parameters.append(value)
        where = " WHERE " + " AND ".join(clauses) if clauses else ""
        with self.connect() as connection:
            total = connection.execute("SELECT COUNT(*) FROM records" + where, parameters).fetchone()[0]
            rows = connection.execute(
                "SELECT * FROM records" + where + " ORDER BY source, id LIMIT ? OFFSET ?",
                [*parameters, limit, offset],
            ).fetchall()
        return {"total": total, "limit": limit, "offset": offset, "records": [dict(r) for r in rows]}

    def all_records(self):
        with self.connect() as connection:
            return [dict(r) for r in connection.execute("SELECT * FROM records ORDER BY source, id")]

    def create_run(self, reference_at, handoff_threshold):
        # A single transaction makes the snapshot and its findings consistent.
        with self.connect() as connection:
            connection.execute("BEGIN")
            records = [dict(r) for r in connection.execute("SELECT * FROM records ORDER BY source, id")]
            report = analyze(records, reference_at, handoff_threshold)
            run_id = str(uuid4())
            connection.execute(
                "INSERT INTO runs VALUES (?, ?, ?, ?, ?, ?)",
                (run_id, datetime.now(timezone.utc).isoformat(), reference_at,
                 handoff_threshold, json.dumps(records), json.dumps(report)),
            )
            connection.executemany(
                "INSERT INTO findings VALUES (?, ?, ?)",
                [(run_id, index, json.dumps(finding)) for index, finding in enumerate(report["findings"])],
            )
        logger.info("analysis_completed run_id=%s accepted=%d findings=%d", run_id, len(records), len(report["findings"]))
        return {"run_id": run_id, "reference_at": reference_at,
                "handoff_threshold": handoff_threshold, **report}

    def get_findings(self, run_id):
        with self.connect() as connection:
            run = connection.execute(
                "SELECT reference_at, handoff_threshold FROM runs WHERE run_id = ?", (run_id,)
            ).fetchone()
            if run is None:
                return None
            findings = connection.execute(
                "SELECT finding_json FROM findings WHERE run_id = ? ORDER BY ordinal", (run_id,)
            ).fetchall()
        return {"run_id": run_id, **dict(run), "findings": [json.loads(r[0]) for r in findings]}
