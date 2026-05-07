"""JSON-friendly 3D evidence graph."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

import numpy as np

from alignment.costs import pairwise_evidence_cost
from evidence import EvidenceToken
from evidence.uncertainty import softmax


@dataclass(slots=True)
class ObservationNode:
    node_id: str
    token: EvidenceToken
    center_3d: list[float] | None = None


@dataclass(slots=True)
class ObjectHypothesisNode:
    node_id: str
    observation_ids: list[str] = field(default_factory=list)
    class_posterior: list[float] = field(default_factory=list)
    center_3d: list[float] | None = None
    confidence: float = 0.0
    support_count: int = 0
    consistency_score: float = 0.0


@dataclass(slots=True)
class GraphEdge:
    source: str
    target: str
    edge_type: str
    weight: float
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class EvidenceGraph:
    observations: list[ObservationNode]
    objects: list[ObjectHypothesisNode]
    edges: list[GraphEdge]

    def to_dict(self) -> dict[str, Any]:
        return {
            "observations": [asdict(node) for node in self.observations],
            "objects": [asdict(node) for node in self.objects],
            "edges": [asdict(edge) for edge in self.edges],
        }


def _aggregate_logits(tokens: list[EvidenceToken]) -> list[float]:
    if not tokens:
        return []
    probs = [softmax(token.class_logits) for token in tokens]
    dim = max(len(p) for p in probs)
    padded = [p + [0.0] * (dim - len(p)) for p in probs]
    return (np.asarray(padded).mean(axis=0)).tolist()


def _aggregate_center(tokens: list[EvidenceToken]) -> list[float] | None:
    centers = [token.metadata.get("center_3d") for token in tokens if token.metadata.get("center_3d") is not None]
    if not centers:
        return None
    return np.asarray(centers, dtype=float).mean(axis=0).tolist()


def build_evidence_graph(tokens: list[EvidenceToken], association_threshold: float = 2.0) -> EvidenceGraph:
    observations = [
        ObservationNode(f"obs_{idx}", token, token.metadata.get("center_3d")) for idx, token in enumerate(tokens)
    ]
    parent = list(range(len(tokens)))

    def find(x: int) -> int:
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a: int, b: int) -> None:
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[rb] = ra

    edges: list[GraphEdge] = []
    for i in range(len(tokens)):
        for j in range(i + 1, len(tokens)):
            cost = pairwise_evidence_cost(tokens[i], tokens[j])
            weight = 1.0 / (1.0 + cost)
            edge_type = "support" if cost <= association_threshold else "conflict"
            edges.append(GraphEdge(observations[i].node_id, observations[j].node_id, edge_type, weight, {"cost": cost}))
            if cost <= association_threshold:
                union(i, j)

    groups: dict[int, list[int]] = {}
    for idx in range(len(tokens)):
        groups.setdefault(find(idx), []).append(idx)

    objects: list[ObjectHypothesisNode] = []
    for obj_idx, indices in enumerate(groups.values()):
        group_tokens = [tokens[i] for i in indices]
        posterior = _aggregate_logits(group_tokens)
        confidence = max(posterior) if posterior else 0.0
        object_id = f"obj_{obj_idx}"
        consistency = 1.0 / (1.0 + float(np.mean([t.uncertainty for t in group_tokens])))
        node = ObjectHypothesisNode(
            node_id=object_id,
            observation_ids=[observations[i].node_id for i in indices],
            class_posterior=posterior,
            center_3d=_aggregate_center(group_tokens),
            confidence=confidence,
            support_count=len(indices),
            consistency_score=consistency,
        )
        objects.append(node)
        for obs_id in node.observation_ids:
            edges.append(GraphEdge(obs_id, object_id, "belongs_to", confidence))

    return EvidenceGraph(observations, objects, edges)

