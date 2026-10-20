
from copy import deepcopy
from typing import Any
import ipaddress

from devicescope.models import Observation


def normalize_mac(value: Any) -> str | None:
    """Return a canonical MAC address, or None if unusable."""
    if not isinstance(value, str) or not value.strip():
        return None

    candidate = value.strip().replace("-", ":").upper()
    parts = candidate.split(":")

    if len(parts) != 6:
        return None

    if any(
        len(part) != 2
        or any(char not in "0123456789ABCDEF" for char in part)
        for part in parts
    ):
        return None

    if candidate in {
        "00:00:00:00:00:00",
        "FF:FF:FF:FF:FF:FF",
    }:
        return None

    return candidate


def normalize_ip(value: Any) -> str | None:
    """Return a canonical IP address, or None if invalid."""
    if not isinstance(value, str) or not value.strip():
        return None

    try:
        return str(ipaddress.ip_address(value.strip()))
    except ValueError:
        return None


def normalize_observation(
    observation: Observation,
) -> Observation:
    """
    Return a normalized copy of an observation.

    The original object is not mutated. Invalid optional network
    identifiers are removed rather than converted into false facts.
    """
    if not isinstance(observation, Observation):
        raise TypeError("observation must be an Observation instance")

    result = deepcopy(observation)
    data = result.data

    if result.source == "windows_neighbor_table":
        raw_ip = data.get("ip")
        normalized_ip = normalize_ip(raw_ip)

        if normalized_ip is None:
            raise ValueError(
                "Network observation requires a valid IP address"
            )

        address = ipaddress.ip_address(normalized_ip)

        if address.version != 4:
            raise ValueError(
                "Windows IPv4 neighbor observations require IPv4 addresses"
            )

        if address.is_multicast or address.is_unspecified:
            raise ValueError(
                "Network observation must identify a unicast host address"
            )

        if address == ipaddress.IPv4Address("255.255.255.255"):
            raise ValueError(
                "Limited broadcast is not a host address"
            )

        data["ip"] = normalized_ip

        mac = normalize_mac(data.get("mac"))
        data["mac"] = mac

        state = data.get("state")

        if isinstance(state, str):
            data["state"] = state.strip().title()
        else:
            data["state"] = "Unknown"

        interface = data.get("interface")

        if isinstance(interface, str):
            data["interface"] = interface.strip()
        else:
            data["interface"] = ""

    return result


def normalize_observations(
    observations: list[Observation],
) -> list[Observation]:
    """Normalize multiple observations while preserving their order."""
    if not isinstance(observations, list):
        raise TypeError("observations must be a list")

    return [
        normalize_observation(observation)
        for observation in observations
    ]
