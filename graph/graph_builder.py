"""Build CoM3D object hypotheses from EvidenceToken JSONL."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Iterable

from alignment.costs import pairwise_evidence_cost
from alignment.matching import greedy_matching, hungarian_matching
from evidence import EvidenceToken, load_tokens_jsonl
from evidence.uncertainty import softmax


@dataclass(slots=True)
class ObjectHypothesis:
    object_id: str
    token_ids: list[str]
    timestamp: float
    class_posterior: list[float]
    confidence: float
    support_count: int
    mean_uncertainty: float
    center_3d: list[float] | None = None
    metadata: dict[str, object] = field(default_factory=dict)

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def group_by_timestamp(tokens: Iterable[EvidenceToken], precision: int = 3) -> dict[float, list[EvidenceToken]]:
    groups: dict[float, list[EvidenceToken]] = {}
    for token in tokens:
        key = round(float(token.timestamp), precision)
        groups.setdefault(key, []).append(token)
    return groups


def _mean_probs(tokens: list[EvidenceToken]) -> list[float]:
    probs = [softmax(token.class_logits) for token in tokens]
    if not probs:
        return []
    dim = max(len(row) for row in probs)
    padded = [row + [0.0] * (dim - len(row)) for row in probs]
    return [sum(row[idx] for row in padded) / len(padded) for idx in range(dim)]


def _mean_center(tokens: list[EvidenceToken]) -> list[float] | None:
    centers = [token.metadata.get("center_3d") for token in tokens if token.metadata.get("center_3d")]
    if not centers:
        return None
    dim = len(centers[0])
    return [sum(float(center[idx]) for center in centers) / len(centers) for idx in range(dim)]


def _connected_components(tokens: list[EvidenceToken], threshold: float, algorithm: str) -> list[list[EvidenceToken]]:
    if len(tokens) <= 1:
        return [[token] for token in tokens]

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

    if algorithm == "hungarian":
        left = tokens[::2]
        right = tokens[1::2]
        offset = 1
        matches = hungarian_matching(left, right, threshold)
        for i, j, _ in matches:
            union(i * 2, j * 2 + offset)
    else:
        for i in range(len(tokens)):
            for j in range(i + 1, len(tokens)):
                if pairwise_evidence_cost(tokens[i], tokens[j]) <= threshold:
                    union(i, j)

    groups: dict[int, list[EvidenceToken]] = {}
    for idx, token in enumerate(tokens):
        groups.setdefault(find(idx), []).append(token)
    return list(groups.values())


def build_object_hypotheses(
    tokens: list[EvidenceToken],
    *,
    threshold: float = 2.0,
    algorithm: str = "greedy",
) -> list[ObjectHypothesis]:
    hypotheses: list[ObjectHypothesis] = []
    for timestamp, group_tokens in sorted(group_by_timestamp(tokens).items()):
        components = _connected_components(group_tokens, threshold, algorithm)
        for idx, component in enumerate(components):
            posterior = _mean_probs(component)
            hypotheses.append(
                ObjectHypothesis(
                    object_id=f"t{timestamp:.3f}_obj{idx:03d}",
                    token_ids=[token.token_id for token in component],
                    timestamp=timestamp,
                    class_posterior=posterior,
                    confidence=max(posterior) if posterior else 0.0,
                    support_count=len(component),
                    mean_uncertainty=sum(token.uncertainty for token in component) / len(component),
                    center_3d=_mean_center(component),
                    metadata={
                        "uav_ids": sorted({token.uav_id for token in component}),
                        "matching_algorithm": algorithm,
                    },
                )
            )
    return hypotheses


def main() -> None:
    parser = argparse.ArgumentParser(description="Build object hypotheses from EvidenceToken JSONL.")
    parser.add_argument("--tokens", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--threshold", type=float, default=2.0)
    parser.add_argument("--algorithm", choices=["greedy", "hungarian"], default="greedy")
    args = parser.parse_args()

    tokens = load_tokens_jsonl(args.tokens)
    hypotheses = build_object_hypotheses(tokens, threshold=args.threshold, algorithm=args.algorithm)
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(
        json.dumps([hypothesis.to_dict() for hypothesis in hypotheses], indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    print(f"Wrote {len(hypotheses)} object hypotheses to {out_path}")


if __name__ == "__main__":
    main()

