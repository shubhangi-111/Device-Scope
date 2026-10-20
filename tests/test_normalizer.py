
import unittest

from devicescope.models import Observation
from devicescope.normalization import (
    normalize_ip,
    normalize_mac,
    normalize_observation,
    normalize_observations,
)


class TestNormalizer(unittest.TestCase):

    def make_observation(self, **overrides):
        data = {
            "ip": "010.068.000.214",
            "mac": "AC-19-8E-EC-61-84",
            "state": "stale",
            "interface": " Wi-Fi ",
        }
        data.update(overrides)

        return Observation(
            source="windows_neighbor_table",
            kind="neighbor_entry",
            data=data,
        )

    def test_normalizes_mac(self):
        self.assertEqual(
            normalize_mac("ac-19-8e-ec-61-84"),
            "AC:19:8E:EC:61:84",
        )

    def test_rejects_invalid_mac(self):
        self.assertIsNone(normalize_mac("not-a-mac"))

    def test_rejects_zero_mac(self):
        self.assertIsNone(
            normalize_mac("00-00-00-00-00-00")
        )

    def test_normalizes_valid_ip(self):
        self.assertEqual(
            normalize_ip("10.68.0.214"),
            "10.68.0.214",
        )

    def test_rejects_invalid_ip(self):
        self.assertIsNone(normalize_ip("not-an-ip"))

    def test_normalizes_neighbor_observation(self):
        original = Observation(
            source="windows_neighbor_table",
            kind="neighbor_entry",
            data={
                "ip": "10.68.0.214",
                "mac": "AC-19-8E-EC-61-84",
                "state": "stale",
                "interface": " Wi-Fi ",
            },
        )

        normalized = normalize_observation(original)

        self.assertEqual(
            normalized.data["mac"],
            "AC:19:8E:EC:61:84",
        )
        self.assertEqual(normalized.data["state"], "Stale")
        self.assertEqual(normalized.data["interface"], "Wi-Fi")

    def test_does_not_mutate_original(self):
        original = Observation(
            source="windows_neighbor_table",
            kind="neighbor_entry",
            data={
                "ip": "10.68.0.214",
                "mac": "AC-19-8E-EC-61-84",
                "state": "stale",
                "interface": "Wi-Fi",
            },
        )

        normalize_observation(original)

        self.assertEqual(
            original.data["mac"],
            "AC-19-8E-EC-61-84",
        )

    def test_rejects_invalid_neighbor_ip(self):
        observation = Observation(
            source="windows_neighbor_table",
            kind="neighbor_entry",
            data={"ip": "not-an-ip"},
        )

        with self.assertRaises(ValueError):
            normalize_observation(observation)

    def test_rejects_multicast_neighbor_ip(self):
        observation = Observation(
            source="windows_neighbor_table",
            kind="neighbor_entry",
            data={"ip": "224.0.0.2"},
        )

        with self.assertRaises(ValueError):
            normalize_observation(observation)

    def test_normalizes_multiple_observations(self):
        observations = [
            Observation(
                source="windows_neighbor_table",
                kind="neighbor_entry",
                data={"ip": "10.68.0.1"},
            ),
            Observation(
                source="windows_neighbor_table",
                kind="neighbor_entry",
                data={"ip": "10.68.0.2"},
            ),
        ]

        normalized = normalize_observations(observations)

        self.assertEqual(len(normalized), 2)
        self.assertEqual(
            normalized[0].data["ip"],
            "10.68.0.1",
        )
        self.assertEqual(
            normalized[1].data["ip"],
            "10.68.0.2",
        )


if __name__ == "__main__":
    unittest.main()
