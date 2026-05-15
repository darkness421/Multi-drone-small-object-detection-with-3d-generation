"""Final decision fusion for CoM3D-ACE detector, geometry, ambiguity, and LLM evidence."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


@dataclass(slots=True)
class FinalDecision:
    object_id: str
    predicted_class: str
    confidence: float
    decision_source: str
    should_reobserve: bool
    reason_tags: list[str] = field(default_factory=list)
    evidence: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _normalize_distribution(values: dict[str, float]) -> dict[str, float]:
    total = sum(max(0.0, float(value)) for value in values.values())
    if total <= 0:
        return {}
    return {key: max(0.0, float(value)) / total for key, value in values.items()}


def _posterior_from_hypothesis(hypothesis: dict[str, Any]) -> dict[str, float]:
    posterior = hypothesis.get("class_posterior", {})
    if isinstance(posterior, dict):
        return _normalize_distribution({str(key): float(value) for key, value in posterior.items()})
    if isinstance(posterior, list):
        names = hypothesis.get("class_names") or [str(idx) for idx in range(len(posterior))]
        return _normalize_distribution({str(name): float(value) for name, value in zip(names, posterior)})
    class_name = hypothesis.get("class") or hypothesis.get("predicted_class")
    confidence = float(hypothesis.get("confidence", 0.0))
    return {str(class_name): confidence} if class_name else {}


def _top(distribution: dict[str, float]) -> tuple[str, float]:
    if not distribution:
        return "unknown", 0.0
    key = max(distribution, key=distribution.get)
    return key, float(distribution[key])


def _llm_vote(llm_payload: dict[str, Any] | None) -> tuple[str | None, float, list[str]]:
    if not llm_payload:
        return None, 0.0, []
    predicted = llm_payload.get("predicted_class") or llm_payload.get("class")
    confidence = float(llm_payload.get("confidence", 0.0))
    reasons = llm_payload.get("reasons", llm_payload.get("reason_tags", []))
    if isinstance(reasons, str):
        reasons = [reasons]
    return str(predicted) if predicted else None, confidence, [str(reason) for reason in reasons]


def adjudicate_object(
    hypothesis: dict[str, Any],
    ambiguity: dict[str, Any] | None = None,
    llm_payload: dict[str, Any] | None = None,
    *,
    llm_weight: float = 0.25,
    reobserve_threshold: float = 0.62,
) -> FinalDecision:
    """Fuse detector posterior, ambiguity score, geometry residual, and optional LLM output."""

    posterior = _posterior_from_hypothesis(hypothesis)
    detector_class, detector_conf = _top(posterior)
    ambiguity = ambiguity or {}
    ambiguity_score = float(ambiguity.get("ambiguity_score", hypothesis.get("ambiguity_score", 0.0)))
    geometry_residual = float((ambiguity.get("components") or {}).get("geometry_residual", hypothesis.get("geometry_residual", 0.0)))
    llm_class, llm_conf, llm_reasons = _llm_vote(llm_payload)

    fused = dict(posterior)
    decision_source = "detector_geometry"
    if llm_class and llm_conf > 0:
        fused[llm_class] = fused.get(llm_class, 0.0) + llm_weight * llm_conf
        fused = _normalize_distribution(fused)
        decision_source = "llm_assisted" if llm_class != detector_class else "llm_confirmed"

    predicted_class, confidence = _top(fused)
    reasons = list(ambiguity.get("reason_tags", [])) + llm_reasons
    if llm_class and llm_class != detector_class:
        reasons.append("llm_detector_disagreement")
    if geometry_residual > 0.5:
        reasons.append("geometry_residual")
    if ambiguity_score >= reobserve_threshold:
        reasons.append("high_ambiguity")

    should_reobserve = ambiguity_score >= reobserve_threshold or (llm_class is not None and llm_class != detector_class and llm_conf >= 0.55)
    return FinalDecision(
        object_id=str(hypothesis.get("object_id", "")),
        predicted_class=predicted_class,
        confidence=float(confidence),
        decision_source=decision_source,
        should_reobserve=should_reobserve,
        reason_tags=sorted(set(reasons)),
        evidence={
            "detector_top_class": detector_class,
            "detector_confidence": detector_conf,
            "ambiguity_score": ambiguity_score,
            "geometry_residual": geometry_residual,
            "llm_class": llm_class,
            "llm_confidence": llm_conf,
        },
    )


def _read_json(path: str | Path | None) -> Any:
    if not path:
        return None
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _by_object(rows: list[dict[str, Any]] | None) -> dict[str, dict[str, Any]]:
    return {str(row.get("object_id")): row for row in rows or []}


def adjudicate_files(hypotheses_path: str | Path, out_path: str | Path, ambiguity_path: str | Path | None = None, llm_path: str | Path | None = None) -> list[dict[str, Any]]:
    hypotheses = _read_json(hypotheses_path) or []
    ambiguity_by_id = _by_object(_read_json(ambiguity_path))
    llm_by_id = _by_object(_read_json(llm_path))
    decisions = [
        adjudicate_object(
            hypothesis,
            ambiguity=ambiguity_by_id.get(str(hypothesis.get("object_id"))),
            llm_payload=llm_by_id.get(str(hypothesis.get("object_id"))),
        ).to_dict()
        for hypothesis in hypotheses
    ]
    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(decisions, indent=2, ensure_ascii=False), encoding="utf-8")
    return decisions


def main() -> None:
    parser = argparse.ArgumentParser(description="Fuse detector/geometry/ambiguity/LLM evidence into final object decisions.")
    parser.add_argument("--hypotheses", required=True)
    parser.add_argument("--ambiguity", default=None)
    parser.add_argument("--llm", default=None)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    decisions = adjudicate_files(args.hypotheses, args.out, args.ambiguity, args.llm)
    print(f"Wrote {args.out} ({len(decisions)} decisions)")


if __name__ == "__main__":
    main()
