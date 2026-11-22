import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from app.core.security import ensure_private_directory, ensure_private_file


_SCHEMA = """
CREATE TABLE IF NOT EXISTS investigations (
    id TEXT PRIMARY KEY,
    fixture_id TEXT NOT NULL,
    report TEXT NOT NULL,
    status TEXT NOT NULL,
    verification_outcome TEXT NOT NULL,
    execution_status TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    latest_event_sequence INTEGER NOT NULL DEFAULT 0,
    version INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS investigation_events (
    investigation_id TEXT NOT NULL REFERENCES investigations(id) ON DELETE CASCADE,
    sequence INTEGER NOT NULL,
    type TEXT NOT NULL,
    created_at TEXT NOT NULL,
    data_json TEXT NOT NULL,
    PRIMARY KEY (investigation_id, sequence)
);
CREATE TABLE IF NOT EXISTS evidence_items (
    id TEXT PRIMARY KEY,
    investigation_id TEXT NOT NULL REFERENCES investigations(id) ON DELETE CASCADE,
    kind TEXT NOT NULL,
    content_type TEXT NOT NULL,
    producer_kind TEXT NOT NULL,
    producer_version TEXT NOT NULL,
    source_fixture_id TEXT,
    title TEXT NOT NULL,
    summary TEXT NOT NULL,
    source_ref_json TEXT
);
CREATE INDEX IF NOT EXISTS ix_evidence_investigation ON evidence_items(investigation_id);
CREATE TABLE IF NOT EXISTS idempotency_records (
    key TEXT PRIMARY KEY,
    request_hash TEXT NOT NULL,
    investigation_id TEXT NOT NULL UNIQUE REFERENCES investigations(id) ON DELETE CASCADE
);
"""


class Database:
    def __init__(self, data_directory: Path) -> None:
        self.data_directory = data_directory
        self.path = data_directory / "bugpilot.sqlite3"

    def initialize(self) -> None:
        ensure_private_directory(self.data_directory)
        ensure_private_file(self.path)
        connection = self.connect()
        try:
            connection.executescript(_SCHEMA)
            connection.execute("PRAGMA journal_mode = WAL")
        finally:
            connection.close()

    def connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path, timeout=10, isolation_level=None)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("PRAGMA busy_timeout = 10000")
        return connection

    @contextmanager
    def transaction(self) -> Iterator[sqlite3.Connection]:
        connection = self.connect()
        try:
            connection.execute("BEGIN IMMEDIATE")
            yield connection
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()