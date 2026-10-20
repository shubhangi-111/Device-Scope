
from collections import Counter

from devicescope.pipeline import DeviceScopePipeline
from devicescope.storage import Database, Repository


NEIGHBOR_STATES = {
    "0": "Unreachable",
    "1": "Incomplete",
    "2": "Probe",
    "3": "Delay",
    "4": "Stale",
    "5": "Reachable",
    "6": "Permanent",
}


def main() -> None:
    repository = Repository(Database("devicescope.db"))
    result = DeviceScopePipeline(repository=repository).run()

    states = Counter()
    devices_with_mac = 0
    devices_with_ip = 0

    for observation in result.observations:
        raw_state = observation.data.get("state")
        if raw_state is not None:
            key = str(raw_state).strip()
            label = NEIGHBOR_STATES.get(key, f"Unknown ({key})")
            states[label] += 1

    for device in result.devices:
        devices_with_mac += bool(device.identifiers.get("mac"))
        devices_with_ip += bool(device.identifiers.get("ip"))

    missing_mac = result.device_count - devices_with_mac

    print("\n" + "=" * 48)
    print("              DEVICESCOPE REPORT")
    print("=" * 48)

    print("\n[ INVENTORY ]")
    print(f"Device records           : {result.device_count}")
    print(f"Observations             : {result.observation_count}")
    print(f"Records with IPv4        : {devices_with_ip}")
    print(f"Records with MAC         : {devices_with_mac}")
    print(f"Records without MAC      : {missing_mac}")

    print("\n[ NEIGHBOR STATES ]")
    if states:
        for label, count in sorted(states.items()):
            print(f"{label:<24}: {count}")
    else:
        print("No neighbor-state data available.")

    print("\n[ FINDINGS ]")
    if missing_mac:
        print(
            f"- {missing_mac} device records lack a MAC address. "
            "Identity is incomplete; this is not proof of a vulnerability."
        )
    else:
        print("- All device records include a MAC address.")

    if states.get("Unreachable", 0):
        print(
            f"- {states['Unreachable']} observations are marked "
            "Unreachable by Windows."
        )

    if states.get("Stale", 0):
        print(
            f"- {states['Stale']} observations are marked Stale. "
            "These entries may need refreshing."
        )

    print("\n[ ASSESSMENT STATUS ]")
    print(f"Evidence records          : {result.evidence_count}")
    print(f"Relationships             : {result.relationship_count}")
    print("Vulnerability assessment  : Not implemented")
    print("Interpretation             : Inventory diagnostics only")

    print("\n[ STORAGE ]")
    print("SQLite database           : devicescope.db")
    print("=" * 48 + "\n")


if __name__ == "__main__":
    main()
