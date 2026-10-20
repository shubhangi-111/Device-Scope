
from collections.abc import Mapping

from devicescope.models import Device, Evidence, Observation
from devicescope.normalization import normalize_mac


DEFAULT_MANUFACTURERS: dict[str, str] = {}


class IdentificationEngine:
    """Generate evidence-backed manufacturer identification claims."""

    def __init__(
        self,
        manufacturers: Mapping[str, str] | None = None,
    ) -> None:
        registry = (
            DEFAULT_MANUFACTURERS
            if manufacturers is None
            else manufacturers
        )
        self.manufacturers = self._validate_registry(registry)

    @staticmethod
    def _validate_registry(
        registry: Mapping[str, str],
    ) -> dict[str, str]:
        """Validate full MAC addresses and three-octet prefixes."""
        if not isinstance(registry, Mapping):
            raise TypeError("manufacturers must be a mapping")

        validated: dict[str, str] = {}

        for prefix, manufacturer in registry.items():
            if not isinstance(prefix, str):
                raise ValueError(
                    f"Invalid manufacturer MAC prefix: {prefix!r}"
                )

            normalized = prefix.strip().replace("-", ":").upper()
            parts = normalized.split(":")

            if len(parts) not in (3, 6):
                raise ValueError(
                    f"Invalid manufacturer MAC prefix: {prefix!r}"
                )

            for part in parts:
                if (
                    len(part) != 2
                    or any(
                        char not in "0123456789ABCDEF"
                        for char in part
                    )
                ):
                    raise ValueError(
                        f"Invalid manufacturer MAC prefix: {prefix!r}"
                    )

            if (
                not isinstance(manufacturer, str)
                or not manufacturer.strip()
            ):
                raise ValueError(
                    "Manufacturer names must be non-empty strings"
                )

            key = ":".join(parts[:3])
            validated[key] = manufacturer.strip()

        return validated

    def identify(
        self,
        device: Device,
        observations: list[Observation],
    ) -> list[Evidence]:
        """Identify a candidate manufacturer from a configured MAC prefix."""
        if not isinstance(device, Device):
            raise TypeError("device must be a Device")

        if not isinstance(observations, list):
            raise TypeError("observations must be a list")

        if not all(
            isinstance(item, Observation)
            for item in observations
        ):
            raise TypeError(
                "observations must contain Observation objects"
            )

        relevant = [
            observation
            for observation in observations
            if observation.device_id == device.id
        ]

        mac = normalize_mac(device.identifiers.get("mac"))

        if mac is None:
            for observation in relevant:
                mac = normalize_mac(observation.data.get("mac"))
                if mac is not None:
                    break

        if mac is None:
            return []

        prefix = ":".join(mac.split(":")[:3])
        manufacturer = self.manufacturers.get(prefix)

        if manufacturer is None:
            return []

        supporting_ids = [
            observation.id
            for observation in relevant
            if normalize_mac(observation.data.get("mac")) == mac
        ]

        return [
            Evidence(
                subject_id=device.id,
                claim="manufacturer",
                value=manufacturer,
                confidence=0.85,
                observation_ids=supporting_ids,
                rationale=(
                    f"MAC prefix {prefix} matched the configured "
                    "manufacturer registry. This is a candidate "
                    "manufacturer attribution, not identification "
                    "of the device owner."
                ),
            )
        ]

    def identify_many(
        self,
        devices: list[Device],
        observations: list[Observation],
    ) -> dict[str, list[Evidence]]:
        """Return identification results keyed by device ID."""
        if not isinstance(devices, list):
            raise TypeError("devices must be a list")

        if not all(isinstance(device, Device) for device in devices):
            raise TypeError("devices must contain Device objects")

        return {
            device.id: self.identify(device, observations)
            for device in devices
        }
