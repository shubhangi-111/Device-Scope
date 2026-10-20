
# DeviceScope

**See your device's network exposure. Understand the evidence. Know what to fix.**

DeviceScope is a local-first network inventory and security-assessment project with a dark-mode radar interface. It collects Windows network-neighbor information, normalizes observations, maintains a SQLite inventory, and presents network state and inventory-completeness diagnostics.

The long-term goal is to make basic security exposure assessments understandable and affordable, including for people without a cybersecurity background.

> **Current status:** The network inventory pipeline and desktop radar UI are implemented. Comprehensive port/service assessment, camera and microphone exposure analysis, and downloadable security reports are planned features—not capabilities currently provided by the application.

## Features

### Implemented

- **Passive network inventory:** Collects IPv4 neighbor-table entries from Windows.
- **Data normalization:** Standardizes IP addresses, MAC addresses, and neighbor observations.
- **Device identification framework:** Supports evidence-based manufacturer attribution when a manufacturer registry is configured.
- **Correlation framework:** Provides a foundation for relationships supported by evidence.
- **SQLite persistence:** Stores devices, observations, evidence, and relationships.
- **Dark-mode radar UI:** Displays an animated scanning indicator and illustrative device markers.
- **Inventory diagnostics:** Summarizes observed neighbor states and records with or without MAC addresses.
- **Automated tests:** Unit and integration tests cover the project's core components.

### Planned

- Scan history and a real `Last scanned` timestamp.
- Detection and classification of selected TCP services and ports.
- Clear distinction between local listeners and services reachable from another host.
- Evidence-backed exposure findings with confidence, severity, and remediation guidance.
- Additional checks for remote-access configurations and potential camera or microphone exposure.
- Downloadable security reports.
- Historical comparisons and configurable scan scopes.
- An optional low-cost report tier, subject to demand and cost validation.

## How it works

```text
Windows Neighbor Table
          |
          v
    Network Collector
          |
          v
     Normalization
          |
          v
 Device Identification
          |
          v
 Evidence / Correlation
          |
          v
    SQLite Storage
          |
          v
    Dark-Mode Radar UI
```

The radar is a visualization of inventory records. Its marker positions are illustrative; they do not represent measured physical locations or actual distances between devices.

## Technology stack

- **Language:** Python
- **Desktop interface:** Tkinter
- **Database:** SQLite
- **Testing:** Python `unittest`
- **Environment:** Windows and Python virtual environments

## Requirements

- Windows
- Python 3.12 or a compatible Python version
- PowerShell
- Git (recommended)

The current network collector uses Windows PowerShell commands. Other operating systems are not currently supported by that collector.

## Installation

Clone the repository and enter the project directory:

```powershell
git clone <YOUR_REPOSITORY_URL>
cd Device-Scope
```

Create and activate a virtual environment:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Install the project in editable mode:

```powershell
python -m pip install -e .
```

If PowerShell prevents virtual-environment activation, use the environment's interpreter directly:

```powershell
.\.venv\Scripts\python.exe -m pip install -e .
```

## Run DeviceScope

### Launch the desktop radar

From the project root:

```powershell
python -m devicescope.ui
```

Click **Start Scan** to collect the current Windows neighbor table. The interface displays inventory statistics after collection completes.

### Run the pipeline from the terminal

```powershell
python -m devicescope.run_pipeline
```

The command runs a collection cycle, persists results in `devicescope.db`, and prints an inventory report.

The database is created in the current working directory.

## Run the tests

Run the complete test suite:

```powershell
python -m unittest discover -s tests -v
```

The test suite covers models, collection parsing, normalization, identification, correlation, storage, and pipeline integration.

## Understanding the results

DeviceScope currently observes network-neighbor information. This is useful for inventory, but it is not a complete security assessment.

- **An IP address is not proof of a unique physical device.** Addresses can change, and entries can be stale or virtual.
- **A missing MAC address is an inventory limitation, not proof of a vulnerability.**
- **An unreachable or stale neighbor entry does not establish malicious activity.**
- **An open port does not automatically mean a camera or microphone is remotely accessible.**
- **A service being reachable does not by itself establish that it is vulnerable or exploitable.**

Future security findings should identify the observation, explain the inference, communicate uncertainty, and provide a practical remediation step.

## Privacy and responsible testing

DeviceScope is designed to keep its inventory and database local by default.

- Do not interpret illustrative radar positions as physical device locations.
- Do not collect, transmit, or store credentials unnecessarily.
- Test services only on devices and networks you own or are authorized to assess.
- Keep scans within a clearly defined scope.
- Prefer non-invasive checks; do not attempt exploitation or access cameras and microphones as part of an exposure assessment.
- Do not claim a vulnerability without sufficient evidence.

A production release should document data retention, report handling, and any network data sent to external services before introducing such functionality.

## Project structure

```text
Device-Scope/
├── docs/
├── src/
│   └── devicescope/
│       ├── collectors/
│       ├── correlation/
│       ├── identification/
│       ├── models/
│       ├── normalization/
│       ├── storage/
│       ├── pipeline.py
│       ├── run_pipeline.py
│       └── ui.py
├── tests/
├── .gitignore
├── pyproject.toml
└── README.md
```

## Roadmap

1. Stabilize device identity reconciliation across collection cycles.
2. Add scan history and timestamps.
3. Implement bounded, evidence-backed service exposure checks.
4. Generate an actionable security report.
5. Expand integration tests and documentation.
6. Evaluate a low-cost report model after validating usefulness and operating costs.

## Disclaimer

DeviceScope is an evolving educational and defensive security project. It does not currently provide a comprehensive vulnerability assessment, guarantee device security, or determine whether a camera or microphone can be accessed remotely.

A clean report means only that the checks performed did not identify a reportable issue; it is not a guarantee that a device is secure.

## License

No license has been selected yet. Until one is added, do not assume that others have permission to redistribute or reuse the project.
```
