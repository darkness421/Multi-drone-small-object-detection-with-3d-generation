"""Object-level detector ROC-AUC utilities.

This module is intentionally separate from ambiguity ROC-AUC. Detector ROC-AUC
uses detection confidence scores and binary correctness labels from IoU matching.
Ambiguity ROC-AUC will later live with the ambiguity scorer and hard-case labels.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import numpy as np

from runtime.config import resolve_path


def xyxy_iou(a: list[float], b: list[float]) -> float:
    ax1, ay1, ax2, ay2 = a
    bx1, by1, bx2, by2 = b
    inter_x1 = max(ax1, bx1)
    inter_y1 = max(ay1, by1)
    inter_x2 = min(ax2, bx2)
    inter_y2 = min(ay2, by2)
    inter_w = max(0.0, inter_x2 - inter_x1)
    inter_h = max(0.0, inter_y2 - inter_y1)
    inter = inter_w * inter_h
    area_a = max(0.0, ax2 - ax1) * max(0.0, ay2 - ay1)
    area_b = max(0.0, bx2 - bx1) * max(0.0, by2 - by1)
    union = area_a + area_b - inter
    return inter / union if union > 0 else 0.0


def load_jsonl(path: str | Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with resolve_path(path).open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def label_detections(
    detections: list[dict[str, Any]],
    ground_truth: list[dict[str, Any]],
    *,
    iou_threshold: float = 0.5,
    class_aware: bool = True,
) -> tuple[list[int], list[float]]:
    """Label detections as matched positives or unmatched false positives.

    Expected row fields: image_id, class_id, bbox_xyxy, score for detections;
    image_id, class_id, bbox_xyxy for ground truth.
    """

    gt_by_image: dict[str, list[dict[str, Any]]] = {}
    for item in ground_truth:
        gt_by_image.setdefault(str(item["image_id"]), []).append(item)

    used: set[tuple[str, int]] = set()
    labels: list[int] = []
    scores: list[float] = []
    for det in sorted(detections, key=lambda row: float(row.get("score", 0.0)), reverse=True):
        image_id = str(det["image_id"])
        best_iou = 0.0
        best_idx: int | None = None
        for idx, gt in enumerate(gt_by_image.get(image_id, [])):
            if (image_id, idx) in used:
                continue
            if class_aware and int(det["class_id"]) != int(gt["class_id"]):
                continue
            iou = xyxy_iou([float(v) for v in det["bbox_xyxy"]], [float(v) for v in gt["bbox_xyxy"]])
            if iou > best_iou:
                best_iou = iou
                best_idx = idx
        is_positive = best_idx is not None and best_iou >= iou_threshold
        if is_positive and best_idx is not None:
            used.add((image_id, best_idx))
        labels.append(1 if is_positive else 0)
        scores.append(float(det.get("score", 0.0)))
    return labels, scores


def roc_auc(labels: list[int], scores: list[float]) -> float | None:
    if len(set(labels)) < 2:
        return None
    try:
        from sklearn.metrics import roc_auc_score
    except ImportError as exc:
        raise RuntimeError("scikit-learn is required for detector ROC-AUC.") from exc
    return float(roc_auc_score(np.asarray(labels), np.asarray(scores)))


def main() -> None:
    parser = argparse.ArgumentParser(description="Compute object-level detector ROC-AUC from JSONL detections and GT.")
    parser.add_argument("--detections-jsonl", required=True)
    parser.add_argument("--ground-truth-jsonl", required=True)
    parser.add_argument("--iou-threshold", type=float, default=0.5)
    parser.add_argument("--class-agnostic", action="store_true")
    parser.add_argument("--out", default=None)
    args = parser.parse_args()

    labels, scores = label_detections(
        load_jsonl(args.detections_jsonl),
        load_jsonl(args.ground_truth_jsonl),
        iou_threshold=args.iou_threshold,
        class_aware=not args.class_agnostic,
    )
    payload = {
        "metric": "object_level_detector_roc_auc",
        "definition": "positive if IoU >= threshold and class matches; unmatched detections are false positives",
        "iou_threshold": args.iou_threshold,
        "num_detections": len(labels),
        "positive_count": int(sum(labels)),
        "negative_count": int(len(labels) - sum(labels)),
        "roc_auc": roc_auc(labels, scores),
    }
    text = json.dumps(payload, indent=2)
    if args.out:
        out_path = resolve_path(args.out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(text, encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
