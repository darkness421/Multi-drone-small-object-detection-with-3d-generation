"""Public names and entrypoint for the frozen REGR selection rules.

The underlying artifact module is the implementation used for the reported
REGR-T and REGR-TG evaluations. This wrapper gives the paper variants concise
names without changing their selection behavior.
"""

from __future__ import annotations

from collections.abc import Callable

from . import _artifact_core


PAPER_METHODS = (
    "none",
    "geometry-reid-greedy",
    "regr-v1",
    "regr-t",
    "regr-tg",
)

_ARTIFACT_METHODS = {
    "none": "no_refinement",
    "geometry-reid-greedy": "geometry_reid_greedy_guard",
    "regr-v1": "regr_v1",
    "regr-t": "regr_temporal_risk_05",
    "regr-tg": "regr_t_reliable_motion_min5",
}

PAPER_PARAMETERS = {
    "maximum_gap_frames": 30,
    "geometry_radius_pixels": _artifact_core.GEOMETRY_RADIUS,
    "appearance_cosine_gate": _artifact_core.APPEARANCE_DISTANCE,
    "normalized_gap_weight": 0.05,
    "reciprocal_consensus_bonus": _artifact_core.RECIPROCAL_SUPPORT_BONUS,
    "sparse_consensus_boundary": 5,
    "minimum_motion_coverage": 0.80,
    "maximum_motion_residual_to_endpoint_ratio": 1.0,
}


def resolve_method(method: str) -> str:
    """Return the immutable artifact method name for a public paper name."""
    try:
        return _ARTIFACT_METHODS[method]
    except KeyError as exc:
        choices = ", ".join(PAPER_METHODS)
        raise ValueError(f"unknown method {method!r}; choose one of: {choices}") from exc


def select_edges(
    method: str,
    predictions: dict[int, list[dict]],
    candidates: list[dict],
) -> tuple[list[dict], Callable[[dict], tuple], dict]:
    """Select candidate edges using one frozen paper operating point.

    Args:
        method: One of :data:`PAPER_METHODS`.
        predictions: Frame-indexed tracker observations. Coordinates are in
            native image pixels.
        candidates: Directed temporal edges produced by
            :func:`regr.graph.build_candidates`.

    Returns:
        Proposed edges, their deterministic union ordering, and an audit
        dictionary describing the selected rule and edge counts.
    """
    artifact_method = resolve_method(method)
    proposed, sort_key, details = _artifact_core.select(
        artifact_method,
        predictions,
        candidates,
    )
    return proposed, sort_key, {
        "paper_method": method,
        "artifact_method": artifact_method,
        **details,
    }
