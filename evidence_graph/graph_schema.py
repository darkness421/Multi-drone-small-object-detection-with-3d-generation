"""JSON schema helpers for 3D object evidence graph."""

from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any


@dataclass(frozen=True)
class EvidenceNode:
    """One object-centered evidence graph node."""
    object_id: str
    coarse_class: str
    fine_class_candidates: list[str]
    center_3d: list[float]
    multi_view_crops: list[str]
    per_view_logits: dict[str, dict[str, float]]
    view_angles: dict[str, str]
    occlusion_level: str
    uncertainty: float
    ambiguity_type: str
    missing_evidence: list[str]
    recommended_next_view: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        """Convert node to JSON-serializable dict."""
        return asdict(self)


def graph_document(nodes: list[EvidenceNode]) -> dict[str, Any]:
    """Create a simple JSON graph document."""
    return {
        "graph_type": "CoM3D object evidence graph",
        "nodes": [node.to_dict() for node in nodes],
        "edges": []
    }

