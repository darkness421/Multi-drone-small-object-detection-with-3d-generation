"""Evaluate cross-view association and 3D object hypotheses."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

from evidence import load_tokens_jsonl
from evaluation.metrics import association_f1, center_error_3d, false_merge_rate, false_split_rate


OBJ_PATTERN = re.compile(r"(obj[_-]?\d+)", re.IGNORECASE)


def prediction_pairs(hypotheses: list[dict[str, Any]]) -> set[tuple[str, str]]:
    pairs: set[tuple[str, str]] = set()
    for hypothesis in hypotheses:
        token_ids = sorted(hypothesis.get("token_ids", []))
        for i in range(len(token_ids)):
            for j in range(i + 1, len(token_ids)):
                pairs.add((token_ids[i], token_ids[j]))
    return pairs


def gt_pairs(gt_object_by_obs: dict[str, str]) -> set[tuple[str, str]]:
    by_object: dict[str, list[str]] = {}
    for obs_id, object_id in gt_object_by_obs.items():
        by_object.setdefault(object_id, []).append(obs_id)
    pairs: set[tuple[str, str]] = set()
    for token_ids in by_object.values():
        token_ids = sorted(token_ids)
        for i in range(len(token_ids)):
            for j in range(i + 1, len(token_ids)):
                pairs.add((token_ids[i], token_ids[j]))
    return pairs


def infer_gt_from_tokens(tokens_path: str | Path) -> tuple[dict[str, str], dict[str, list[float]]]:
    mapping: dict[str, str] = {}
    centers: dict[str, list[float]] = {}
    for token in load_tokens_jsonl(tokens_path):
        match = OBJ_PATTERN.search(token.token_id)
        object_id = token.object_id or (match.group(1).replace("-", "_") if match else token.token_id)
        mapping[token.token_id] = object_id
        center = token.metadata.get("center_3d")
        if center is not None:
            centers.setdefault(object_id, center)
    return mapping, centers


def load_gt(path: str | Path) -> tuple[dict[str, str], dict[str, list[float]]]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    mapping: dict[str, str] = {}
    centers: dict[str, list[float]] = {}
    for row in payload:
        token_id = row["token_id"]
        object_id = row["object_id"]
        mapping[token_id] = object_id
        if row.get("center_3d") is not None:
            centers[object_id] = row["center_3d"]
    return mapping, centers


def majority_gt_object(token_ids: list[str], gt_object_by_obs: dict[str, str]) -> str | None:
    counts: dict[str, int] = {}
    for token_id in token_ids:
        object_id = gt_object_by_obs.get(token_id)
        if object_id is not None:
            counts[object_id] = counts.get(object_id, 0) + 1
    if not counts:
        return None
    return max(counts.items(), key=lambda item: item[1])[0]


def mean_3d_error(
    hypotheses: list[dict[str, Any]],
    gt_object_by_obs: dict[str, str],
    gt_center_by_object: dict[str, list[float]],
) -> float:
    errors: list[float] = []
    for hypothesis in hypotheses:
        pred_center = hypothesis.get("center_3d")
        if pred_center is None:
            continue
        gt_object = majority_gt_object(hypothesis.get("token_ids", []), gt_object_by_obs)
        if gt_object is None or gt_object not in gt_center_by_object:
            continue
        errors.append(center_error_3d(pred_center, gt_center_by_object[gt_object]))
    return sum(errors) / len(errors) if errors else 0.0


def evaluate_association(
    hypotheses: list[dict[str, Any]],
    gt_object_by_obs: dict[str, str],
    gt_center_by_object: dict[str, list[float]],
) -> dict[str, float]:
    pred_nodes = [hypothesis.get("token_ids", []) for hypothesis in hypotheses]
    assoc = association_f1(prediction_pairs(hypotheses), gt_pairs(gt_object_by_obs))
    return {
        "association_precision": assoc["precision"],
        "association_recall": assoc["recall"],
        "association_f1": assoc["f1"],
        "false_merge_rate": false_merge_rate(pred_nodes, gt_object_by_obs),
        "false_split_rate": false_split_rate(pred_nodes, gt_object_by_obs),
        "mean_3d_center_error": mean_3d_error(hypotheses, gt_object_by_obs, gt_center_by_object),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate association F1, merge/split, and 3D center error.")
    parser.add_argument("--hypotheses", required=True)
    parser.add_argument("--gt", default=None, help="Optional JSON list with token_id, object_id, center_3d.")
    parser.add_argument("--tokens", default=None, help="Optional EvidenceToken JSONL for inferring dummy GT from token IDs.")
    parser.add_argument("--out", default="outputs/evaluation/association_metrics.json")
    args = parser.parse_args()

    hypotheses = json.loads(Path(args.hypotheses).read_text(encoding="utf-8"))
    if args.gt:
        gt_object_by_obs, gt_center_by_object = load_gt(args.gt)
    elif args.tokens:
        gt_object_by_obs, gt_center_by_object = infer_gt_from_tokens(args.tokens)
    else:
        raise SystemExit("Provide --gt or --tokens.")

    metrics = evaluate_association(hypotheses, gt_object_by_obs, gt_center_by_object)
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    print(json.dumps(metrics, indent=2))


if __name__ == "__main__":
    main()

