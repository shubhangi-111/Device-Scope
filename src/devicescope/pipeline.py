
"""Orchestrate DeviceScope collection and persistence."""

from dataclasses import dataclass, replace
from typing import Callable

from devicescope.collectors.network import collect
from devicescope.correlation import CorrelationEngine
from devicescope.identification import IdentificationEngine
from devicescope.models import Device, Evidence, Observation, Relationship
from devicescope.normalization import (
    normalize_ip,
    normalize_mac,
    normalize_observations,
)
from devicescope.storage import Repository


Collector = Callable[[], list[tuple[Device, Observation]]]


@dataclass
class PipelineResult:
    devices: list[Device]
    observations: list[Observation]
    evidence: list[Evidence]
    relationships: list[Relationship]

    @property
    def device_count(self) -> int:
        return len(self.devices)

    @property
    def observation_count(self) -> int:
        return len(self.observations)

    @property
    def evidence_count(self) -> int:
        return len(self.evidence)

    @property
    def relationship_count(self) -> int:
        return len(self.relationships)


class DeviceScopePipeline:
    def __init__(
        self,
        repository: Repository,
        identification_engine: IdentificationEngine | None = None,
        correlation_engine: CorrelationEngine | None = None,
        collector: Collector | None = None,
    ) -> None:
        self.repository = repository
        self.identification_engine = (
            identification_engine or IdentificationEngine()
        )
        self.correlation_engine = correlation_engine or CorrelationEngine()
        self.collector = collector or collect

    @staticmethod
    def _identity_key(device: Device) -> tuple[str, str]:
        mac = normalize_mac(device.identifiers.get("mac"))
        if mac:
            return ("mac", mac)

        ip = normalize_ip(device.identifiers.get("ip"))
        if ip:
            return ("ip", ip)

        return ("id", device.id)

    def run(self) -> PipelineResult:
        collected = self.collector()
        if not isinstance(collected, list):
            raise TypeError("Collector must return a list")

        for item in collected:
            if (
                not isinstance(item, tuple)
                or len(item) != 2
                or not isinstance(item[0], Device)
                or not isinstance(item[1], Observation)
            ):
                raise TypeError(
                    "Each collector result must be a "
                    "(Device, Observation) tuple"
                )

        normalized = normalize_observations(
            [observation for _, observation in collected]
        )

        # Build the persisted identity index before processing this run.
        inventory: dict[tuple[str, str], Device] = {}
        for existing in self.repository.list_devices():
            key = self._identity_key(existing)
            inventory.setdefault(key, existing)

        devices_by_id: dict[str, Device] = {}
        observations: list[Observation] = []

        for (incoming, _), observation in zip(
            collected, normalized, strict=True
        ):
            key = self._identity_key(incoming)
            canonical = inventory.get(key)

            if canonical is None:
                canonical = incoming
                inventory[key] = canonical
            else:
                canonical.identifiers.update(
                    {
                        name: value
                        for name, value in incoming.identifiers.items()
                        if value
                    }
                )
                canonical.attributes.update(incoming.attributes)

                if canonical.name is None and incoming.name:
                    canonical.name = incoming.name

                if incoming.first_seen < canonical.first_seen:
                    canonical.first_seen = incoming.first_seen

                if incoming.last_seen > canonical.last_seen:
                    canonical.last_seen = incoming.last_seen

            devices_by_id[canonical.id] = canonical
            observations.append(
                replace(observation, device_id=canonical.id)
            )

        devices = list(devices_by_id.values())

        for device in devices:
            self.repository.save_device(device)

        for observation in observations:
            self.repository.save_observation(observation)

        evidence: list[Evidence] = []
        for device in devices:
            known = self.repository.list_observations(device.id)
            for item in self.identification_engine.identify(device, known):
                self.repository.save_evidence(item)
                evidence.append(item)

        # No relationship is inferred without explicit candidate rules.
        relationships: list[Relationship] = self.correlation_engine.correlate(
            devices, evidence, []
        )

        for relationship in relationships:
            self.repository.save_relationship(relationship)

        return PipelineResult(
            devices=devices,
            observations=observations,
            evidence=evidence,
            relationships=relationships,
        )
