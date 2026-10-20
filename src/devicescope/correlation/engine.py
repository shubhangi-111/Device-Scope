
from devicescope.models import Device, Evidence, Relationship


class CorrelationEngine:
    """Build evidence-backed relationships between known devices."""

    def correlate(
        self,
        devices: list[Device],
        evidence_items: list[Evidence],
        candidates: list[dict],
    ) -> list[Relationship]:
        if not all(isinstance(d, Device) for d in devices):
            raise TypeError("devices must contain Device objects")

        if not all(isinstance(e, Evidence) for e in evidence_items):
            raise TypeError("evidence_items must contain Evidence objects")

        if not isinstance(candidates, list):
            raise TypeError("candidates must be a list")

        device_ids = {device.id for device in devices}
        evidence_by_id = {item.id: item for item in evidence_items}

        relationships = []

        for candidate in candidates:
            if not isinstance(candidate, dict):
                raise TypeError("each candidate must be a dictionary")

            source_id = candidate.get("source_id")
            target_id = candidate.get("target_id")
            relation_type = candidate.get("relation_type")
            evidence_ids = candidate.get("evidence_ids", [])

            if source_id not in device_ids or target_id not in device_ids:
                continue

            if source_id == target_id:
                continue

            if not isinstance(evidence_ids, list) or not evidence_ids:
                continue

            supporting_evidence = [
                evidence_by_id[eid]
                for eid in evidence_ids
                if eid in evidence_by_id
            ]

            # Every cited item must actually support this relationship.
            if len(supporting_evidence) != len(evidence_ids):
                continue

            if not all(
                item.subject_id in {source_id, target_id}
                for item in supporting_evidence
            ):
                continue

            if not isinstance(relation_type, str) or not relation_type.strip():
                continue

            confidence = min(
                item.confidence for item in supporting_evidence
            )

            relationships.append(
                Relationship(
                    source_id=source_id,
                    target_id=target_id,
                    relation_type=relation_type.strip(),
                    confidence=confidence,
                    evidence_ids=list(evidence_ids),
                )
            )

        return relationships
