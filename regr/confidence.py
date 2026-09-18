"""Candidate-specific motion confidence and competition-aware REGR linking.

This module contains the pre-registered A/B development search. It never reads
ground-truth identity. All coordinates are native-image pixels and all temporal
fits use the actual frame indices supplied by the frozen tracker output.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
import json
import math
from pathlib import Path
from typing import Callable

import numpy as np


MAX_GAP = 30
GEOMETRY_RADIUS = 55.0
APPEARANCE_DISTANCE = 0.30

SEARCH_CONFIG_PATH = Path(__file__).resolve().parents[1] / "configs" / "regr_ab_search.json"
SEARCH_PROTOCOL = json.loads(SEARCH_CONFIG_PATH.read_text(encoding="utf-8"))
STAGE2_CONFIG_PATH = Path(__file__).resolve().parents[1] / "configs" / "regr_ab_stage2_search.json"
STAGE2_PROTOCOL = json.loads(STAGE2_CONFIG_PATH.read_text(encoding="utf-8"))
SEARCH_SPECS = {
    row["name"]: row
    for protocol in (SEARCH_PROTOCOL, STAGE2_PROTOCOL)
    for row in protocol["configurations"]
}

BASELINE_METHODS = (
    "no_refinement",
    "geometry_greedy",
    "geometry_reid_greedy",
    "partial_hungarian_u100",
    "partial_hungarian_u080",
    "partial_hungarian_u070",
    "regr_t",
    "regr_tg_old",
)
FINAL_METHODS = (
    "regr_final",
    "regr_final_no_gap",
    "regr_final_no_reciprocal",
    "regr_final_no_motion",
    "regr_final_motion_always",
)
METHODS = BASELINE_METHODS + tuple(SEARCH_SPECS) + FINAL_METHODS


@dataclass(frozen=True)
class MotionFit:
    anchor_frame: int
    anchor_center: np.ndarray
    velocity: np.ndarray
    point_count: int
    span_frames: int
    fit_rmse_pixels: float
    holdout_error_pixels: float
    velocity_variation_pixels_per_frame: float
    object_scale_pixels: float
    confidence: float


def edge_id(edge: dict) -> tuple[int, int]:
    return int(edge["earlier"]), int(edge["later"])


def fixed_gated(candidates: list[dict]) -> list[dict]:
    return [
        dict(edge)
        for edge in candidates
        if edge.get("cosine_distance") is not None
        and int(edge["gap"]) <= MAX_GAP
        and float(edge["endpoint_center_distance_pixels"]) <= GEOMETRY_RADIUS
        and float(edge["cosine_distance"]) <= APPEARANCE_DISTANCE
    ]


def observations_by_track(
    predictions: dict[int, list[dict]],
) -> dict[int, list[tuple[int, np.ndarray, float]]]:
    tracks: dict[int, list[tuple[int, np.ndarray, float]]] = defaultdict(list)
    for frame, rows in predictions.items():
        for row in rows:
            center = np.asarray(
                [
                    float(row["x"]) + float(row["w"]) / 2.0,
                    float(row["y"]) + float(row["h"]) / 2.0,
                ],
                dtype=float,
            )
            scale = float(math.hypot(float(row["w"]), float(row["h"])))
            tracks[int(row["id"])].append((int(frame), center, max(scale, 1.0)))
    for values in tracks.values():
        values.sort(key=lambda item: item[0])
    return dict(tracks)


def _linear_fit(frames: np.ndarray, centers: np.ndarray) -> tuple[np.ndarray, np.ndarray, float]:
    origin = float(frames[0])
    design = np.column_stack([np.ones(len(frames)), frames - origin])
    coefficients, _, _, _ = np.linalg.lstsq(design, centers, rcond=None)
    fitted = design @ coefficients
    rmse = float(np.sqrt(np.mean(np.sum((fitted - centers) ** 2, axis=1))))
    return coefficients[0], coefficients[1], rmse


def _motion_fit(
    observations: list[tuple[int, np.ndarray, float]],
    window: int,
    endpoint: str,
) -> MotionFit | None:
    if window < 3 or len(observations) < 3:
        return None
    selected = observations[-window:] if endpoint == "source" else observations[:window]
    frames = np.asarray([row[0] for row in selected], dtype=float)
    centers = np.stack([row[1] for row in selected])
    scales = np.asarray([row[2] for row in selected], dtype=float)
    if len(np.unique(frames)) < 3:
        return None
    origin_center, velocity, rmse = _linear_fit(frames, centers)
    anchor_index = -1 if endpoint == "source" else 0
    anchor_frame = int(frames[anchor_index])
    anchor_center = centers[anchor_index]

    if endpoint == "source":
        train_frames, train_centers = frames[:-1], centers[:-1]
        target_frame, target_center = frames[-1], centers[-1]
    else:
        train_frames, train_centers = frames[1:], centers[1:]
        target_frame, target_center = frames[0], centers[0]
    holdout_origin, holdout_velocity, _ = _linear_fit(train_frames, train_centers)
    holdout_prediction = holdout_origin + holdout_velocity * (target_frame - train_frames[0])
    holdout_error = float(np.linalg.norm(holdout_prediction - target_center))

    intervals = np.diff(frames)
    step_velocities = np.diff(centers, axis=0) / intervals[:, None]
    if len(step_velocities) > 1:
        velocity_variation = float(
            np.sqrt(np.mean(np.sum((step_velocities - step_velocities.mean(axis=0)) ** 2, axis=1)))
        )
    else:
        velocity_variation = float("inf")

    scale = max(float(np.median(scales)), 1.0)
    median_interval = max(float(np.median(intervals)), 1.0)
    normalized_internal_error = (
        holdout_error + rmse + 0.5 * velocity_variation * median_interval
    ) / scale
    support = 0.70 + 0.30 * min(1.0, (len(selected) - 3) / 2.0)
    expected_span = max(2.0, float(len(selected) - 1))
    span_support = min(1.0, float(frames[-1] - frames[0]) / expected_span)
    confidence = float(support * span_support * math.exp(-normalized_internal_error))
    return MotionFit(
        anchor_frame=anchor_frame,
        anchor_center=anchor_center,
        velocity=velocity,
        point_count=len(selected),
        span_frames=int(frames[-1] - frames[0]),
        fit_rmse_pixels=rmse,
        holdout_error_pixels=holdout_error,
        velocity_variation_pixels_per_frame=velocity_variation,
        object_scale_pixels=scale,
        confidence=max(0.0, min(1.0, confidence)),
    )


def add_candidate_motion_features(
    edges: list[dict],
    predictions: dict[int, list[dict]],
    window: int,
    normalization: str,
) -> None:
    tracks = observations_by_track(predictions)
    fits: dict[tuple[int, str], MotionFit | None] = {}

    def cached_fit(identity: int, endpoint: str) -> MotionFit | None:
        key = (identity, endpoint)
        if key not in fits:
            fits[key] = _motion_fit(tracks[identity], window, endpoint)
        return fits[key]

    for edge in edges:
        source_id, destination_id = edge_id(edge)
        source_fit = cached_fit(source_id, "source")
        destination_fit = cached_fit(destination_id, "destination")
        edge["motion_window"] = int(window)
        edge["motion_normalization"] = normalization
        edge["source_motion_confidence"] = 0.0 if source_fit is None else source_fit.confidence
        edge["destination_motion_confidence"] = 0.0 if destination_fit is None else destination_fit.confidence
        edge["motion_confidence"] = (
            0.0
            if source_fit is None or destination_fit is None
            else float(math.sqrt(source_fit.confidence * destination_fit.confidence))
        )
        edge["motion_estimate_count"] = int(source_fit is not None) + int(destination_fit is not None)
        residuals = []
        uncertainty_terms = []
        source_observations = tracks[source_id]
        destination_observations = tracks[destination_id]
        source_frame, source_center, source_scale = source_observations[-1]
        destination_frame, destination_center, destination_scale = destination_observations[0]
        gap = float(destination_frame - source_frame)
        if source_fit is not None:
            source_prediction = source_fit.anchor_center + source_fit.velocity * (
                destination_frame - source_fit.anchor_frame
            )
            residuals.append(float(np.linalg.norm(source_prediction - destination_center)))
            uncertainty_terms.append(
                source_fit.holdout_error_pixels
                + source_fit.fit_rmse_pixels
                + abs(gap) * source_fit.velocity_variation_pixels_per_frame
            )
            edge["source_forward_x"] = float(source_prediction[0])
            edge["source_forward_y"] = float(source_prediction[1])
        if destination_fit is not None:
            destination_prediction = destination_fit.anchor_center + destination_fit.velocity * (
                source_frame - destination_fit.anchor_frame
            )
            residuals.append(float(np.linalg.norm(destination_prediction - source_center)))
            uncertainty_terms.append(
                destination_fit.holdout_error_pixels
                + destination_fit.fit_rmse_pixels
                + abs(gap) * destination_fit.velocity_variation_pixels_per_frame
            )
            edge["destination_backward_x"] = float(destination_prediction[0])
            edge["destination_backward_y"] = float(destination_prediction[1])
        residual = float(np.mean(residuals)) if residuals else None
        uncertainty = float(np.mean(uncertainty_terms)) if uncertainty_terms else None
        if normalization == "endpoint":
            denominator = max(float(edge["endpoint_center_distance_pixels"]), 1.0)
        elif normalization == "object_scale":
            denominator = max(float(math.sqrt(source_scale * destination_scale)), 1.0)
        elif normalization == "none":
            denominator = 1.0
        else:
            raise ValueError(f"unknown motion normalization: {normalization}")
        edge["motion_residual_pixels"] = residual
        edge["motion_uncertainty_pixels"] = uncertainty
        edge["motion_normalizer_pixels"] = denominator
        edge["motion_normalized_residual"] = (
            residual / denominator if residual is not None else None
        )


def add_legacy_motion_features(
    edges: list[dict], predictions: dict[int, list[dict]]
) -> None:
    """Reproduce the previous two-observation endpoint residual exactly."""
    tracks = observations_by_track(predictions)
    for edge in edges:
        source = tracks[int(edge["earlier"])]
        destination = tracks[int(edge["later"])]
        source_frame, source_center, _ = source[-1]
        destination_frame, destination_center, _ = destination[0]
        residuals = []
        if len(source) >= 2:
            previous_frame, previous_center, _ = source[-2]
            duration = max(1, source_frame - previous_frame)
            velocity = (source_center - previous_center) / duration
            predicted = source_center + velocity * (destination_frame - source_frame)
            residuals.append(float(np.linalg.norm(predicted - destination_center)))
        if len(destination) >= 2:
            next_frame, next_center, _ = destination[1]
            duration = max(1, next_frame - destination_frame)
            velocity = (next_center - destination_center) / duration
            predicted = destination_center - velocity * (destination_frame - source_frame)
            residuals.append(float(np.linalg.norm(predicted - source_center)))
        residual = (
            float(np.mean(residuals))
            if residuals
            else float(edge["endpoint_center_distance_pixels"])
        )
        edge["motion_estimate_count"] = len(residuals)
        edge["motion_residual_pixels"] = residual
        edge["motion_normalized_residual"] = residual / max(
            float(edge["endpoint_center_distance_pixels"]), 1e-9
        )


def appearance_key(edge: dict) -> tuple:
    return (
        float(edge["cosine_distance"]),
        int(edge["gap"]),
        float(edge["endpoint_center_distance_pixels"]),
        int(edge["earlier"]),
        int(edge["later"]),
    )


def geometry_key(edge: dict) -> tuple:
    return (
        float(edge["endpoint_center_distance_pixels"]),
        float(edge["cosine_distance"]),
        int(edge["gap"]),
        int(edge["earlier"]),
        int(edge["later"]),
    )


def controlled_cost(edge: dict) -> float:
    if edge.get("controlled_cost") is not None:
        return float(edge["controlled_cost"])
    return float(
        (
            float(edge["cosine_distance"]) / APPEARANCE_DISTANCE
            + float(edge["endpoint_center_distance_pixels"]) / GEOMETRY_RADIUS
            + float(edge["gap"]) / MAX_GAP
        )
        / 3.0
    )


def evidence_cost(edge: dict, include_motion: bool, confidence_min: float) -> float:
    appearance = float(edge["cosine_distance"]) / APPEARANCE_DISTANCE
    geometry = float(edge["endpoint_center_distance_pixels"]) / GEOMETRY_RADIUS
    gap = float(edge["gap"]) / MAX_GAP
    base = (0.50 * appearance + 0.25 * geometry + 0.10 * gap) / 0.85
    informative = include_motion and float(edge.get("motion_confidence", 0.0)) >= confidence_min
    if informative:
        motion = min(float(edge["motion_normalized_residual"]), 2.0)
        value = 0.85 * base + 0.15 * motion
    else:
        value = base
    edge["evidence_base_cost"] = float(base)
    edge["evidence_cost"] = float(value)
    edge["motion_informative"] = bool(informative)
    return float(value)


def _reciprocal(edges: list[dict], key: Callable[[dict], tuple]) -> set[tuple[int, int]]:
    outgoing: dict[int, list[dict]] = defaultdict(list)
    incoming: dict[int, list[dict]] = defaultdict(list)
    for edge in edges:
        outgoing[int(edge["earlier"])].append(edge)
        incoming[int(edge["later"])].append(edge)
    best_out = {identity: min(values, key=key) for identity, values in outgoing.items()}
    best_in = {identity: min(values, key=key) for identity, values in incoming.items()}
    return {
        edge_id(edge)
        for edge in edges
        if best_out[int(edge["earlier"])] is edge and best_in[int(edge["later"])] is edge
    }


def _partial_hungarian(
    edges: list[dict],
    cost: Callable[[dict], float],
    unmatched_cost: float,
) -> list[dict]:
    try:
        from scipy.optimize import linear_sum_assignment
    except ImportError as exc:  # pragma: no cover - exercised in minimal installs
        raise RuntimeError(
            "partial-Hungarian controls require the optional evaluation dependency "
            "'scipy'; install regr-aerial-mot[evaluation]"
        ) from exc
    valid = [edge for edge in edges if cost(edge) < unmatched_cost]
    if not valid:
        return []
    sources = sorted({int(edge["earlier"]) for edge in valid})
    destinations = sorted({int(edge["later"]) for edge in valid})
    row_index = {identity: index for index, identity in enumerate(sources)}
    column_index = {identity: index for index, identity in enumerate(destinations)}
    matrix = np.full((len(sources), len(destinations) + len(sources)), 1e6, dtype=float)
    lookup: dict[tuple[int, int], dict] = {}
    for edge in valid:
        row = row_index[int(edge["earlier"])]
        column = column_index[int(edge["later"])]
        value = cost(edge)
        previous = lookup.get((row, column))
        if previous is None or (value, edge_id(edge)) < (cost(previous), edge_id(previous)):
            matrix[row, column] = value
            lookup[(row, column)] = edge
    for row in range(len(sources)):
        matrix[row, len(destinations) + row] = unmatched_cost
    rows, columns = linear_sum_assignment(matrix)
    return [
        lookup[(row, column)]
        for row, column in zip(rows, columns)
        if column < len(destinations) and matrix[row, column] < unmatched_cost
    ]


def _competition_margins(
    edges: list[dict],
    cost: Callable[[dict], float],
    unmatched_cost: float,
) -> dict[tuple[int, int], float]:
    outgoing: dict[int, list[dict]] = defaultdict(list)
    incoming: dict[int, list[dict]] = defaultdict(list)
    for edge in edges:
        outgoing[int(edge["earlier"])].append(edge)
        incoming[int(edge["later"])].append(edge)
    margins = {}
    for edge in edges:
        identity = edge_id(edge)
        alternatives_out = [cost(item) for item in outgoing[identity[0]] if item is not edge]
        alternatives_in = [cost(item) for item in incoming[identity[1]] if item is not edge]
        out_alternative = min(alternatives_out + [unmatched_cost])
        in_alternative = min(alternatives_in + [unmatched_cost])
        margins[identity] = float(min(out_alternative, in_alternative) - cost(edge))
    return margins


def competition_assignment(
    edges: list[dict],
    cost: Callable[[dict], float],
    unmatched_cost: float,
    minimum_margin: float,
) -> tuple[list[dict], int]:
    remaining = list(edges)
    reassignments = 0
    while remaining:
        selected = _partial_hungarian(remaining, cost, unmatched_cost)
        margins = _competition_margins(remaining, cost, unmatched_cost)
        rejected = [edge for edge in selected if margins[edge_id(edge)] + 1e-12 < minimum_margin]
        if not rejected:
            for edge in remaining:
                edge["competition_margin"] = margins[edge_id(edge)]
            return selected, reassignments
        rejected_ids = {edge_id(edge) for edge in rejected}
        remaining = [edge for edge in remaining if edge_id(edge) not in rejected_ids]
        reassignments += 1
    return [], reassignments


def _old_tg_filter(edges: list[dict], predictions: dict[int, list[dict]]) -> tuple[list[dict], bool]:
    add_legacy_motion_features(edges, predictions)
    geometry_ids = _reciprocal(edges, geometry_key)
    appearance_ids = _reciprocal(edges, appearance_key)
    consensus = geometry_ids & appearance_ids
    coverage = sum(int(edge["motion_estimate_count"]) > 0 for edge in edges) / len(edges) if edges else 0.0
    active = len(consensus) < 5 and coverage >= 0.80
    if not active:
        return edges, False
    return [
        edge
        for edge in edges
        if int(edge["motion_estimate_count"]) > 0
        and float(edge["motion_normalized_residual"]) <= 1.0
    ], True


def _temporal_key(
    edges: list[dict],
    gap_weight: float = 0.05,
    reciprocal_bonus: float = 0.005,
) -> Callable[[dict], tuple]:
    geometry_ids = _reciprocal(edges, geometry_key)
    appearance_ids = _reciprocal(edges, appearance_key)
    consensus = geometry_ids & appearance_ids

    def key(edge: dict) -> tuple:
        score = (
            float(edge["cosine_distance"])
            + gap_weight * float(edge["gap"]) / MAX_GAP
            - (reciprocal_bonus if edge_id(edge) in consensus else 0.0)
        )
        edge["temporal_risk"] = score
        return score, float(edge["cosine_distance"]), int(edge["gap"]), *edge_id(edge)

    return key


def _conditional_motion_filter(
    edges: list[dict],
    confidence_min: float,
    ratio_max: float,
) -> tuple[list[dict], dict]:
    geometry_ids = _reciprocal(edges, geometry_key)
    appearance_ids = _reciprocal(edges, appearance_key)
    consensus = geometry_ids & appearance_ids
    informative = [
        edge for edge in edges
        if float(edge.get("motion_confidence", 0.0)) >= confidence_min
    ]
    coverage = len(informative) / len(edges) if edges else 0.0
    active = len(consensus) < 5 and coverage >= 0.80
    if not active:
        return list(edges), {
            "guard_active": False,
            "reciprocal_consensus_count": len(consensus),
            "reliable_motion_edge_fraction": coverage,
        }
    admissible = [
        edge for edge in edges
        if float(edge.get("motion_confidence", 0.0)) < confidence_min
        or float(edge["motion_normalized_residual"]) <= ratio_max
    ]
    return admissible, {
        "guard_active": True,
        "reciprocal_consensus_count": len(consensus),
        "reliable_motion_edge_fraction": coverage,
    }


def select(
    method: str,
    predictions: dict[int, list[dict]],
    candidates: list[dict],
) -> tuple[list[dict], Callable[[dict], tuple], dict]:
    """Return proposed links, deterministic component order, and audit data."""
    if method == "no_refinement":
        return [], appearance_key, {"gated_edges": 0, "proposed_edges": 0, "candidate_decisions": []}

    gated = fixed_gated(candidates)
    if method == "geometry_greedy":
        geometry_edges = [
            dict(edge)
            for edge in candidates
            if int(edge["gap"]) <= MAX_GAP
            and float(edge["endpoint_center_distance_pixels"]) <= GEOMETRY_RADIUS
        ]
        return geometry_edges, geometry_key, {
            "selection": "geometry-only greedy",
            "gated_edges": len(geometry_edges),
            "proposed_edges": len(geometry_edges),
            "candidate_decisions": geometry_edges,
        }
    if method == "geometry_reid_greedy":
        return gated, appearance_key, {
            "selection": "fixed-gate appearance-order greedy",
            "gated_edges": len(gated),
            "proposed_edges": len(gated),
            "candidate_decisions": gated,
        }
    if method.startswith("partial_hungarian_u"):
        unmatched_cost = float(method.rsplit("u", 1)[1]) / 100.0
        proposed = _partial_hungarian(gated, controlled_cost, unmatched_cost)
        return proposed, lambda edge: (controlled_cost(edge), int(edge["gap"]), *edge_id(edge)), {
            "selection": "controlled-cost partial Hungarian",
            "unmatched_cost": unmatched_cost,
            "gated_edges": len(gated),
            "proposed_edges": len(proposed),
            "candidate_decisions": gated,
        }
    if method in {"regr_t", "regr_tg_old"}:
        if method == "regr_tg_old":
            proposed, guard_active = _old_tg_filter(gated, predictions)
        else:
            proposed, guard_active = gated, False
        key = _temporal_key(gated)
        return proposed, key, {
            "selection": "legacy temporal risk with optional graph-wide guard",
            "guard_active": guard_active,
            "gated_edges": len(gated),
            "proposed_edges": len(proposed),
            "candidate_decisions": gated,
        }

    if method in FINAL_METHODS:
        gap_weight = 0.0 if method == "regr_final_no_gap" else 0.05
        reciprocal_bonus = 0.0 if method == "regr_final_no_reciprocal" else 0.005
        temporal_key = _temporal_key(gated, gap_weight, reciprocal_bonus)
        if method == "regr_final_no_motion":
            admissible = list(gated)
            activation = {
                "guard_active": False,
                "reciprocal_consensus_count": len(
                    _reciprocal(gated, geometry_key) & _reciprocal(gated, appearance_key)
                ),
                "reliable_motion_edge_fraction": 0.0,
            }
        else:
            add_candidate_motion_features(gated, predictions, 3, "object_scale")
            for edge in gated:
                edge["motion_informative"] = bool(
                    float(edge["motion_confidence"]) >= 0.50
                )
            if method == "regr_final_motion_always":
                admissible = [
                    edge for edge in gated
                    if not edge["motion_informative"]
                    or float(edge["motion_normalized_residual"]) <= 1.0
                ]
                activation = {
                    "guard_active": True,
                    "reciprocal_consensus_count": len(
                        _reciprocal(gated, geometry_key) & _reciprocal(gated, appearance_key)
                    ),
                    "reliable_motion_edge_fraction": (
                        sum(edge["motion_informative"] for edge in gated) / len(gated)
                        if gated else 0.0
                    ),
                }
            else:
                admissible, activation = _conditional_motion_filter(gated, 0.50, 1.0)
        proposed_ids = {edge_id(edge) for edge in admissible}
        for edge in gated:
            edge["proposed"] = edge_id(edge) in proposed_ids
            edge["decision_reason"] = (
                "proposed" if edge["proposed"] else "conditional_reliable_motion_inconsistent"
            )
        return admissible, temporal_key, {
            "selection": "frozen final conditional candidate-specific motion confidence",
            "family": "FINAL_ABLATION" if method != "regr_final" else "FINAL",
            "solver": "greedy",
            "window": 0 if method == "regr_final_no_motion" else 3,
            "motion_normalization": "none" if method == "regr_final_no_motion" else "object_scale",
            "motion_confidence_min": 0.50,
            "motion_ratio_max": 1.0,
            "gap_weight": gap_weight,
            "reciprocal_bonus": reciprocal_bonus,
            **activation,
            "gated_edges": len(gated),
            "motion_informative_edges": sum(
                bool(edge.get("motion_informative", False)) for edge in gated
            ),
            "motion_rejected_edges": len(gated) - len(admissible),
            "proposed_edges": len(admissible),
            "candidate_decisions": gated,
        }

    try:
        spec = SEARCH_SPECS[method]
    except KeyError as exc:
        raise ValueError(f"unknown method: {method}") from exc

    family = spec["family"]
    if family == "A2_CONDITIONAL":
        add_candidate_motion_features(
            gated,
            predictions,
            int(spec["window"]),
            str(spec["motion_normalization"]),
        )
        for edge in gated:
            edge["motion_informative"] = bool(
                float(edge["motion_confidence"]) >= float(spec["motion_confidence_min"])
            )
        admissible, activation = _conditional_motion_filter(
            gated,
            float(spec["motion_confidence_min"]),
            float(spec["motion_ratio_max"]),
        )
        temporal_key = _temporal_key(gated)
        if spec["solver"] == "greedy":
            proposed = admissible
        elif spec["solver"] == "hungarian":
            proposed = _partial_hungarian(
                admissible,
                lambda edge: float(temporal_key(edge)[0]),
                float(spec["unmatched_cost"]),
            )
        else:
            raise ValueError(f"unknown solver: {spec['solver']}")
        proposed_ids = {edge_id(edge) for edge in proposed}
        admissible_ids = {edge_id(edge) for edge in admissible}
        for edge in gated:
            identity = edge_id(edge)
            edge["proposed"] = identity in proposed_ids
            if identity not in admissible_ids:
                edge["decision_reason"] = "conditional_reliable_motion_inconsistent"
            elif edge["proposed"]:
                edge["decision_reason"] = "proposed"
            else:
                edge["decision_reason"] = "not_selected_by_assignment"
        return proposed, temporal_key, {
            "selection": "legacy temporal order plus conditionally activated candidate-specific motion confidence",
            "family": family,
            "solver": spec["solver"],
            "window": int(spec["window"]),
            "motion_normalization": spec["motion_normalization"],
            "motion_confidence_min": float(spec["motion_confidence_min"]),
            "motion_ratio_max": float(spec["motion_ratio_max"]),
            "unmatched_cost": float(spec["unmatched_cost"]),
            **activation,
            "gated_edges": len(gated),
            "motion_informative_edges": sum(
                bool(edge.get("motion_informative", False)) for edge in gated
            ),
            "motion_rejected_edges": len(gated) - len(admissible),
            "proposed_edges": len(proposed),
            "candidate_decisions": gated,
        }
    if family in {"A", "AB"}:
        add_candidate_motion_features(
            gated,
            predictions,
            int(spec["window"]),
            str(spec["motion_normalization"]),
        )
    if family == "A":
        for edge in gated:
            edge["motion_informative"] = bool(
                float(edge["motion_confidence"]) >= float(spec["motion_confidence_min"])
            )
        admissible = [
            edge
            for edge in gated
            if not edge["motion_informative"]
            or float(edge["motion_normalized_residual"]) <= float(spec["motion_ratio_max"])
        ]
        proposed = _partial_hungarian(admissible, controlled_cost, float(spec["unmatched_cost"]))
        key = lambda edge: (controlled_cost(edge), int(edge["gap"]), *edge_id(edge))
        reassignments = 0
    else:
        include_motion = family == "AB"
        for edge in gated:
            evidence_cost(edge, include_motion, float(spec["motion_confidence_min"]))
        admissible = [
            edge
            for edge in gated
            if not bool(edge.get("motion_informative", False))
            or float(edge["motion_normalized_residual"]) <= float(spec["motion_ratio_max"])
        ]
        cost = lambda edge: float(edge["evidence_cost"])
        if spec["solver"] == "hungarian":
            proposed, reassignments = competition_assignment(
                admissible,
                cost,
                float(spec["unmatched_cost"]),
                float(spec["competition_margin"]),
            )
        elif spec["solver"] == "greedy":
            margins = _competition_margins(admissible, cost, float(spec["unmatched_cost"]))
            for edge in admissible:
                edge["competition_margin"] = margins[edge_id(edge)]
            proposed = [
                edge
                for edge in admissible
                if cost(edge) < float(spec["unmatched_cost"])
                and margins[edge_id(edge)] + 1e-12 >= float(spec["competition_margin"])
            ]
            reassignments = 0
        else:
            raise ValueError(f"unknown solver: {spec['solver']}")
        key = lambda edge: (float(edge["evidence_cost"]), int(edge["gap"]), *edge_id(edge))

    proposed_ids = {edge_id(edge) for edge in proposed}
    for edge in gated:
        edge["proposed"] = edge_id(edge) in proposed_ids
        if edge not in admissible:
            edge["decision_reason"] = "reliable_motion_inconsistent"
        elif edge["proposed"]:
            edge["decision_reason"] = "proposed"
        elif family in {"B", "AB"} and float(edge.get("evidence_cost", 1e9)) >= float(spec["unmatched_cost"]):
            edge["decision_reason"] = "worse_than_unmatched"
        elif family in {"B", "AB"} and float(edge.get("competition_margin", -1e9)) < float(spec["competition_margin"]):
            edge["decision_reason"] = "insufficient_competition_margin"
        else:
            edge["decision_reason"] = "not_selected_by_assignment"
    return proposed, key, {
        "selection": "pre-registered candidate-specific confidence and competition-aware linking",
        "family": family,
        "solver": spec["solver"],
        "window": int(spec["window"]),
        "motion_normalization": spec["motion_normalization"],
        "motion_confidence_min": float(spec["motion_confidence_min"]),
        "motion_ratio_max": float(spec["motion_ratio_max"]),
        "unmatched_cost": float(spec["unmatched_cost"]),
        "competition_margin_min": float(spec["competition_margin"]),
        "reassignment_rounds": int(reassignments),
        "gated_edges": len(gated),
        "motion_informative_edges": sum(bool(edge.get("motion_informative", False)) for edge in gated),
        "motion_rejected_edges": len(gated) - len(admissible),
        "proposed_edges": len(proposed),
        "candidate_decisions": gated,
    }
