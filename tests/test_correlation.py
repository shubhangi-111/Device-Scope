
import unittest

from devicescope.correlation import CorrelationEngine
from devicescope.models import Device, Evidence


class TestCorrelationEngine(unittest.TestCase):

    def setUp(self):
        self.engine = CorrelationEngine()

        self.device_a = Device(
            identifiers={"ip": "10.68.0.214"}
        )
        self.device_b = Device(
            identifiers={"ip": "10.68.0.1"}
        )

        self.evidence = Evidence(
            subject_id=self.device_a.id,
            claim="observed_relationship",
            value="example association",
            confidence=0.7,
            rationale="Test evidence only.",
        )

    def test_creates_supported_relationship(self):
        result = self.engine.correlate(
            [self.device_a, self.device_b],
            [self.evidence],
            [{
                "source_id": self.device_a.id,
                "target_id": self.device_b.id,
                "relation_type": "associated_with",
                "evidence_ids": [self.evidence.id],
            }],
        )

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].confidence, 0.7)

    def test_rejects_unknown_device(self):
        result = self.engine.correlate(
            [self.device_a],
            [self.evidence],
            [{
                "source_id": self.device_a.id,
                "target_id": "unknown-device",
                "relation_type": "associated_with",
                "evidence_ids": [self.evidence.id],
            }],
        )

        self.assertEqual(result, [])

    def test_rejects_self_relationship(self):
        result = self.engine.correlate(
            [self.device_a],
            [self.evidence],
            [{
                "source_id": self.device_a.id,
                "target_id": self.device_a.id,
                "relation_type": "associated_with",
                "evidence_ids": [self.evidence.id],
            }],
        )

        self.assertEqual(result, [])

    def test_rejects_relationship_without_evidence(self):
        result = self.engine.correlate(
            [self.device_a, self.device_b],
            [],
            [{
                "source_id": self.device_a.id,
                "target_id": self.device_b.id,
                "relation_type": "associated_with",
                "evidence_ids": [],
            }],
        )

        self.assertEqual(result, [])

    def test_uses_lowest_supporting_confidence(self):
        second = Evidence(
            subject_id=self.device_b.id,
            claim="observed_relationship",
            value="second test signal",
            confidence=0.4,
        )

        result = self.engine.correlate(
            [self.device_a, self.device_b],
            [self.evidence, second],
            [{
                "source_id": self.device_a.id,
                "target_id": self.device_b.id,
                "relation_type": "associated_with",
                "evidence_ids": [
                    self.evidence.id,
                    second.id,
                ],
            }],
        )

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].confidence, 0.4)


if __name__ == "__main__":
    unittest.main()
