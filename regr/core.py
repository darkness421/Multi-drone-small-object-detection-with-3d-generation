"""Stable method names and entrypoint for frozen REGR selection rules.

``regr`` is the final development-selected method reported in the revised
paper. Earlier v1/T/TG names remain available only to reproduce the development
history; their implementation and thresholds are not silently changed.
"""

from __future__ import annotations

from collections.abc import Callable

from . import confidence, variants


METHODS = (
    "none",
    "geometry-reid-greedy",
    "regr",
    "regr-v1",
    "regr-t",
    "regr-tg",
)

_IMPLEMENTATIONS = {
    "none": "no_refinement",
    "geometry-reid-greedy": "geometry_reid_greedy_guard",
    "regr": "regr_final",
    "regr-v1": "regr_v1",
    "regr-t": "regr_temporal_risk_05",
    "regr-tg": "regr_t_reliable_motion_min5",
}

PARAMETERS = {
    "maximum_gap_frames": 30,
    "geometry_radius_pixels": variants.GEOMETRY_RADIUS,
    "appearance_cosine_gate": variants.APPEARANCE_DISTANCE,
    "normalized_gap_weight": 0.05,
    "reciprocal_consensus_bonus": variants.RECIPROCAL_SUPPORT_BONUS,
    "sparse_consensus_boundary": 5,
    "minimum_motion_coverage": 0.80,
    "motion_fit_window_observations": 3,
    "motion_confidence_minimum": 0.50,
    "motion_normalization": "geometric_mean_endpoint_box_diagonal",
    "maximum_normalized_motion_residual": 1.0,
}


def resolve_method(method: str) -> str:
    """Return the frozen implementation name for a public method name."""
    try:
        return _IMPLEMENTATIONS[method]
    except KeyError as exc:
        choices = ", ".join(METHODS)
        raise ValueError(f"unknown method {method!r}; choose one of: {choices}") from exc


def select_edges(
    method: str,
    predictions: dict[int, list[dict]],
    candidates: list[dict],
) -> tuple[list[dict], Callable[[dict], tuple], dict]:
    """Select candidate edges using one frozen paper operating point.

    Args:
        method: One of :data:`METHODS`.
        predictions: Frame-indexed tracker observations. Coordinates are in
            native image pixels.
        candidates: Directed temporal edges produced by
            :func:`regr.graph.build_candidates`.

    Returns:
        Proposed edges, their deterministic union ordering, and an audit
        dictionary describing the selected rule and edge counts.
    """
    implementation = resolve_method(method)
    if method == "regr":
        proposed, sort_key, details = confidence.select(
            implementation, predictions, candidates
        )
    else:
        proposed, sort_key, details = variants.select(
            implementation,
            predictions,
            candidates,
        )
    return proposed, sort_key, {
        "method": method,
        "implementation": implementation,
        **details,
    }
