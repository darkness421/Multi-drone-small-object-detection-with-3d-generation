"""Reusable metrics for CoM3D-ACE experiments."""

from __future__ import annotations

import math
from typing import Sequence

import numpy as np

from evidence.uncertainty import brier_score, expected_calibration_error


def bbox_iou_xywh(a: Sequence[float], b: Sequence[float]) -> float:
    ax1, ay1, aw, ah = [float(v) for v in a]
    bx1, by1, bw, bh = [float(v) for v in b]
    ax2, ay2 = ax1 + aw, ay1 + ah
    bx2, by2 = bx1 + bw, by1 + bh
    inter_x1, inter_y1 = max(ax1, bx1), max(ay1, by1)
    inter_x2, inter_y2 = min(ax2, bx2), min(ay2, by2)
    inter = max(0.0, inter_x2 - inter_x1) * max(0.0, inter_y2 - inter_y1)
    union = aw * ah + bw * bh - inter
    return float(inter / union) if union > 0 else 0.0


def precision_recall_f1(tp: int, fp: int, fn: int) -> dict[str, float]:
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return {"precision": precision, "recall": recall, "f1": f1}


def average_precision_at_iou(
    predictions: Sequence[dict[str, object]],
    ground_truth: Sequence[dict[str, object]],
    *,
    iou_threshold: float = 0.5,
) -> float:
    """Small dependency-free AP approximation for smoke tests and CSV drafts."""

    preds = sorted(predictions, key=lambda row: float(row.get("score", 0.0)), reverse=True)
    matched: set[int] = set()
    tp: list[float] = []
    fp: list[float] = []
    for pred in preds:
        best_iou = 0.0
        best_idx = -1
        for idx, gt in enumerate(ground_truth):
            if idx in matched or pred.get("category_id") != gt.get("category_id"):
                continue
            iou = bbox_iou_xywh(pred["bbox"], gt["bbox"])
            if iou > best_iou:
                best_iou = iou
                best_idx = idx
        if best_iou >= iou_threshold and best_idx >= 0:
            matched.add(best_idx)
            tp.append(1.0)
            fp.append(0.0)
        else:
            tp.append(0.0)
            fp.append(1.0)
    if not ground_truth or not preds:
        return 0.0
    cum_tp = np.cumsum(tp)
    cum_fp = np.cumsum(fp)
    recalls = cum_tp / max(len(ground_truth), 1)
    precisions = cum_tp / np.maximum(cum_tp + cum_fp, 1e-12)
    ap = 0.0
    for threshold in np.linspace(0.0, 1.0, 11):
        valid = precisions[recalls >= threshold]
        ap += float(valid.max()) if valid.size else 0.0
    return ap / 11.0


def detection_metrics(
    predictions: Sequence[dict[str, object]],
    ground_truth: Sequence[dict[str, object]],
) -> dict[str, float]:
    ap50 = average_precision_at_iou(predictions, ground_truth, iou_threshold=0.5)
    ap75 = average_precision_at_iou(predictions, ground_truth, iou_threshold=0.75)
    thresholds = np.arange(0.5, 1.0, 0.05)
    ap5095 = float(np.mean([average_precision_at_iou(predictions, ground_truth, iou_threshold=float(t)) for t in thresholds]))
    return {"AP": ap5095, "AP50": ap50, "AP75": ap75, "APsmall": ap50}


def center_error_3d(pred: Sequence[float], target: Sequence[float]) -> float:
    return float(math.sqrt(sum((float(a) - float(b)) ** 2 for a, b in zip(pred, target))))


def association_f1(pred_pairs: set[tuple[str, str]], gt_pairs: set[tuple[str, str]]) -> dict[str, float]:
    tp = len(pred_pairs & gt_pairs)
    fp = len(pred_pairs - gt_pairs)
    fn = len(gt_pairs - pred_pairs)
    return precision_recall_f1(tp, fp, fn)


def false_merge_rate(object_nodes: Sequence[Sequence[str]], gt_object_by_obs: dict[str, str]) -> float:
    if not object_nodes:
        return 0.0
    false_merges = 0
    for node in object_nodes:
        gt_ids = {gt_object_by_obs.get(obs_id) for obs_id in node if obs_id in gt_object_by_obs}
        if len(gt_ids) > 1:
            false_merges += 1
    return false_merges / len(object_nodes)


def false_split_rate(object_nodes: Sequence[Sequence[str]], gt_object_by_obs: dict[str, str]) -> float:
    gt_to_pred: dict[str, set[int]] = {}
    for node_idx, node in enumerate(object_nodes):
        for obs_id in node:
            gt_id = gt_object_by_obs.get(obs_id)
            if gt_id is not None:
                gt_to_pred.setdefault(gt_id, set()).add(node_idx)
    if not gt_to_pred:
        return 0.0
    return sum(1 for pred_ids in gt_to_pred.values() if len(pred_ids) > 1) / len(gt_to_pred)


def ambiguity_metrics(scores: Sequence[float], labels: Sequence[int]) -> dict[str, float]:
    metrics: dict[str, float] = {}
    try:
        from sklearn.metrics import average_precision_score, roc_auc_score

        metrics["AUROC"] = float(roc_auc_score(labels, scores)) if len(set(labels)) > 1 else 0.0
        metrics["AUPRC"] = float(average_precision_score(labels, scores)) if labels else 0.0
    except ImportError:
        metrics["AUROC"] = 0.0
        metrics["AUPRC"] = 0.0
    preds = [score >= 0.5 for score in scores]
    tp = sum(1 for p, y in zip(preds, labels) if p and y)
    fp = sum(1 for p, y in zip(preds, labels) if p and not y)
    fn = sum(1 for p, y in zip(preds, labels) if not p and y)
    metrics.update(precision_recall_f1(tp, fp, fn))
    return metrics


def calibration_metrics(confidences: Sequence[float], correct: Sequence[bool], probs: Sequence[Sequence[float]] | None = None, labels: Sequence[int] | None = None) -> dict[str, float]:
    payload = {"ECE": expected_calibration_error(confidences, correct)}
    if probs is not None and labels is not None:
        payload["Brier"] = float(np.mean([brier_score(p, y) for p, y in zip(probs, labels)])) if labels else 0.0
    return payload


def policy_metrics(
    *,
    final_correct: Sequence[bool],
    ambiguity_resolved: Sequence[bool],
    reobserve_count: Sequence[int],
    flight_cost: Sequence[float],
    vlm_call_count: Sequence[int],
    latency: Sequence[float],
) -> dict[str, float]:
    n = len(final_correct)
    return {
        "final_accuracy": sum(final_correct) / n if n else 0.0,
        "ambiguity_resolution_rate": sum(ambiguity_resolved) / len(ambiguity_resolved) if ambiguity_resolved else 0.0,
        "re_observation_count": float(np.mean(reobserve_count)) if reobserve_count else 0.0,
        "flight_cost": float(np.mean(flight_cost)) if flight_cost else 0.0,
        "VLM_call_count": float(np.mean(vlm_call_count)) if vlm_call_count else 0.0,
        "latency": float(np.mean(latency)) if latency else 0.0,
    }
