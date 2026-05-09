"""Score ambiguous object hypotheses and evaluate hard-case detection."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from evidence.uncertainty import class_entropy
from evaluation.metrics import ambiguity_metrics


def cross_view_disagreement(hypothesis: dict[str, Any]) -> float:
    token_count = max(int(hypothesis.get("support_count", 1)), 1)
    uav_count = len(hypothesis.get("metadata", {}).get("uav_ids", []))
    return 1.0 - min(1.0, uav_count / max(token_count, 1))


def missing_evidence_score(hypothesis: dict[str, Any], min_support: int = 2) -> float:
    support = int(hypothesis.get("support_count", 0))
    return max(0.0, min(1.0, (min_support - support) / max(min_support, 1)))


def low_resolution_score(hypothesis: dict[str, Any]) -> float:
    return float(hypothesis.get("metadata", {}).get("low_resolution_score", 0.0))


def geometry_residual_score(hypothesis: dict[str, Any]) -> float:
    return float(hypothesis.get("metadata", {}).get("geometry_residual", 1.0 if hypothesis.get("center_3d") is None else 0.0))


def score_hypothesis(hypothesis: dict[str, Any]) -> dict[str, Any]:
    entropy = class_entropy(hypothesis.get("class_posterior", []))
    disagreement = cross_view_disagreement(hypothesis)
    missing = missing_evidence_score(hypothesis)
    low_res = low_resolution_score(hypothesis)
    geom = geometry_residual_score(hypothesis)
    score = 0.30 * entropy + 0.20 * disagreement + 0.20 * missing + 0.15 * low_res + 0.15 * geom
    reasons = []
    if entropy > 0.6:
        reasons.append("class_entropy")
    if disagreement > 0.4:
        reasons.append("cross_view_disagreement")
    if missing > 0.0:
        reasons.append("missing_evidence")
    if low_res > 0.5:
        reasons.append("low_resolution")
    if geom > 0.5:
        reasons.append("geometry_residual")
    return {
        "object_id": hypothesis.get("object_id"),
        "ambiguity_score": float(score),
        "reason_tags": reasons,
        "components": {
            "class_entropy": entropy,
            "cross_view_disagreement": disagreement,
            "missing_evidence": missing,
            "low_resolution": low_res,
            "geometry_residual": geom,
        },
    }


def score_file(hypotheses_path: str | Path, out_path: str | Path) -> list[dict[str, Any]]:
    hypotheses = json.loads(Path(hypotheses_path).read_text(encoding="utf-8"))
    scored = [score_hypothesis(hypothesis) for hypothesis in hypotheses]
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    Path(out_path).write_text(json.dumps(scored, indent=2, ensure_ascii=False), encoding="utf-8")
    return scored


def evaluate_hard_cases(scores_path: str | Path, labels_path: str | Path) -> dict[str, float]:
    scores = json.loads(Path(scores_path).read_text(encoding="utf-8"))
    labels_payload = json.loads(Path(labels_path).read_text(encoding="utf-8"))
    labels_by_id = {row["object_id"]: int(row["hard_case"]) for row in labels_payload}
    y_score = [row["ambiguity_score"] for row in scores if row["object_id"] in labels_by_id]
    y_true = [labels_by_id[row["object_id"]] for row in scores if row["object_id"] in labels_by_id]
    return ambiguity_metrics(y_score, y_true)


def main() -> None:
    parser = argparse.ArgumentParser(description="Score object ambiguity and optionally evaluate hard-case AUROC/AUPRC.")
    parser.add_argument("--hypotheses", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--labels", default=None)
    args = parser.parse_args()

    score_file(args.hypotheses, args.out)
    print(f"Wrote ambiguity scores to {args.out}")
    if args.labels:
        print(json.dumps(evaluate_hard_cases(args.out, args.labels), indent=2))


if __name__ == "__main__":
    main()

