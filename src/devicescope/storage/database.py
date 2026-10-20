
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator


SCHEMA = """
CREATE TABLE IF NOT EXISTS devices (
    id TEXT PRIMARY KEY,
    device_type TEXT NOT NULL,
    name TEXT,
    identifiers_json TEXT NOT NULL,
    attributes_json TEXT NOT NULL,
    first_seen TEXT NOT NULL,
    last_seen TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS observations (
    id TEXT PRIMARY KEY,
    source TEXT NOT NULL,
    kind TEXT NOT NULL,
    observed_at TEXT NOT NULL,
    device_id TEXT,
    data_json TEXT NOT NULL,
    FOREIGN KEY (device_id) REFERENCES devices(id)
        ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS evidence (
    id TEXT PRIMARY KEY,
    subject_id TEXT NOT NULL,
    claim TEXT NOT NULL,
    value TEXT NOT NULL,
    confidence REAL NOT NULL
        CHECK(confidence >= 0 AND confidence <= 1),
    rationale TEXT,
    created_at TEXT NOT NULL,
    FOREIGN KEY (subject_id) REFERENCES devices(id)
        ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS evidence_observations (
    evidence_id TEXT NOT NULL,
    observation_id TEXT NOT NULL,
    PRIMARY KEY (evidence_id, observation_id),
    FOREIGN KEY (evidence_id) REFERENCES evidence(id)
        ON DELETE CASCADE,
    FOREIGN KEY (observation_id) REFERENCES observations(id)
        ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS relationships (
    id TEXT PRIMARY KEY,
    source_id TEXT NOT NULL,
    target_id TEXT NOT NULL,
    relation_type TEXT NOT NULL,
    confidence REAL NOT NULL
        CHECK(confidence >= 0 AND confidence <= 1),
    attributes_json TEXT NOT NULL,
    first_seen TEXT NOT NULL,
    last_seen TEXT NOT NULL,
    FOREIGN KEY (source_id) REFERENCES devices(id)
        ON DELETE CASCADE,
    FOREIGN KEY (target_id) REFERENCES devices(id)
        ON DELETE CASCADE,
    CHECK(source_id != target_id)
);

CREATE TABLE IF NOT EXISTS relationship_evidence (
    relationship_id TEXT NOT NULL,
    evidence_id TEXT NOT NULL,
    PRIMARY KEY (relationship_id, evidence_id),
    FOREIGN KEY (relationship_id) REFERENCES relationships(id)
        ON DELETE CASCADE,
    FOREIGN KEY (evidence_id) REFERENCES evidence(id)
        ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_observations_device
    ON observations(device_id);

CREATE INDEX IF NOT EXISTS idx_observations_time
    ON observations(observed_at);

CREATE INDEX IF NOT EXISTS idx_evidence_subject
    ON evidence(subject_id);

CREATE INDEX IF NOT EXISTS idx_relationships_source
    ON relationships(source_id);

CREATE INDEX IF NOT EXISTS idx_relationships_target
    ON relationships(target_id);
"""


class ClosingConnection(sqlite3.Connection):
    """SQLite connection that closes when its context exits."""

    def __exit__(self, exc_type, exc_value, traceback):
        try:
            return super().__exit__(exc_type, exc_value, traceback)
        finally:
            self.close()


class Database:
    """Manage DeviceScope's SQLite database."""

    def __init__(
        self,
        path: str | Path = "devicescope.db",
    ) -> None:
        self.path = str(path)
        self._initialized = False

    def connect(self) -> sqlite3.Connection:
        """Open a connection with foreign keys enabled."""
        connection = sqlite3.connect(
            self.path,
            factory=ClosingConnection,
        )
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    def initialize(self) -> None:
        """Create tables and indexes if they do not exist."""
        with self.connect() as connection:
            connection.executescript(SCHEMA)

        self._initialized = True

    @contextmanager
    def transaction(self) -> Iterator[sqlite3.Connection]:
        """Commit on success, roll back on failure, and close always."""
        connection = self.connect()

        try:
            with connection:
                yield connection
        finally:
            connection.close()
