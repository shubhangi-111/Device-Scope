# DeviceScope Architecture

## Purpose

DeviceScope is a defensive device-visibility and exposure
assessment tool.

It discovers observable devices and connections, records
supporting evidence, estimates identification confidence,
and presents relationships between entities.

## Processing Pipeline

Collect -> Normalize -> Identify -> Correlate -> Present

### Collect

Gather observations from authorized sources.

Collectors must preserve the original observation and avoid
making unsupported identity claims.

### Normalize

Convert raw observations into a consistent internal format.

Preserve the original data for traceability.

### Identify

Associate observations with candidate entities.

Every inferred identity should have supporting evidence
and an explicit confidence score.

### Correlate

Build relationships between entities using observations
and evidence.

Relationships must record their supporting evidence.

### Present

Expose results through the CLI, JSON reports, and HTML
visualizations.

## Storage

SQLite will eventually persist observations, evidence,
relationships, and historical changes.

## Design Principles

- Modular components with clear responsibilities.
- Evidence-based attribution.
- Explicit confidence scores.
- Traceable conclusions.
- Minimal dependencies.
- Defensive, authorized observation only.
- No unsupported claims about device ownership or identity.