#!/usr/bin/env python3
"""GT-free edge verification and one-to-one temporal link solvers for ACE-V."""

from __future__ import annotations

from collections import defaultdict
from typing import Callable, Iterable

import numpy as np
from scipy.optimize import linear_sum_assignment


PAIR_NULL_COST = 1.0
OUTGOING_NULL_COST = 0.5
INCOMING_NULL_COST = 0.5
MOTION_SAMPLES = 3


def edge_key(edge: dict) -> tuple:
    return (
        float(edge["controlled_cost"]),
        int(edge["gap"]),
        int(edge["earlier"]),
        int(edge["later"]),
    )


def pair(edge: dict) -> tuple[int, int]:
    return int(edge["earlier"]), int(edge["later"])


def tracklet_rows(predictions: dict[int, list[dict]]) -> dict[int, list[tuple[int, dict]]]:
    output: dict[int, list[tuple[int, dict]]] = defaultdict(list)
    for frame, rows in predictions.items():
        for row in rows:
            output[int(row["id"])].append((int(frame), row))
    for identity, values in output.items():
        values.sort(key=lambda item: item[0])
        frames = [frame for frame, _ in values]
        if len(frames) != len(set(frames)):
            raise ValueError(f"tracklet {identity} contains duplicate frame observations")
    return dict(output)


def _centers(values: list[tuple[int, dict]]) -> tuple[np.ndarray, np.ndarray]:
    times = np.asarray([frame for frame, _ in values], dtype=float)
    centers = np.asarray(
        [
            [float(row["x"]) + float(row["w"]) / 2.0,
             float(row["y"]) + float(row["h"]) / 2.0]
            for _, row in values
        ],
        dtype=float,
    )
    return times, centers


def _linear_fit(values: list[tuple[int, dict]]) -> tuple[np.ndarray, np.ndarray, float]:
    times, centers = _centers(values)
    origin = float(np.mean(times))
    design = np.column_stack((times - origin, np.ones_like(times)))
    coefficients, _, _, _ = np.linalg.lstsq(design, centers, rcond=None)
    predicted = design @ coefficients
    rms = float(np.sqrt(np.mean(np.sum((predicted - centers) ** 2, axis=1))))

    def evaluate(time: float) -> np.ndarray:
        return np.asarray([time - origin, 1.0]) @ coefficients

    return evaluate, coefficients, rms


def _box_diagonal(row: dict) -> float:
    return float(np.hypot(float(row["w"]), float(row["h"])))


def motion_feature(
    rows: dict[int, list[tuple[int, dict]]],
    source: int,
    destination: int,
    samples: int = MOTION_SAMPLES,
) -> dict:
    source_values = rows.get(int(source), [])[-samples:]
    destination_values = rows.get(int(destination), [])[:samples]
    base = {
        "motion_source_observations": len(source_values),
        "motion_destination_observations": len(destination_values),
        "motion_available": False,
        "motion_missing_reason": None,
        "motion_midpoint_frame": None,
        "motion_endpoint_scale_pixels": None,
        "motion_disagreement_pixels": None,
        "motion_residual": None,
        "motion_source_fit_residual_pixels": None,
        "motion_destination_fit_residual_pixels": None,
    }
    if len(source_values) < 2 or len(destination_values) < 2:
        base["motion_missing_reason"] = "fewer_than_two_distinct_frames"
        return base
    source_end = source_values[-1][0]
    destination_start = destination_values[0][0]
    if source_end >= destination_start:
        base["motion_missing_reason"] = "not_strictly_forward"
        return base
    source_fit, _, source_rms = _linear_fit(source_values)
    destination_fit, _, destination_rms = _linear_fit(destination_values)
    midpoint = (source_end + destination_start) / 2.0
    disagreement = float(np.linalg.norm(source_fit(midpoint) - destination_fit(midpoint)))
    scale = (
        _box_diagonal(source_values[-1][1])
        + _box_diagonal(destination_values[0][1])
    ) / 2.0
    if not np.isfinite(scale) or scale <= 0:
        base["motion_missing_reason"] = "invalid_endpoint_box_scale"
        return base
    base.update({
        "motion_available": True,
        "motion_midpoint_frame": midpoint,
        "motion_endpoint_scale_pixels": scale,
        "motion_disagreement_pixels": disagreement,
        "motion_residual": disagreement / scale,
        "motion_source_fit_residual_pixels": source_rms,
        "motion_destination_fit_residual_pixels": destination_rms,
    })
    return base


def add_verification_features(
    candidates: Iterable[dict],
    predictions: dict[int, list[dict]],
    pair_null_cost: float = PAIR_NULL_COST,
    motion_samples: int = MOTION_SAMPLES,
) -> list[dict]:
    edges = [dict(edge) for edge in candidates]
    outgoing: dict[int, list[dict]] = defaultdict(list)
    incoming: dict[int, list[dict]] = defaultdict(list)
    for edge in edges:
        outgoing[int(edge["earlier"])].append(edge)
        incoming[int(edge["later"])].append(edge)
    rows = tracklet_rows(predictions)
    output = []
    for edge in edges:
        source, destination = pair(edge)
        edge_cost = float(edge["controlled_cost"])
        outgoing_alternatives = [
            float(other["controlled_cost"])
            for other in outgoing[source]
            if pair(other) != (source, destination)
        ]
        incoming_alternatives = [
            float(other["controlled_cost"])
            for other in incoming[destination]
            if pair(other) != (source, destination)
        ]
        outgoing_alternative = min([pair_null_cost, *outgoing_alternatives])
        incoming_alternative = min([pair_null_cost, *incoming_alternatives])
        outgoing_margin = outgoing_alternative - edge_cost
        incoming_margin = incoming_alternative - edge_cost
        ambiguity = max(0.0, -min(outgoing_margin, incoming_margin))
        output.append({
            **edge,
            "outgoing_alternative_cost": outgoing_alternative,
            "incoming_alternative_cost": incoming_alternative,
            "outgoing_margin": outgoing_margin,
            "incoming_margin": incoming_margin,
            "competition_ambiguity": ambiguity,
            "outgoing_candidate_count": len(outgoing[source]),
            "incoming_candidate_count": len(incoming[destination]),
            **motion_feature(rows, source, destination, motion_samples),
        })
    return output


def verifier_pass(edge: dict, family: str, tau_a: float, tau_m: float) -> bool:
    ambiguity_ok = float(edge["competition_ambiguity"]) <= float(tau_a)
    motion_available = bool(edge["motion_available"])
    motion_ok = motion_available and float(edge["motion_residual"]) <= float(tau_m)
    if family == "V_off":
        return True
    if family == "V_margin":
        return ambiguity_ok
    if family == "V_motion":
        return motion_ok if motion_available else True
    if family == "V_full":
        fallback = (
            float(edge["outgoing_margin"]) > 0
            and float(edge["incoming_margin"]) > 0
        )
        return ambiguity_ok and (motion_ok if motion_available else fallback)
    raise ValueError(f"unknown verifier family: {family}")


def soft_information_cost(edge: dict) -> float:
    ambiguity_term = min(float(edge["competition_ambiguity"]) / 0.10, 1.0)
    motion_term = (
        min(float(edge["motion_residual"]) / 8.0, 1.0)
        if edge["motion_available"] else 1.0
    )
    return float(np.mean([float(edge["controlled_cost"]), ambiguity_term, motion_term]))


def partial_hungarian(
    edges: Iterable[dict],
    cost: Callable[[dict], float] = lambda edge: float(edge["controlled_cost"]),
    outgoing_null_cost: float = OUTGOING_NULL_COST,
    incoming_null_cost: float = INCOMING_NULL_COST,
) -> list[dict]:
    """Solve one-to-one links with explicit null choices for both endpoints."""
    values = list(edges)
    if not values:
        return []
    sources = sorted({int(edge["earlier"]) for edge in values})
    destinations = sorted({int(edge["later"]) for edge in values})
    source_index = {identity: index for index, identity in enumerate(sources)}
    destination_index = {identity: index for index, identity in enumerate(destinations)}
    source_count = len(sources)
    destination_count = len(destinations)
    size = source_count + destination_count
    matrix = np.full((size, size), 1e9, dtype=float)
    lookup: dict[tuple[int, int], dict] = {}
    for edge in sorted(values, key=edge_key):
        row = source_index[int(edge["earlier"])]
        column = destination_index[int(edge["later"])]
        value = float(cost(edge))
        if value < matrix[row, column]:
            matrix[row, column] = value
            lookup[(row, column)] = edge
    for row in range(source_count):
        matrix[row, destination_count + row] = outgoing_null_cost
    for column in range(destination_count):
        matrix[source_count + column, column] = incoming_null_cost
    matrix[source_count:, destination_count:] = 0.0
    rows, columns = linear_sum_assignment(matrix)
    selected = [
        lookup[(row, column)]
        for row, column in zip(rows, columns)
        if row < source_count and column < destination_count
        and (row, column) in lookup
        and matrix[row, column] < outgoing_null_cost + incoming_null_cost
    ]
    return sorted(selected, key=edge_key)


def path_constrained_greedy(
    edges: Iterable[dict],
    cost: Callable[[dict], float] = lambda edge: float(edge["controlled_cost"]),
    pair_null_cost: float = PAIR_NULL_COST,
) -> list[dict]:
    selected = []
    used_sources: set[int] = set()
    used_destinations: set[int] = set()
    for edge in sorted(
        edges,
        key=lambda item: (cost(item), int(item["gap"]), *pair(item)),
    ):
        source, destination = pair(edge)
        if float(cost(edge)) >= pair_null_cost:
            continue
        if source in used_sources or destination in used_destinations:
            continue
        used_sources.add(source)
        used_destinations.add(destination)
        selected.append(edge)
    return selected


def filter_edges(
    edges: Iterable[dict], family: str, tau_a: float, tau_m: float
) -> list[dict]:
    return [edge for edge in edges if verifier_pass(edge, family, tau_a, tau_m)]


def assert_path_constraints(edges: Iterable[dict]) -> None:
    outgoing: set[int] = set()
    incoming: set[int] = set()
    successor: dict[int, int] = {}
    for edge in edges:
        source, destination = pair(edge)
        if source in outgoing:
            raise AssertionError(f"multiple successors for {source}")
        if destination in incoming:
            raise AssertionError(f"multiple predecessors for {destination}")
        outgoing.add(source)
        incoming.add(destination)
        successor[source] = destination
    for start in successor:
        seen = set()
        current = start
        while current in successor:
            if current in seen:
                raise AssertionError("cycle in temporal links")
            seen.add(current)
            current = successor[current]
