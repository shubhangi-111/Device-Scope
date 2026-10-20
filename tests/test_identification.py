
import unittest

from devicescope.identification import IdentificationEngine
from devicescope.models import Device, Observation


TEST_REGISTRY = {
    "AC:19:8E": "Example Devices Inc.",
}


class TestIdentificationEngine(unittest.TestCase):

    def setUp(self):
        self.engine = IdentificationEngine(TEST_REGISTRY)

        self.device = Device(
            device_type="network_neighbor",
            identifiers={
                "ip": "10.68.0.214",
                "mac": "AC:19:8E:EC:61:84",
            },
        )

        self.observation = Observation(
            source="windows_neighbor_table",
            kind="neighbor_entry",
            device_id=self.device.id,
            data={
                "ip": "10.68.0.214",
                "mac": "AC-19-8E-EC-61-84",
                "state": "Stale",
                "interface": "Wi-Fi",
            },
        )

    def test_identifies_registered_manufacturer(self):
        evidence = self.engine.identify(
            self.device,
            [self.observation],
        )

        self.assertEqual(len(evidence), 1)
        self.assertEqual(evidence[0].claim, "manufacturer")
        self.assertEqual(
            evidence[0].value,
            "Example Devices Inc.",
        )

    def test_evidence_references_supporting_observation(self):
        evidence = self.engine.identify(
            self.device,
            [self.observation],
        )

        self.assertIn(
            self.observation.id,
            evidence[0].observation_ids,
        )

    def test_evidence_has_rationale(self):
        evidence = self.engine.identify(
            self.device,
            [self.observation],
        )

        self.assertIn("MAC prefix", evidence[0].rationale)

    def test_unknown_prefix_produces_no_claim(self):
        engine = IdentificationEngine(
            {"11:22:33": "Another Manufacturer"}
        )

        evidence = engine.identify(
            self.device,
            [self.observation],
        )

        self.assertEqual(evidence, [])

    def test_missing_mac_produces_no_claim(self):
        device = Device(
            device_type="network_neighbor",
            identifiers={"ip": "10.68.0.214"},
        )

        evidence = self.engine.identify(device, [])

        self.assertEqual(evidence, [])

    def test_can_use_mac_from_observation(self):
        device = Device(
            device_type="network_neighbor",
            identifiers={"ip": "10.68.0.214"},
        )

        observation = Observation(
            source="windows_neighbor_table",
            kind="neighbor_entry",
            device_id=device.id,
            data={"mac": "AC-19-8E-EC-61-84"},
        )

        evidence = self.engine.identify(
            device,
            [observation],
        )

        self.assertEqual(len(evidence), 1)
        self.assertEqual(
            evidence[0].value,
            "Example Devices Inc.",
        )

    def test_ignores_observations_for_other_devices(self):
        unrelated = Observation(
            source="windows_neighbor_table",
            kind="neighbor_entry",
            device_id="another-device",
            data={"mac": "AC-19-8E-EC-61-84"},
        )

        evidence = self.engine.identify(
            self.device,
            [unrelated],
        )

        # The device's own MAC still matches the registry,
        # but the unrelated observation must not be cited.
        self.assertEqual(len(evidence), 1)
        self.assertEqual(evidence[0].observation_ids, [])

    def test_invalid_registry_prefix_is_rejected(self):
        with self.assertRaises(ValueError):
            IdentificationEngine(
                {"not-a-mac": "Example Manufacturer"}
            )

    def test_empty_manufacturer_is_rejected(self):
        with self.assertRaises(ValueError):
            IdentificationEngine({"AC:19:8E": "  "})

    def test_identify_many_returns_results_by_device_id(self):
        results = self.engine.identify_many(
            [self.device],
            [self.observation],
        )

        self.assertIn(self.device.id, results)
        self.assertEqual(
            results[self.device.id][0].value,
            "Example Devices Inc.",
        )


if __name__ == "__main__":
    unittest.main()
