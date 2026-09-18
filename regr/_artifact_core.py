#!/usr/bin/env python3
"""Deterministic REGR-T variants with development-only abstention guards."""

from __future__ import annotations

from collections import defaultdict
from typing import Callable

import numpy as np


GEOMETRY_RADIUS = 55.0
APPEARANCE_DISTANCE = 0.30
APPEARANCE_MARGIN = 0.02
RECIPROCAL_SUPPORT_BONUS = 0.005

BASELINES = (
    "geometry_reid_greedy_guard",
    "regr_v1",
)

ENHANCEMENTS = (
    "regr_anchor_completion",
    "regr_dual_reciprocal",
    "regr_margin_reciprocal",
    "regr_cost_reciprocal",
    "regr_motion_reciprocal",
    "regr_consensus_anchor_completion",
    "regr_quality_anchor_completion",
    "regr_low_cost_anchor_completion",
    "regr_temporal_risk_05",
    "regr_temporal_risk_10",
    "regr_temporal_risk_15",
    "regr_t_motion_ratio_100",
    "regr_t_motion_ratio_125",
    "regr_t_consensus_min3",
    "regr_t_consensus_min5",
    "regr_t_sparse_motion_min3",
    "regr_t_sparse_motion_min5",
    "regr_t_reliable_motion_min3",
    "regr_t_reliable_motion_min5",
)

METHODS = ("no_refinement",) + BASELINES + ENHANCEMENTS


def edge_id(edge: dict) -> tuple[int, int]:
    return int(edge["earlier"]), int(edge["later"])


def fixed_gated(candidates: list[dict]) -> list[dict]:
    return [
        edge
        for edge in candidates
        if edge.get("cosine_distance") is not None
        and float(edge["endpoint_center_distance_pixels"]) <= GEOMETRY_RADIUS
        and float(edge["cosine_distance"]) <= APPEARANCE_DISTANCE
    ]


def reciprocal(edges: list[dict], key: Callable[[dict], tuple]) -> list[dict]:
    outgoing: dict[int, list[dict]] = defaultdict(list)
    incoming: dict[int, list[dict]] = defaultdict(list)
    for edge in edges:
        outgoing[int(edge["earlier"])].append(edge)
        incoming[int(edge["later"])].append(edge)
    best_out = {identity: min(values, key=key) for identity, values in outgoing.items()}
    best_in = {identity: min(values, key=key) for identity, values in incoming.items()}
    return [
        edge
        for edge in edges
        if best_out[int(edge["earlier"])] is edge
        and best_in[int(edge["later"])] is edge
    ]


def centers_by_track(predictions: dict[int, list[dict]]) -> dict[int, list[tuple[int, np.ndarray]]]:
    output: dict[int, list[tuple[int, np.ndarray]]] = defaultdict(list)
    for frame, rows in predictions.items():
        for row in rows:
            output[int(row["id"])].append((
                int(frame),
                np.asarray(
                    [float(row["x"]) + float(row["w"]) / 2.0,
                     float(row["y"]) + float(row["h"]) / 2.0],
                    dtype=float,
                ),
            ))
    for values in output.values():
        values.sort(key=lambda item: item[0])
    return dict(output)


def add_motion_residuals(edges: list[dict], predictions: dict[int, list[dict]]) -> None:
    tracks = centers_by_track(predictions)
    for edge in edges:
        source = tracks[int(edge["earlier"])]
        destination = tracks[int(edge["later"])]
        source_frame, source_center = source[-1]
        destination_frame, destination_center = destination[0]
        residuals = []
        if len(source) >= 2:
            previous_frame, previous_center = source[-2]
            duration = max(1, source_frame - previous_frame)
            velocity = (source_center - previous_center) / duration
            predicted = source_center + velocity * (destination_frame - source_frame)
            residuals.append(float(np.linalg.norm(predicted - destination_center)))
        if len(destination) >= 2:
            next_frame, next_center = destination[1]
            duration = max(1, next_frame - destination_frame)
            velocity = (next_center - destination_center) / duration
            predicted = destination_center - velocity * (destination_frame - source_frame)
            residuals.append(float(np.linalg.norm(predicted - source_center)))
        edge["motion_endpoint_residual_pixels"] = (
            float(np.mean(residuals))
            if residuals
            else float(edge["endpoint_center_distance_pixels"])
        )
        edge["motion_estimate_count"] = len(residuals)


def appearance_margins(edges: list[dict]) -> dict[tuple[int, int], float]:
    outgoing: dict[int, list[dict]] = defaultdict(list)
    incoming: dict[int, list[dict]] = defaultdict(list)
    for edge in edges:
        outgoing[int(edge["earlier"])].append(edge)
        incoming[int(edge["later"])].append(edge)

    def margin(edge: dict, values: list[dict]) -> float:
        ordered = sorted(values, key=appearance_key)
        if ordered[0] is not edge:
            return float("-inf")
        if len(ordered) == 1:
            return float("inf")
        return float(ordered[1]["cosine_distance"] - edge["cosine_distance"])

    return {
        edge_id(edge): min(
            margin(edge, outgoing[int(edge["earlier"])]),
            margin(edge, incoming[int(edge["later"])]),
        )
        for edge in edges
    }


def geometry_key(edge: dict) -> tuple:
    return (
        float(edge["endpoint_center_distance_pixels"]),
        float(edge["cosine_distance"]),
        int(edge["gap"]),
        int(edge["earlier"]),
        int(edge["later"]),
    )


def appearance_key(edge: dict) -> tuple:
    return (
        float(edge["cosine_distance"]),
        int(edge["gap"]),
        float(edge["endpoint_center_distance_pixels"]),
        int(edge["earlier"]),
        int(edge["later"]),
    )


def cost_key(edge: dict) -> tuple:
    return (
        float(edge["controlled_cost"]),
        int(edge["gap"]),
        int(edge["earlier"]),
        int(edge["later"]),
    )


def motion_key(edge: dict) -> tuple:
    return (
        float(edge["motion_endpoint_residual_pixels"]),
        float(edge["cosine_distance"]),
        int(edge["gap"]),
        int(edge["earlier"]),
        int(edge["later"]),
    )


def ordered_union(*groups: list[dict]) -> tuple[list[dict], dict[tuple[int, int], int]]:
    output = []
    priority = {}
    seen = set()
    for rank, group in enumerate(groups):
        for edge in group:
            identity = edge_id(edge)
            priority[identity] = min(priority.get(identity, rank), rank)
            if identity not in seen:
                output.append(edge)
                seen.add(identity)
    return output, priority


def select(method: str, predictions: dict[int, list[dict]], candidates: list[dict]):
    """Return proposed edges, deterministic union order, and audit details."""
    if method == "no_refinement":
        return [], appearance_key, {"gated_edges": 0, "proposed_edges": 0}

    gated = fixed_gated(candidates)
    add_motion_residuals(gated, predictions)
    historical = reciprocal(gated, geometry_key)
    appearance = reciprocal(gated, appearance_key)
    controlled = reciprocal(gated, cost_key)
    motion = reciprocal(gated, motion_key)

    if method == "geometry_reid_greedy_guard":
        proposed = gated
        sort_key = appearance_key
        details = {"selection": "all fixed-gate edges; appearance order"}
    elif method == "regr_v1":
        proposed = historical
        sort_key = appearance_key
        details = {"selection": "geometry-first reciprocal"}
    elif method == "regr_anchor_completion":
        proposed, priority = ordered_union(historical, gated)
        sort_key = lambda edge: (priority[edge_id(edge)],) + appearance_key(edge)
        details = {"selection": "REGR anchors, then all fixed-gate edges"}
    elif method == "regr_dual_reciprocal":
        proposed, priority = ordered_union(historical, appearance)
        sort_key = lambda edge: (priority[edge_id(edge)],) + appearance_key(edge)
        details = {"selection": "union of geometry- and appearance-reciprocal edges"}
    elif method == "regr_margin_reciprocal":
        margins = appearance_margins(gated)
        confident = [edge for edge in appearance if margins[edge_id(edge)] >= APPEARANCE_MARGIN]
        for edge in confident:
            edge["bidirectional_appearance_margin"] = margins[edge_id(edge)]
        proposed, priority = ordered_union(historical, confident)
        sort_key = lambda edge: (priority[edge_id(edge)],) + appearance_key(edge)
        details = {
            "selection": "REGR plus margin-qualified appearance-reciprocal edges",
            "appearance_margin": APPEARANCE_MARGIN,
            "margin_qualified_edges": len(confident),
        }
    elif method == "regr_cost_reciprocal":
        proposed, priority = ordered_union(historical, controlled)
        sort_key = lambda edge: (priority[edge_id(edge)],) + cost_key(edge)
        details = {"selection": "union of historical- and controlled-cost reciprocal edges"}
    elif method == "regr_motion_reciprocal":
        proposed, priority = ordered_union(historical, motion)
        sort_key = lambda edge: (priority[edge_id(edge)],) + motion_key(edge)
        details = {"selection": "union of historical- and motion-residual reciprocal edges"}
    elif method == "regr_consensus_anchor_completion":
        appearance_ids = {edge_id(edge) for edge in appearance}
        anchors = [edge for edge in historical if edge_id(edge) in appearance_ids]
        proposed, priority = ordered_union(anchors, gated)
        sort_key = lambda edge: (priority[edge_id(edge)],) + appearance_key(edge)
        details = {
            "selection": "geometry/appearance reciprocal consensus anchors, then fixed-gate appearance order",
            "promoted_anchor_edges": len(anchors),
        }
    elif method == "regr_quality_anchor_completion":
        anchors = [
            edge for edge in historical
            if float(edge["cosine_distance"]) <= 0.10 and int(edge["gap"]) <= 5
        ]
        proposed, priority = ordered_union(anchors, gated)
        sort_key = lambda edge: (priority[edge_id(edge)],) + appearance_key(edge)
        details = {
            "selection": "development-fixed high-quality REGR anchors, then fixed-gate appearance order",
            "anchor_appearance_max": 0.10,
            "anchor_gap_max": 5,
            "promoted_anchor_edges": len(anchors),
        }
    elif method == "regr_low_cost_anchor_completion":
        anchors = [
            edge for edge in historical
            if float(edge["controlled_cost"]) <= 0.30
        ]
        proposed, priority = ordered_union(anchors, gated)
        sort_key = lambda edge: (priority[edge_id(edge)],) + appearance_key(edge)
        details = {
            "selection": "development-fixed low-cost REGR anchors, then fixed-gate appearance order",
            "anchor_controlled_cost_max": 0.30,
            "promoted_anchor_edges": len(anchors),
        }
    elif method in {
        "regr_temporal_risk_05",
        "regr_temporal_risk_10",
        "regr_temporal_risk_15",
        "regr_t_motion_ratio_100",
        "regr_t_motion_ratio_125",
        "regr_t_consensus_min3",
        "regr_t_consensus_min5",
        "regr_t_sparse_motion_min3",
        "regr_t_sparse_motion_min5",
        "regr_t_reliable_motion_min3",
        "regr_t_reliable_motion_min5",
    }:
        gap_weight = {
            "regr_temporal_risk_05": 0.05,
            "regr_temporal_risk_10": 0.10,
            "regr_temporal_risk_15": 0.15,
            "regr_t_motion_ratio_100": 0.05,
            "regr_t_motion_ratio_125": 0.05,
            "regr_t_consensus_min3": 0.05,
            "regr_t_consensus_min5": 0.05,
            "regr_t_sparse_motion_min3": 0.05,
            "regr_t_sparse_motion_min5": 0.05,
            "regr_t_reliable_motion_min3": 0.05,
            "regr_t_reliable_motion_min5": 0.05,
        }[method]
        historical_ids = {edge_id(edge) for edge in historical}
        appearance_ids = {edge_id(edge) for edge in appearance}
        consensus_ids = historical_ids & appearance_ids

        def temporal_risk_key(edge: dict) -> tuple:
            score = (
                float(edge["cosine_distance"])
                + gap_weight * float(edge["gap"]) / 30.0
                - (RECIPROCAL_SUPPORT_BONUS if edge_id(edge) in consensus_ids else 0.0)
            )
            return (
                score,
                float(edge["cosine_distance"]),
                int(edge["gap"]),
                int(edge["earlier"]),
                int(edge["later"]),
            )

        proposed = gated
        if method in {"regr_t_motion_ratio_100", "regr_t_motion_ratio_125"}:
            ratio_max = {
                "regr_t_motion_ratio_100": 1.00,
                "regr_t_motion_ratio_125": 1.25,
            }[method]
            proposed = [
                edge
                for edge in gated
                if int(edge["motion_estimate_count"]) == 0
                or float(edge["motion_endpoint_residual_pixels"])
                / max(float(edge["endpoint_center_distance_pixels"]), 1e-9)
                <= ratio_max
            ]
        else:
            ratio_max = None

        if method in {"regr_t_consensus_min3", "regr_t_consensus_min5"}:
            minimum_consensus = {
                "regr_t_consensus_min3": 3,
                "regr_t_consensus_min5": 5,
            }[method]
            if len(consensus_ids) < minimum_consensus:
                proposed = []
        else:
            minimum_consensus = None

        if method in {"regr_t_sparse_motion_min3", "regr_t_sparse_motion_min5"}:
            sparse_boundary = {
                "regr_t_sparse_motion_min3": 3,
                "regr_t_sparse_motion_min5": 5,
            }[method]
            if len(consensus_ids) < sparse_boundary:
                proposed = [
                    edge
                    for edge in proposed
                    if int(edge["motion_estimate_count"]) > 0
                    and float(edge["motion_endpoint_residual_pixels"])
                    / max(float(edge["endpoint_center_distance_pixels"]), 1e-9)
                    <= 1.0
                ]
        else:
            sparse_boundary = None

        motion_coverage = (
            sum(int(edge["motion_estimate_count"]) > 0 for edge in gated) / len(gated)
            if gated
            else 0.0
        )
        if method in {"regr_t_reliable_motion_min3", "regr_t_reliable_motion_min5"}:
            reliable_boundary = {
                "regr_t_reliable_motion_min3": 3,
                "regr_t_reliable_motion_min5": 5,
            }[method]
            if len(consensus_ids) < reliable_boundary and motion_coverage >= 0.80:
                proposed = [
                    edge
                    for edge in proposed
                    if int(edge["motion_estimate_count"]) > 0
                    and float(edge["motion_endpoint_residual_pixels"])
                    / max(float(edge["endpoint_center_distance_pixels"]), 1e-9)
                    <= 1.0
                ]
        else:
            reliable_boundary = None

        sort_key = temporal_risk_key
        details = {
            "selection": (
                "fixed-gate edges ranked by appearance, temporal gap, and soft reciprocal consensus; "
                "optional development-fixed abstention"
            ),
            "gap_weight": gap_weight,
            "reciprocal_support_bonus": RECIPROCAL_SUPPORT_BONUS,
            "consensus_edges": len(consensus_ids),
            "motion_ratio_max": ratio_max,
            "minimum_consensus_edges": minimum_consensus,
            "sparse_motion_boundary": sparse_boundary,
            "reliable_motion_boundary": reliable_boundary,
            "motion_coverage": motion_coverage,
            "abstained": bool(gated and not proposed),
        }
    else:
        raise ValueError(f"unknown method: {method}")

    return proposed, sort_key, {
        "gated_edges": len(gated),
        "historical_reciprocal_edges": len(historical),
        "appearance_reciprocal_edges": len(appearance),
        "controlled_cost_reciprocal_edges": len(controlled),
        "motion_reciprocal_edges": len(motion),
        "proposed_edges": len(proposed),
        **details,
    }
