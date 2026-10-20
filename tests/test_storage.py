
import tempfile
import unittest
from pathlib import Path

from devicescope.models import (
    Device,
    Evidence,
    Observation,
    Relationship,
)
from devicescope.storage import Database, Repository


class TestStorage(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        db_path = Path(self.temp_dir.name) / "test.db"

        self.repository = Repository(Database(db_path))

        self.device_a = Device(
            device_type="network_neighbor",
            name="test-device-a",
            identifiers={"ip": "10.68.0.214"},
        )
        self.device_b = Device(
            device_type="network_neighbor",
            name="test-device-b",
            identifiers={"ip": "10.68.0.1"},
        )

        self.repository.save_device(self.device_a)
        self.repository.save_device(self.device_b)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_saves_and_retrieves_device(self):
        result = self.repository.get_device(self.device_a.id)

        self.assertIsNotNone(result)
        self.assertEqual(result.name, "test-device-a")
        self.assertEqual(
            result.identifiers["ip"],
            "10.68.0.214",
        )

    def test_missing_device_returns_none(self):
        self.assertIsNone(
            self.repository.get_device("missing-device")
        )

    def test_lists_devices(self):
        devices = self.repository.list_devices()

        self.assertEqual(len(devices), 2)

    def test_saves_and_retrieves_observation(self):
        observation = Observation(
            source="windows_neighbor_table",
            kind="neighbor_entry",
            device_id=self.device_a.id,
            data={
                "ip": "10.68.0.214",
                "state": "Stale",
            },
        )

        self.repository.save_observation(observation)
        result = self.repository.get_observation(observation.id)

        self.assertIsNotNone(result)
        self.assertEqual(result.device_id, self.device_a.id)
        self.assertEqual(result.data["state"], "Stale")

    def test_lists_observations_by_device(self):
        observation = Observation(
            source="test",
            kind="sample",
            device_id=self.device_a.id,
        )
        self.repository.save_observation(observation)

        results = self.repository.list_observations(
            self.device_a.id
        )

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].id, observation.id)

    def test_saves_and_retrieves_evidence(self):
        observation = Observation(
            source="test",
            kind="sample",
            device_id=self.device_a.id,
        )
        self.repository.save_observation(observation)

        evidence = Evidence(
            subject_id=self.device_a.id,
            claim="manufacturer",
            value="Example Manufacturer",
            confidence=0.85,
            observation_ids=[observation.id],
            rationale="Test evidence.",
        )

        self.repository.save_evidence(evidence)
        result = self.repository.get_evidence(evidence.id)

        self.assertIsNotNone(result)
        self.assertEqual(result.value, "Example Manufacturer")
        self.assertEqual(
            result.observation_ids,
            [observation.id],
        )

    def test_saves_and_retrieves_relationship(self):
        evidence = Evidence(
            subject_id=self.device_a.id,
            claim="association",
            value="test association",
            confidence=0.7,
        )
        self.repository.save_evidence(evidence)

        relationship = Relationship(
            source_id=self.device_a.id,
            target_id=self.device_b.id,
            relation_type="associated_with",
            confidence=0.7,
            evidence_ids=[evidence.id],
            attributes={"origin": "test"},
        )

        self.repository.save_relationship(relationship)
        result = self.repository.get_relationship(relationship.id)

        self.assertIsNotNone(result)
        self.assertEqual(
            result.relation_type,
            "associated_with",
        )
        self.assertEqual(result.evidence_ids, [evidence.id])
        self.assertEqual(result.attributes["origin"], "test")

    def test_rejects_observation_for_missing_device(self):
        observation = Observation(
            source="test",
            kind="sample",
            device_id="missing-device",
        )

        with self.assertRaises(Exception):
            self.repository.save_observation(observation)

        self.assertIsNone(
            self.repository.get_observation(observation.id)
        )

    def test_rejects_evidence_for_missing_subject(self):
        evidence = Evidence(
            subject_id="missing-device",
            claim="manufacturer",
            value="Unknown",
            confidence=0.5,
        )

        with self.assertRaises(Exception):
            self.repository.save_evidence(evidence)

        self.assertIsNone(
            self.repository.get_evidence(evidence.id)
        )

    def test_rejects_relationship_for_missing_device(self):
        relationship = Relationship(
            source_id=self.device_a.id,
            target_id="missing-device",
            relation_type="associated_with",
            confidence=0.5,
        )

        with self.assertRaises(Exception):
            self.repository.save_relationship(relationship)

        self.assertIsNone(
            self.repository.get_relationship(relationship.id)
        )


if __name__ == "__main__":
    unittest.main()
