
import ipaddress
import json
import subprocess
from typing import Any

from devicescope.models import Device, Observation


ZERO_MACS = {
    "00:00:00:00:00:00",
    "ff:ff:ff:ff:ff:ff",
}


def normalize_mac(value: str | None) -> str | None:
    """Normalize a MAC address or return None if unusable."""
    if not value:
        return None

    normalized = value.strip().replace("-", ":").upper()

    if normalized in ZERO_MACS:
        return None

    parts = normalized.split(":")

    if len(parts) != 6:
        return None

    if any(
        len(part) != 2
        or any(char not in "0123456789ABCDEF" for char in part)
        for part in parts
    ):
        return None

    return normalized


def parse_neighbors(
    records: list[dict[str, Any]],
) -> list[tuple[Device, Observation]]:
    """Convert Windows neighbor records into candidate devices."""
    results = []

    for record in records:
        try:
            address = ipaddress.ip_address(
                str(record.get("IPAddress", "")).strip()
            )
        except ValueError:
            continue

        # Neighbor discovery should represent individual IP hosts,
        # not multicast groups or broadcast addresses.
        if address.is_multicast or address.is_unspecified:
            continue

        if address.version != 4:
            continue

        if address == ipaddress.IPv4Address("255.255.255.255"):
            continue

        mac = normalize_mac(record.get("LinkLayerAddress"))

        state = str(record.get("State", "Unknown")).strip()
        interface = str(record.get("InterfaceAlias", "")).strip()

        identifiers = {"ip": str(address)}

        if mac is not None:
            identifiers["mac"] = mac

        device = Device(
            device_type="network_neighbor",
            identifiers=identifiers,
            attributes={
                "mac_available": mac is not None,
            },
        )

        observation = Observation(
            source="windows_neighbor_table",
            kind="neighbor_entry",
            device_id=device.id,
            data={
                "ip": str(address),
                "mac": mac,
                "state": state,
                "interface": interface,
            },
        )

        results.append((device, observation))

    return results


def collect() -> list[tuple[Device, Observation]]:
    """Collect IPv4 neighbor entries from Windows."""
    if subprocess.os.name != "nt":
        raise OSError("This collector currently supports Windows only")

    command = (
        "Get-NetNeighbor -AddressFamily IPv4 | "
        "Select-Object IPAddress, LinkLayerAddress, State, InterfaceAlias | "
        "ConvertTo-Json -Compress"
    )

    completed = subprocess.run(
        [
            "powershell.exe",
            "-NoProfile",
            "-NonInteractive",
            "-Command",
            command,
        ],
        capture_output=True,
        text=True,
        timeout=15,
        check=True,
    )

    output = completed.stdout.strip()

    if not output:
        return []

    records = json.loads(output)

    # PowerShell emits an object for one result and an array for many.
    if isinstance(records, dict):
        records = [records]

    if not isinstance(records, list):
        raise ValueError("Unexpected Windows neighbor-table output")

    return parse_neighbors(records)
