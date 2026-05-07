"""Ambiguity scoring and reason diagnosis."""

from __future__ import annotations

from dataclasses import asdict, dataclass

from evidence.uncertainty import class_entropy
from graph.evidence_graph import ObjectHypothesisNode


@dataclass(slots=True)
class AmbiguityWeights:
    w_H: float = 1.0
    w_D: float = 1.0
    w_M: float = 1.0
    w_O: float = 0.8
    w_R: float = 0.8
    w_G: float = 1.0


@dataclass(slots=True)
class AmbiguityDiagnosis:
    object_id: str
    score: float
    level: str
    reasons: list[str]
    missing_evidence_type: str | None
    recommended_action_type: str

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def level_from_score(score: float) -> str:
    if score < 0.35:
        return "low"
    if score < 0.7:
        return "medium"
    return "high"


def diagnose_ambiguity(
    obj: ObjectHypothesisNode,
    *,
    cross_view_disagreement: float = 0.0,
    missing_evidence: float | None = None,
    occlusion_score: float = 0.0,
    low_resolution_score: float = 0.0,
    geometry_inconsistency: float | None = None,
    weights: AmbiguityWeights | None = None,
) -> AmbiguityDiagnosis:
    weights = weights or AmbiguityWeights()
    missing = 1.0 if missing_evidence is None and obj.support_count < 2 else float(missing_evidence or 0.0)
    geometry = float(geometry_inconsistency if geometry_inconsistency is not None else 1.0 - obj.consistency_score)
    entropy = class_entropy(obj.class_posterior)
    score = (
        weights.w_H * entropy
        + weights.w_D * cross_view_disagreement
        + weights.w_M * missing
        + weights.w_O * occlusion_score
        + weights.w_R * low_resolution_score
        + weights.w_G * geometry
    ) / (weights.w_H + weights.w_D + weights.w_M + weights.w_O + weights.w_R + weights.w_G)

    reasons: list[str] = []
    if entropy > 0.6:
        reasons.append("class_entropy")
    if cross_view_disagreement > 0.4:
        reasons.append("cross_view_disagreement")
    if missing > 0.5:
        reasons.append("missing_evidence")
    if occlusion_score > 0.5:
        reasons.append("occlusion")
    if low_resolution_score > 0.5:
        reasons.append("low_resolution")
    if geometry > 0.5:
        reasons.append("geometry_inconsistency")

    missing_type = None
    if "missing_evidence" in reasons:
        missing_type = "additional_view"
    elif "low_resolution" in reasons:
        missing_type = "closer_view"
    elif "occlusion" in reasons:
        missing_type = "side_view"

    level = level_from_score(score)
    action = "finalize" if level == "low" else "VLM verify" if level == "medium" else "active re-observe"
    return AmbiguityDiagnosis(obj.node_id, float(score), level, reasons, missing_type, action)

