
import json
from datetime import datetime
from typing import Any

from devicescope.models import (
    Device,
    Evidence,
    Observation,
    Relationship,
)
from devicescope.storage.database import Database


def _json_dump(value: Any) -> str:
    return json.dumps(value, sort_keys=True)


def _json_load(value: str) -> Any:
    return json.loads(value)


def _datetime(value: str) -> datetime:
    return datetime.fromisoformat(value)


class Repository:
    """Persist and retrieve DeviceScope models."""

    def __init__(self, database: Database) -> None:
        self.database = database
        self.database.initialize()

    def save_device(self, device: Device) -> None:
        with self.database.transaction() as connection:
            connection.execute(
                """
                INSERT INTO devices (
                    id, device_type, name, identifiers_json,
                    attributes_json, first_seen, last_seen
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    device_type = excluded.device_type,
                    name = excluded.name,
                    identifiers_json = excluded.identifiers_json,
                    attributes_json = excluded.attributes_json,
                    first_seen = excluded.first_seen,
                    last_seen = excluded.last_seen
                """,
                (
                    device.id,
                    device.device_type,
                    device.name,
                    _json_dump(device.identifiers),
                    _json_dump(device.attributes),
                    device.first_seen.isoformat(),
                    device.last_seen.isoformat(),
                ),
            )

    def get_device(self, device_id: str) -> Device | None:
        with self.database.connect() as connection:
            row = connection.execute(
                "SELECT * FROM devices WHERE id = ?",
                (device_id,),
            ).fetchone()

        if row is None:
            return None

        return Device(
            id=row["id"],
            device_type=row["device_type"],
            name=row["name"],
            identifiers=_json_load(row["identifiers_json"]),
            attributes=_json_load(row["attributes_json"]),
            first_seen=_datetime(row["first_seen"]),
            last_seen=_datetime(row["last_seen"]),
        )

    def list_devices(self) -> list[Device]:
        with self.database.connect() as connection:
            rows = connection.execute(
                "SELECT id FROM devices ORDER BY first_seen, id"
            ).fetchall()

        devices = [
            self.get_device(row["id"])
            for row in rows
        ]
        return [device for device in devices if device is not None]

    def save_observation(self, observation: Observation) -> None:
        with self.database.transaction() as connection:
            connection.execute(
                """
                INSERT INTO observations (
                    id, source, kind, observed_at, device_id, data_json
                ) VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    source = excluded.source,
                    kind = excluded.kind,
                    observed_at = excluded.observed_at,
                    device_id = excluded.device_id,
                    data_json = excluded.data_json
                """,
                (
                    observation.id,
                    observation.source,
                    observation.kind,
                    observation.observed_at.isoformat(),
                    observation.device_id,
                    _json_dump(observation.data),
                ),
            )

    def get_observation(
        self,
        observation_id: str,
    ) -> Observation | None:
        with self.database.connect() as connection:
            row = connection.execute(
                "SELECT * FROM observations WHERE id = ?",
                (observation_id,),
            ).fetchone()

        if row is None:
            return None

        return Observation(
            id=row["id"],
            source=row["source"],
            kind=row["kind"],
            observed_at=_datetime(row["observed_at"]),
            device_id=row["device_id"],
            data=_json_load(row["data_json"]),
        )

    def list_observations(
        self,
        device_id: str | None = None,
    ) -> list[Observation]:
        with self.database.connect() as connection:
            if device_id is None:
                rows = connection.execute(
                    "SELECT id FROM observations ORDER BY observed_at, id"
                ).fetchall()
            else:
                rows = connection.execute(
                    """
                    SELECT id FROM observations
                    WHERE device_id = ?
                    ORDER BY observed_at, id
                    """,
                    (device_id,),
                ).fetchall()

        return [
            self.get_observation(row["id"])
            for row in rows
        ]

    def save_evidence(self, evidence: Evidence) -> None:
        with self.database.transaction() as connection:
            connection.execute(
                """
                INSERT INTO evidence (
                    id, subject_id, claim, value, confidence,
                    rationale, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    subject_id = excluded.subject_id,
                    claim = excluded.claim,
                    value = excluded.value,
                    confidence = excluded.confidence,
                    rationale = excluded.rationale,
                    created_at = excluded.created_at
                """,
                (
                    evidence.id,
                    evidence.subject_id,
                    evidence.claim,
                    evidence.value,
                    evidence.confidence,
                    evidence.rationale,
                    evidence.created_at.isoformat(),
                ),
            )

            connection.execute(
                "DELETE FROM evidence_observations WHERE evidence_id = ?",
                (evidence.id,),
            )

            connection.executemany(
                """
                INSERT INTO evidence_observations (
                    evidence_id, observation_id
                ) VALUES (?, ?)
                """,
                [
                    (evidence.id, observation_id)
                    for observation_id in evidence.observation_ids
                ],
            )

    def get_evidence(self, evidence_id: str) -> Evidence | None:
        with self.database.connect() as connection:
            row = connection.execute(
                "SELECT * FROM evidence WHERE id = ?",
                (evidence_id,),
            ).fetchone()

            if row is None:
                return None

            observations = connection.execute(
                """
                SELECT observation_id
                FROM evidence_observations
                WHERE evidence_id = ?
                ORDER BY observation_id
                """,
                (evidence_id,),
            ).fetchall()

        return Evidence(
            id=row["id"],
            subject_id=row["subject_id"],
            claim=row["claim"],
            value=row["value"],
            confidence=row["confidence"],
            rationale=row["rationale"],
            created_at=_datetime(row["created_at"]),
            observation_ids=[
                item["observation_id"] for item in observations
            ],
        )

    def list_evidence(
        self,
        subject_id: str | None = None,
    ) -> list[Evidence]:
        with self.database.connect() as connection:
            if subject_id is None:
                rows = connection.execute(
                    "SELECT id FROM evidence ORDER BY created_at, id"
                ).fetchall()
            else:
                rows = connection.execute(
                    """
                    SELECT id FROM evidence
                    WHERE subject_id = ?
                    ORDER BY created_at, id
                    """,
                    (subject_id,),
                ).fetchall()

        return [
            self.get_evidence(row["id"])
            for row in rows
        ]

    def save_relationship(self, relationship: Relationship) -> None:
        with self.database.transaction() as connection:
            connection.execute(
                """
                INSERT INTO relationships (
                    id, source_id, target_id, relation_type, confidence,
                    attributes_json, first_seen, last_seen
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    source_id = excluded.source_id,
                    target_id = excluded.target_id,
                    relation_type = excluded.relation_type,
                    confidence = excluded.confidence,
                    attributes_json = excluded.attributes_json,
                    first_seen = excluded.first_seen,
                    last_seen = excluded.last_seen
                """,
                (
                    relationship.id,
                    relationship.source_id,
                    relationship.target_id,
                    relationship.relation_type,
                    relationship.confidence,
                    _json_dump(relationship.attributes),
                    relationship.first_seen.isoformat(),
                    relationship.last_seen.isoformat(),
                ),
            )

            connection.execute(
                """
                DELETE FROM relationship_evidence
                WHERE relationship_id = ?
                """,
                (relationship.id,),
            )

            connection.executemany(
                """
                INSERT INTO relationship_evidence (
                    relationship_id, evidence_id
                ) VALUES (?, ?)
                """,
                [
                    (relationship.id, evidence_id)
                    for evidence_id in relationship.evidence_ids
                ],
            )

    def get_relationship(
        self,
        relationship_id: str,
    ) -> Relationship | None:
        with self.database.connect() as connection:
            row = connection.execute(
                "SELECT * FROM relationships WHERE id = ?",
                (relationship_id,),
            ).fetchone()

            if row is None:
                return None

            evidence_rows = connection.execute(
                """
                SELECT evidence_id
                FROM relationship_evidence
                WHERE relationship_id = ?
                ORDER BY evidence_id
                """,
                (relationship_id,),
            ).fetchall()

        return Relationship(
            id=row["id"],
            source_id=row["source_id"],
            target_id=row["target_id"],
            relation_type=row["relation_type"],
            confidence=row["confidence"],
            attributes=_json_load(row["attributes_json"]),
            first_seen=_datetime(row["first_seen"]),
            last_seen=_datetime(row["last_seen"]),
            evidence_ids=[
                item["evidence_id"] for item in evidence_rows
            ],
        )

    def list_relationships(
        self,
        device_id: str | None = None,
    ) -> list[Relationship]:
        with self.database.connect() as connection:
            if device_id is None:
                rows = connection.execute(
                    "SELECT id FROM relationships ORDER BY first_seen, id"
                ).fetchall()
            else:
                rows = connection.execute(
                    """
                    SELECT id FROM relationships
                    WHERE source_id = ? OR target_id = ?
                    ORDER BY first_seen, id
                    """,
                    (device_id, device_id),
                ).fetchall()

        return [
            self.get_relationship(row["id"])
            for row in rows
        ]
