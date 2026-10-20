
import unittest

from devicescope.collectors.network import (
    normalize_mac,
    parse_neighbors,
)


class TestNetworkCollector(unittest.TestCase):

    def test_normalizes_mac_address(self):
        self.assertEqual(
            normalize_mac("AA-BB-CC-DD-EE-FF"),
            "AA:BB:CC:DD:EE:FF",
        )

    def test_rejects_zero_mac(self):
        self.assertIsNone(
            normalize_mac("00-00-00-00-00-00")
        )

    def test_excludes_multicast(self):
        records = [{
            "IPAddress": "224.0.0.2",
            "LinkLayerAddress": "01-00-5E-00-00-02",
            "State": "Permanent",
            "InterfaceAlias": "Wi-Fi",
        }]

        self.assertEqual(parse_neighbors(records), [])

    def test_keeps_unicast_without_mac(self):
        records = [{
            "IPAddress": "10.68.0.214",
            "LinkLayerAddress": "00-00-00-00-00-00",
            "State": "Stale",
            "InterfaceAlias": "Wi-Fi",
        }]

        results = parse_neighbors(records)

        self.assertEqual(len(results), 1)

        device, observation = results[0]

        self.assertEqual(
            device.identifiers["ip"],
            "10.68.0.214",
        )
        self.assertNotIn("mac", device.identifiers)
        self.assertEqual(observation.data["state"], "Stale")
        self.assertIsNone(observation.data["mac"])

    def test_preserves_interface_and_state(self):
        records = [{
            "IPAddress": "10.68.0.1",
            "LinkLayerAddress": "D4-01-CC-33-66-77",
            "State": "Reachable",
            "InterfaceAlias": "Wi-Fi",
        }]

        _, observation = parse_neighbors(records)[0]

        self.assertEqual(observation.data["state"], "Reachable")
        self.assertEqual(observation.data["interface"], "Wi-Fi")

    def test_ignores_invalid_addresses(self):
        records = [{
            "IPAddress": "not-an-ip",
            "LinkLayerAddress": "AA-BB-CC-DD-EE-FF",
            "State": "Stale",
            "InterfaceAlias": "Wi-Fi",
        }]

        self.assertEqual(parse_neighbors(records), [])


if __name__ == "__main__":
    unittest.main()
