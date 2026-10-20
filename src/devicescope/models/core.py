from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4


def new_id() -> str:
    """Generate an internal identifier."""
    return str(uuid4())


def utc_now() -> datetime:
    """Return the current timezone-aware UTC timestamp."""
    return datetime.now(timezone.utc)


def require_text(field_name: str, value: str) -> None:
    """Reject missing or empty string values."""
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")


def require_aware_datetime(
    field_name: str,
    value: datetime,
) -> None:
    """Require a timezone-aware datetime."""
    if (
        not isinstance(value, datetime)
        or value.tzinfo is None
        or value.utcoffset() is None
    ):
        raise ValueError(
            f"{field_name} must be timezone-aware"
        )


def require_confidence(value: float) -> None:
    """Require a numeric confidence score between 0 and 1."""
    if (
        isinstance(value, bool)
        or not isinstance(value, (int, float))
        or not 0.0 <= value <= 1.0
    ):
        raise ValueError(
            "confidence must be a number between 0 and 1"
        )


@dataclass
class Device:
    device_type: str = "unknown"
    name: str | None = None
    identifiers: dict[str, str] = field(default_factory=dict)
    attributes: dict[str, Any] = field(default_factory=dict)

    id: str = field(default_factory=new_id)
    first_seen: datetime = field(default_factory=utc_now)
    last_seen: datetime = field(default_factory=utc_now)

    def __post_init__(self) -> None:
        require_text("id", self.id)
        require_text("device_type", self.device_type)

        if self.name is not None:
            require_text("name", self.name)

        require_aware_datetime("first_seen", self.first_seen)
        require_aware_datetime("last_seen", self.last_seen)

        if self.first_seen > self.last_seen:
            raise ValueError(
                "first_seen cannot be later than last_seen"
            )

        if not isinstance(self.identifiers, dict):
            raise ValueError("identifiers must be a dictionary")

        for key, value in self.identifiers.items():
            require_text("identifier key", key)
            require_text("identifier value", value)

        if not isinstance(self.attributes, dict):
            raise ValueError("attributes must be a dictionary")


@dataclass
class Observation:
    source: str
    kind: str

    observed_at: datetime = field(default_factory=utc_now)
    device_id: str | None = None
    data: dict[str, Any] = field(default_factory=dict)

    id: str = field(default_factory=new_id)

    def __post_init__(self) -> None:
        require_text("source", self.source)
        require_text("kind", self.kind)
        require_text("id", self.id)
        require_aware_datetime("observed_at", self.observed_at)

        if self.device_id is not None:
            require_text("device_id", self.device_id)

        if not isinstance(self.data, dict):
            raise ValueError("data must be a dictionary")


@dataclass
class Evidence:
    subject_id: str
    claim: str
    value: str
    confidence: float

    observation_ids: list[str] = field(default_factory=list)
    rationale: str | None = None

    id: str = field(default_factory=new_id)
    created_at: datetime = field(default_factory=utc_now)

    def __post_init__(self) -> None:
        require_text("subject_id", self.subject_id)
        require_text("claim", self.claim)
        require_text("value", self.value)
        require_text("id", self.id)
        require_confidence(self.confidence)
        require_aware_datetime("created_at", self.created_at)

        if not isinstance(self.observation_ids, list):
            raise ValueError(
                "observation_ids must be a list"
            )

        for observation_id in self.observation_ids:
            require_text("observation_id", observation_id)

        if self.rationale is not None:
            require_text("rationale", self.rationale)


@dataclass
class Relationship:
    source_id: str
    target_id: str
    relation_type: str
    confidence: float

    evidence_ids: list[str] = field(default_factory=list)
    attributes: dict[str, Any] = field(default_factory=dict)

    id: str = field(default_factory=new_id)
    first_seen: datetime = field(default_factory=utc_now)
    last_seen: datetime = field(default_factory=utc_now)

    def __post_init__(self) -> None:
        require_text("source_id", self.source_id)
        require_text("target_id", self.target_id)
        require_text("relation_type", self.relation_type)
        require_text("id", self.id)

        require_confidence(self.confidence)
        require_aware_datetime("first_seen", self.first_seen)
        require_aware_datetime("last_seen", self.last_seen)

        if self.first_seen > self.last_seen:
            raise ValueError(
                "first_seen cannot be later than last_seen"
            )

        if not isinstance(self.evidence_ids, list):
            raise ValueError("evidence_ids must be a list")

        for evidence_id in self.evidence_ids:
            require_text("evidence_id", evidence_id)

        if not isinstance(self.attributes, dict):
            raise ValueError("attributes must be a dictionary")