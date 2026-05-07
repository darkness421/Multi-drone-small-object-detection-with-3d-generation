"""Pairwise evidence alignment costs and reliability weights."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Sequence

from evidence import EvidenceToken
from evidence.uncertainty import softmax


def euclidean(a: Sequence[float], b: Sequence[float]) -> float:
    if not a or not b:
        return 0.0
    n = min(len(a), len(b))
    return math.sqrt(sum((float(a[i]) - float(b[i])) ** 2 for i in range(n)))


def l1(a: Sequence[float], b: Sequence[float]) -> float:
    if not a or not b:
        return 0.0
    n = min(len(a), len(b))
    return sum(abs(float(a[i]) - float(b[i])) for i in range(n))


def class_distance(e_i: EvidenceToken, e_j: EvidenceToken) -> float:
    p_i = softmax(e_i.class_logits)
    p_j = softmax(e_j.class_logits)
    return 0.5 * l1(p_i, p_j)


def geometry_distance(e_i: EvidenceToken, e_j: EvidenceToken) -> float:
    pose_i = e_i.uav_pose or e_i.metadata.get("center_3d", [])
    pose_j = e_j.uav_pose or e_j.metadata.get("center_3d", [])
    return euclidean(pose_i, pose_j)


def resolution_score(token: EvidenceToken, reference_area: float = 1024.0) -> float:
    return min(1.0, max(0.0, token.bbox_area / reference_area))


@dataclass(slots=True)
class AlignmentWeights:
    lambda_app: float = 1.0
    lambda_geo: float = 1.0
    lambda_cls: float = 1.0
    lambda_res: float = 0.5
    lambda_time: float = 0.2
    lambda_unc: float = 0.5


def pairwise_evidence_cost(e_i: EvidenceToken, e_j: EvidenceToken, weights: AlignmentWeights | None = None) -> float:
    weights = weights or AlignmentWeights()
    appearance = euclidean(e_i.crop_feature, e_j.crop_feature)
    geometry = geometry_distance(e_i, e_j)
    cls = class_distance(e_i, e_j)
    res = abs(resolution_score(e_i) - resolution_score(e_j))
    time = abs(e_i.timestamp - e_j.timestamp)
    unc = 0.5 * (e_i.uncertainty + e_j.uncertainty)
    return float(
        weights.lambda_app * appearance
        + weights.lambda_geo * geometry
        + weights.lambda_cls * cls
        + weights.lambda_res * res
        + weights.lambda_time * time
        + weights.lambda_unc * unc
    )


def reliability_weight(
    token: EvidenceToken,
    *,
    visibility_score: float = 1.0,
    geometry_residual: float = 0.0,
    a: float = 2.0,
    b: float = 1.0,
    c: float = 2.0,
    d: float = 1.0,
) -> float:
    z = a * resolution_score(token) + b * visibility_score - c * token.uncertainty - d * geometry_residual
    return float(1.0 / (1.0 + math.exp(-z)))

