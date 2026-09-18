"""Candidate construction and observation-preserving identity relabeling."""

from __future__ import annotations

from collections import Counter, defaultdict
from collections.abc import Callable

import numpy as np

from .core import PAPER_PARAMETERS, select_edges


def _tracklets(
    predictions: dict[int, list[dict]],
) -> tuple[dict[int, set[int]], dict[int, list[tuple[int, dict]]], dict[int, int]]:
    frames: dict[int, set[int]] = defaultdict(set)
    rows: dict[int, list[tuple[int, dict]]] = defaultdict(list)
    classes: dict[int, int] = {}
    for frame, observations in predictions.items():
        for row in observations:
            identity = int(row["id"])
            class_id = int(row.get("class_id", 0))
            previous = classes.setdefault(identity, class_id)
            if previous != class_id:
                raise ValueError(f"tracklet {identity} contains multiple classes")
            frames[identity].add(int(frame))
            rows[identity].append((int(frame), row))
    for identity in rows:
        rows[identity].sort(key=lambda item: item[0])
    return dict(frames), dict(rows), classes


def build_candidates(
    predictions: dict[int, list[dict]],
    descriptors: dict[int, np.ndarray],
    *,
    maximum_gap_frames: int = 30,
) -> list[dict]:
    """Build same-class, forward temporal edges from frozen tracklets.

    Descriptor arrays must already be finite and L2-normalized, matching the
    cached BaseReID features used in the paper. Geometry is measured between
    the source endpoint center and destination start center in native pixels.
    Candidate gating itself is performed by the selected REGR rule.
    """
    frames, rows, classes = _tracklets(predictions)
    identities = sorted(frames)
    candidates: list[dict] = []
    for left_index, left in enumerate(identities):
        for right in identities[left_index + 1 :]:
            if classes[left] != classes[right] or frames[left] & frames[right]:
                continue
            if max(frames[left]) < min(frames[right]):
                earlier, later = left, right
            elif max(frames[right]) < min(frames[left]):
                earlier, later = right, left
            else:
                continue
            gap = min(frames[later]) - max(frames[earlier])
            if gap < 1 or gap > maximum_gap_frames:
                continue

            earlier_row = rows[earlier][-1][1]
            later_row = rows[later][0][1]
            earlier_center = np.asarray(
                [
                    float(earlier_row["x"]) + float(earlier_row["w"]) / 2.0,
                    float(earlier_row["y"]) + float(earlier_row["h"]) / 2.0,
                ],
                dtype=float,
            )
            later_center = np.asarray(
                [
                    float(later_row["x"]) + float(later_row["w"]) / 2.0,
                    float(later_row["y"]) + float(later_row["h"]) / 2.0,
                ],
                dtype=float,
            )
            geometry = float(np.linalg.norm(earlier_center - later_center))
            appearance = None
            if earlier in descriptors and later in descriptors:
                first = np.asarray(descriptors[earlier], dtype=float)
                second = np.asarray(descriptors[later], dtype=float)
                if first.shape != second.shape:
                    raise ValueError(f"descriptor shape mismatch for {earlier}->{later}")
                if not np.isfinite(first).all() or not np.isfinite(second).all():
                    raise ValueError(f"non-finite descriptor for {earlier}->{later}")
                appearance = float(1.0 - np.dot(first, second))

            candidates.append(
                {
                    "earlier": earlier,
                    "later": later,
                    "gap": int(gap),
                    "endpoint_center_distance_pixels": geometry,
                    "cosine_distance": appearance,
                    "controlled_cost": (
                        (
                            geometry / PAPER_PARAMETERS["geometry_radius_pixels"]
                            + appearance / PAPER_PARAMETERS["appearance_cosine_gate"]
                            + gap / PAPER_PARAMETERS["maximum_gap_frames"]
                        )
                        / 3.0
                        if appearance is not None
                        else None
                    ),
                }
            )
    return candidates


def apply_edges(
    predictions: dict[int, list[dict]],
    proposed: list[dict],
    sort_key: Callable[[dict], tuple],
) -> tuple[dict[int, list[dict]], list[dict], list[dict]]:
    """Apply proposed links while rejecting component frame overlap."""
    frames, _, _ = _tracklets(predictions)
    parent = {identity: identity for identity in frames}
    support = {identity: set(values) for identity, values in frames.items()}

    def find(identity: int) -> int:
        while parent[identity] != identity:
            parent[identity] = parent[parent[identity]]
            identity = parent[identity]
        return identity

    accepted: list[dict] = []
    rejected: list[dict] = []
    for edge in sorted(proposed, key=sort_key):
        source = find(int(edge["earlier"]))
        destination = find(int(edge["later"]))
        if source == destination:
            continue
        overlap = support[source] & support[destination]
        if overlap:
            rejected.append(
                {
                    **edge,
                    "rejection": "component_frame_overlap",
                    "overlap_frames": sorted(overlap),
                }
            )
            continue
        parent[destination] = source
        support[source] |= support[destination]
        accepted.append(dict(edge))

    output: dict[int, list[dict]] = defaultdict(list)
    for frame, observations in predictions.items():
        output[int(frame)] = [
            {**row, "id": find(int(row["id"]))} for row in observations
        ]
    return dict(output), accepted, rejected


def observation_signature(predictions: dict[int, list[dict]]) -> Counter:
    """Return the identity-agnostic observation multiset."""
    signature: Counter = Counter()
    for frame, observations in predictions.items():
        for row in observations:
            signature[
                (
                    int(frame),
                    round(float(row["x"]), 7),
                    round(float(row["y"]), 7),
                    round(float(row["w"]), 7),
                    round(float(row["h"]), 7),
                    round(float(row.get("conf", 1.0)), 7),
                    int(row.get("class_id", 0)),
                )
            ] += 1
    return signature


def duplicate_frame_identity_count(predictions: dict[int, list[dict]]) -> int:
    """Count invalid duplicate identity assignments within frames."""
    count = 0
    for observations in predictions.values():
        identities = Counter(int(row["id"]) for row in observations)
        count += sum(value - 1 for value in identities.values() if value > 1)
    return count


def refine(
    predictions: dict[int, list[dict]],
    descriptors: dict[int, np.ndarray],
    method: str = "regr-tg",
) -> tuple[dict[int, list[dict]], dict]:
    """Run one frozen refiner and return relabeled observations plus audit."""
    candidates = build_candidates(predictions, descriptors)
    proposed, sort_key, details = select_edges(method, predictions, candidates)
    output, accepted, rejected = apply_edges(predictions, proposed, sort_key)
    preserved = observation_signature(predictions) == observation_signature(output)
    duplicates = duplicate_frame_identity_count(output)
    if not preserved or duplicates:
        raise RuntimeError(
            "refinement violated the observation-preservation contract: "
            f"preserved={preserved}, duplicate_frame_identities={duplicates}"
        )
    return output, {
        **details,
        "candidate_edges": len(candidates),
        "accepted_edges": len(accepted),
        "rejected_edges": len(rejected),
        "observation_multiset_preserved": preserved,
        "duplicate_frame_identity_count": duplicates,
        "accepted": accepted,
        "rejected": rejected,
    }
