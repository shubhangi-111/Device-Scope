
import tempfile
import unittest
from pathlib import Path

from devicescope.models import Device, Observation
from devicescope.pipeline import DeviceScopePipeline
from devicescope.storage import Database, Repository


class TestDeviceScopePipeline(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        database_path = Path(self.temp_dir.name) / "pipeline.db"
        self.repository = Repository(Database(database_path))

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_pipeline_persists_collected_device_and_observation(self):
        device = Device(
            device_type="network_neighbor",
            identifiers={
                "ip": "192.0.2.10",
                "mac": "AA:BB:CC:11:22:33",
            },
        )
        observation = Observation(
            source="windows_neighbor_table",
            kind="neighbor_entry",
            device_id=device.id,
            data={
                "ip": "192.0.2.10",
                "mac": "AA:BB:CC:11:22:33",
                "state": "Stale",
                "interface": "Test Interface",
            },
        )

        pipeline = DeviceScopePipeline(
            repository=self.repository,
            collector=lambda: [(device, observation)],
        )

        result = pipeline.run()

        self.assertEqual(result.device_count, 1)
        self.assertEqual(result.observation_count, 1)
        self.assertEqual(
            self.repository.get_device(device.id).identifiers["ip"],
            "192.0.2.10",
        )
        self.assertEqual(
            self.repository.get_observation(observation.id).device_id,
            device.id,
        )

    def test_empty_collection_returns_empty_result(self):
        pipeline = DeviceScopePipeline(
            repository=self.repository,
            collector=lambda: [],
        )

        result = pipeline.run()

        self.assertEqual(result.device_count, 0)
        self.assertEqual(result.observation_count, 0)
        self.assertEqual(result.evidence_count, 0)
        self.assertEqual(result.relationship_count, 0)


if __name__ == "__main__":
    unittest.main()
