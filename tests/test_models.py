import unittest
from datetime import datetime

from devicescope.models import (
    Device,
    Evidence,
    Observation,
    Relationship,
)


class TestDeviceScopeModels(unittest.TestCase):

    def test_device_generates_an_id(self):
        device = Device()

        self.assertTrue(device.id)
        self.assertEqual(device.device_type, "unknown")

    def test_device_stores_identifiers(self):
        device = Device(
            name="test-device",
            identifiers={
                "ip": "192.168.1.10",
                "mac": "AA:BB:CC:DD:EE:FF",
            },
        )

        self.assertEqual(
            device.identifiers["ip"],
            "192.168.1.10",
        )

    def test_observation_records_its_source(self):
        observation = Observation(
            source="network",
            kind="host_discovered",
            device_id="device-123",
            data={"ip": "192.168.1.10"},
        )

        self.assertEqual(observation.source, "network")
        self.assertEqual(
            observation.device_id,
            "device-123",
        )
        self.assertTrue(observation.id)

    def test_evidence_rejects_invalid_confidence(self):
        with self.assertRaises(ValueError):
            Evidence(
                subject_id="device-123",
                claim="manufacturer",
                value="Example Manufacturer",
                confidence=1.5,
            )

    def test_evidence_accepts_valid_confidence(self):
        evidence = Evidence(
            subject_id="device-123",
            claim="manufacturer",
            value="Example Manufacturer",
            confidence=0.85,
            rationale="A matching manufacturer record was found.",
        )

        self.assertEqual(evidence.confidence, 0.85)

    def test_relationship_records_supporting_evidence(self):
        relationship = Relationship(
            source_id="device-123",
            target_id="device-456",
            relation_type="communicates_with",
            confidence=0.9,
            evidence_ids=["evidence-123"],
        )

        self.assertEqual(
            relationship.relation_type,
            "communicates_with",
        )
        self.assertEqual(
            relationship.evidence_ids,
            ["evidence-123"],
        )

    def test_observation_rejects_naive_timestamps(self):
        with self.assertRaises(ValueError):
            Observation(
                source="network",
                kind="host_discovered",
                observed_at=datetime.now(),
            )


if __name__ == "__main__":
    unittest.main()