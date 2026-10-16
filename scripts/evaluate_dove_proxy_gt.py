#!/usr/bin/env python3
"""Evaluate a frozen detector on validated Isaac proxy RGB and 2D GT captures.

This is a synthetic proxy smoke evaluation. It must not be presented as a
real-city, independent, or detector-generalization benchmark.
"""

from __future__ import annotations

import argparse
import ast
import csv
import hashlib
import json
import math
import random
import sys
import time
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable, Mapping

from PIL import Image, ImageDraw


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from detectors.wrappers import UltralyticsWrapper  # noqa: E402
from dove_wm.proxy_gt import load_deduplicated_gt  # noqa: E402


RANDOM_SEED = 20261015
GT_CANONICAL = {
    "sedan": "car",
    "pickup": "car",
    "police_car": "car",
    "car": "car",
    "van": "van",
    "ambulance": "van",
    "truck": "truck",
    "bus": "bus",
    "pedestrian": "pedestrian",
    "people": "pedestrian",
    "person": "pedestrian",
    "worker": "pedestrian",
    "small_boat": "boat",
    "boat": "boat",
    "debris": "debris",
}


def _normalise(value: Any) -> str:
    return str(value or "").strip().lower().replace(" ", "_").replace("-", "_")


def _canonical(value: Any) -> str:
    label = _normalise(value)
    return GT_CANONICAL.get(label, label)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _write_csv(path: Path, rows: Iterable[Mapping[str, Any]]) -> None:
    materialised = list(rows)
    fields = list(dict.fromkeys(key for row in materialised for key in row)) or ["status"]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(materialised)


def _label_from_info(info: Mapping[str, Any], semantic_id: Any) -> str:
    mapping = info.get("idToLabels") or info.get("id_to_labels") or {}
    raw = mapping.get(str(semantic_id), mapping.get(semantic_id, "")) if isinstance(mapping, dict) else ""
    if isinstance(raw, dict):
        return str(raw.get("class") or raw.get("label") or raw.get("name") or "")
    if isinstance(raw, str):
        try:
            parsed = ast.literal_eval(raw)
        except (ValueError, SyntaxError):
            parsed = None
        if isinstance(parsed, dict):
            return str(parsed.get("class") or parsed.get("label") or parsed.get("name") or "")
        return raw
    return str(raw or "")


def _coord(row: Mapping[str, Any], *names: str) -> float:
    for name in names:
        if name in row:
            return float(row[name])
    raise KeyError(f"missing coordinate {names} in {sorted(row)}")


def _load_gt(path: Path) -> list[dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(payload, dict):
        data = payload.get("data", [])
        info = payload.get("info", {})
    else:
        data = payload
        info = {}
    rows = []
    for item in data:
        if not isinstance(item, dict):
            continue
        semantic_id = item.get("semanticId", item.get("semantic_id", item.get("id")))
        label = _label_from_info(info, semantic_id)
        if not label:
            label = str(item.get("class") or item.get("label") or "unknown")
        x1 = _coord(item, "x_min", "xMin", "xmin")
        y1 = _coord(item, "y_min", "yMin", "ymin")
        x2 = _coord(item, "x_max", "xMax", "xmax")
        y2 = _coord(item, "y_max", "yMax", "ymax")
        if x2 <= x1 or y2 <= y1:
            continue
        rows.append(
            {
                "semantic_id": semantic_id,
                "label": _normalise(label),
                "canonical": _canonical(label),
                "xyxy": [x1, y1, x2, y2],
            }
        )
    return rows


def _iou(a: list[float], b: list[float]) -> float:
    ix1 = max(a[0], b[0])
    iy1 = max(a[1], b[1])
    ix2 = min(a[2], b[2])
    iy2 = min(a[3], b[3])
    inter = max(0.0, ix2 - ix1) * max(0.0, iy2 - iy1)
    area_a = max(0.0, a[2] - a[0]) * max(0.0, a[3] - a[1])
    area_b = max(0.0, b[2] - b[0]) * max(0.0, b[3] - b[1])
    return inter / max(area_a + area_b - inter, 1.0e-12)


def _match(
    gt: list[dict[str, Any]], predictions: list[dict[str, Any]], iou_threshold: float
) -> dict[str, Any]:
    matched_gt: set[int] = set()
    tp = 0
    match_rows = []
    for pred_index, pred in sorted(
        enumerate(predictions), key=lambda pair: (-float(pair[1]["confidence"]), pair[0])
    ):
        candidates = [
            (index, _iou(pred["xyxy"], target["xyxy"]))
            for index, target in enumerate(gt)
            if index not in matched_gt and target["canonical"] == pred["canonical"]
        ]
        best_index, best_iou = max(candidates, key=lambda pair: pair[1], default=(-1, 0.0))
        is_tp = best_index >= 0 and best_iou >= iou_threshold
        if is_tp:
            matched_gt.add(best_index)
            tp += 1
        match_rows.append(
            {
                "prediction_index": pred_index,
                "gt_index": best_index if is_tp else None,
                "iou": best_iou,
                "true_positive": bool(is_tp),
            }
        )
    fp = len(predictions) - tp
    fn = len(gt) - tp
    precision = tp / max(tp + fp, 1)
    recall = tp / max(tp + fn, 1)
    f1 = 2.0 * precision * recall / max(precision + recall, 1.0e-12)
    best_gt_ious = [
        max(
            (
                _iou(target["xyxy"], pred["xyxy"])
                for pred in predictions
                if pred["canonical"] == target["canonical"]
            ),
            default=0.0,
        )
        for target in gt
    ]
    return {
        "tp": tp,
        "fp": fp,
        "fn": fn,
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "mean_gt_best_iou": sum(best_gt_ious) / max(len(best_gt_ious), 1),
        "matches": match_rows,
    }


def _draw_overlay(
    image_path: Path,
    gt: list[dict[str, Any]],
    predictions: list[dict[str, Any]],
    out_path: Path,
) -> None:
    with Image.open(image_path).convert("RGB") as image:
        draw = ImageDraw.Draw(image)
        for row in gt:
            draw.rectangle(row["xyxy"], outline=(40, 220, 70), width=3)
            draw.text((row["xyxy"][0] + 2, row["xyxy"][1] + 2), f"GT {row['canonical']}", fill=(40, 220, 70))
        for row in predictions:
            draw.rectangle(row["xyxy"], outline=(235, 55, 55), width=2)
            draw.text(
                (row["xyxy"][0] + 2, max(0, row["xyxy"][1] - 12)),
                f"P {row['canonical']} {row['confidence']:.2f}",
                fill=(235, 55, 55),
            )
        out_path.parent.mkdir(parents=True, exist_ok=True)
        image.save(out_path)


def _range_to_origin(camera_record: Mapping[str, Any]) -> float:
    x, y, z = [float(value) for value in camera_record["capture_position_xyz_m"]]
    return math.sqrt(x * x + y * y + z * z)


def _box_inside_image(box: list[float], width: int, height: int) -> bool:
    x1, y1, x2, y2 = box
    return (
        0.0 <= x1 < x2 <= float(width)
        and 0.0 <= y1 < y2 <= float(height)
    )


def _same_outcome(a: Mapping[str, Any], b: Mapping[str, Any]) -> bool:
    return math.isclose(
        float(a["recall_at_iou50"]),
        float(b["recall_at_iou50"]),
        rel_tol=0.0,
        abs_tol=1.0e-12,
    ) and math.isclose(
        float(a["f1_at_iou50"]),
        float(b["f1_at_iou50"]),
        rel_tol=0.0,
        abs_tol=1.0e-12,
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--capture-dir", required=True)
    parser.add_argument("--checkpoint", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--device", default="0")
    parser.add_argument("--imgsz", type=int, default=1280)
    parser.add_argument("--confidence", type=float, default=0.01)
    parser.add_argument("--iou-threshold", type=float, default=0.5)
    parser.add_argument("--seed", type=int, default=RANDOM_SEED)
    args = parser.parse_args()

    capture_dir = Path(args.capture_dir).resolve()
    output_dir = Path(args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    checkpoint = Path(args.checkpoint).resolve()
    summary = json.loads((capture_dir / "proxy_capture_summary.json").read_text(encoding="utf-8"))
    if summary.get("status") != "proxy_direct_capture_complete":
        raise RuntimeError(f"capture is not validated: {summary.get('status')}")

    wrapper = UltralyticsWrapper(
        str(checkpoint),
        predict_kwargs={"conf": args.confidence, "imgsz": args.imgsz, "device": args.device},
    )
    model_names = wrapper.model.names
    detector_classes = {_canonical(name) for name in model_names.values()}

    camera_meta = {row["uav_id"]: row for row in summary["capture_cameras"]}
    capture_records = summary["direct_capture"]["records"]
    gt_by_record: dict[tuple[str, int], list[dict[str, Any]]] = {}
    benchmark_classes: set[str] = set()
    for record in capture_records:
        key = (str(record["uav_id"]), int(record["frame_index"]))
        gt_rows = load_deduplicated_gt(capture_dir / record["bbox_path"])
        gt_by_record[key] = gt_rows
        benchmark_classes.update(row["canonical"] for row in gt_rows)
    evaluation_classes = sorted(benchmark_classes & detector_classes)
    if not evaluation_classes:
        raise RuntimeError(
            "capture and detector have no shared target classes: "
            f"capture={sorted(benchmark_classes)}, detector={sorted(detector_classes)}"
        )

    rows = []
    prediction_rows = []
    coordinate_rows = []
    started = time.perf_counter()
    for record in capture_records:
        uav_id = record["uav_id"]
        rgb_path = capture_dir / record["rgb_path"]
        bbox_path = capture_dir / record["bbox_path"]
        gt_all = gt_by_record[(str(uav_id), int(record["frame_index"]))]
        gt = [row for row in gt_all if row["canonical"] in evaluation_classes]
        with Image.open(rgb_path) as image:
            image_width, image_height = image.size
        expected_width, expected_height = summary["render_resolution"]
        if (image_width, image_height) != (expected_width, expected_height):
            raise RuntimeError(
                f"render resolution mismatch for {rgb_path}: "
                f"image={(image_width, image_height)}, manifest={(expected_width, expected_height)}"
            )
        invalid_gt = [
            row for row in gt if not _box_inside_image(row["xyxy"], image_width, image_height)
        ]
        if invalid_gt:
            raise RuntimeError(f"{uav_id} has {len(invalid_gt)} GT boxes outside the saved RGB frame")

        infer_started = time.perf_counter()
        tokens = wrapper.predict(rgb_path, {"image_id": rgb_path.stem, "uav_id": uav_id})
        inference_seconds = time.perf_counter() - infer_started
        predictions_all = []
        for token in tokens:
            x, y, width, height = [float(value) for value in token.bbox_2d]
            label = _normalise(token.metadata.get("class_name"))
            predictions_all.append(
                {
                    "label": label,
                    "canonical": _canonical(label),
                    "confidence": float(token.confidence),
                    "xyxy": [x, y, x + width, y + height],
                }
            )
        predictions = [row for row in predictions_all if row["canonical"] in evaluation_classes]
        invalid_predictions = [
            row
            for row in predictions
            if not _box_inside_image(row["xyxy"], image_width, image_height)
        ]
        if invalid_predictions:
            raise RuntimeError(
                f"{uav_id} has {len(invalid_predictions)} predictions outside the saved RGB frame"
            )
        metrics = _match(gt, predictions, args.iou_threshold)
        max_confidence_all = max((row["confidence"] for row in predictions_all), default=0.0)
        max_confidence = max((row["confidence"] for row in predictions), default=0.0)
        row = {
            "uav_id": uav_id,
            "frame_index": record["frame_index"],
            "rgb_path": str(rgb_path),
            "bbox_path": str(bbox_path),
            "range_to_origin_m": _range_to_origin(camera_meta[uav_id]),
            "gt_count_all": len(gt_all),
            "gt_count_evaluable": len(gt),
            "unsupported_gt_count": len(gt_all) - len(gt),
            "evaluation_classes": ";".join(evaluation_classes),
            "gt_present_classes": ";".join(sorted({item["canonical"] for item in gt})),
            "prediction_count_all": len(predictions_all),
            "prediction_count_evaluable": len(predictions),
            "max_detector_confidence": max_confidence,
            "max_detector_confidence_all_classes": max_confidence_all,
            "image_width": image_width,
            "image_height": image_height,
            "gt_boxes_inside_image": True,
            "prediction_boxes_inside_image": True,
            "tp": metrics["tp"],
            "fp": metrics["fp"],
            "fn": metrics["fn"],
            "precision_at_iou50": metrics["precision"],
            "recall_at_iou50": metrics["recall"],
            "f1_at_iou50": metrics["f1"],
            "mean_gt_best_iou": metrics["mean_gt_best_iou"],
            "inference_seconds": inference_seconds,
        }
        rows.append(row)
        for index, prediction in enumerate(predictions_all):
            prediction_rows.append(
                {
                    "uav_id": uav_id,
                    "frame_index": record["frame_index"],
                    "prediction_index": index,
                    "in_benchmark_class_set": prediction["canonical"] in evaluation_classes,
                    **prediction,
                }
            )
        for source, boxes in (("gt", gt), ("prediction", predictions)):
            for index, item in enumerate(boxes):
                x1, y1, x2, y2 = item["xyxy"]
                coordinate_rows.append(
                    {
                        "uav_id": uav_id,
                        "frame_index": record["frame_index"],
                        "source": source,
                        "index": index,
                        "canonical": item["canonical"],
                        "x1": x1,
                        "y1": y1,
                        "x2": x2,
                        "y2": y2,
                        "image_width": image_width,
                        "image_height": image_height,
                        "inside_saved_image": _box_inside_image(
                            item["xyxy"], image_width, image_height
                        ),
                    }
                )
        _draw_overlay(
            rgb_path,
            gt,
            predictions,
            output_dir / "overlays" / f"frame_{int(record['frame_index']):04d}_{uav_id}.png",
        )

    grouped_rows: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped_rows[int(row["frame_index"])].append(row)
    policy_rows = []
    oracle_ties_by_frame = []
    for frame_index, frame_rows in sorted(grouped_rows.items()):
        ordered = sorted(frame_rows, key=lambda row: row["uav_id"])
        deterministic_oracle = max(
            ordered,
            key=lambda row: (
                row["recall_at_iou50"],
                row["f1_at_iou50"],
                -row["range_to_origin_m"],
                row["uav_id"],
            ),
        )
        oracle_ties = [row for row in ordered if _same_outcome(row, deterministic_oracle)]
        oracle_tied_uav_ids = sorted(row["uav_id"] for row in oracle_ties)
        oracle_ties_by_frame.append(
            {"frame_index": frame_index, "uav_ids": oracle_tied_uav_ids}
        )
        oracle = min(
            oracle_ties, key=lambda row: (row["range_to_origin_m"], row["uav_id"])
        )
        geometry = min(
            ordered, key=lambda row: (row["range_to_origin_m"], row["uav_id"])
        )
        detector_proxy = max(
            ordered, key=lambda row: (row["max_detector_confidence"], row["uav_id"])
        )
        rng = random.Random(f"{args.seed}:{frame_index}")
        policies = {
            "FIXED_FIRST": ordered[0],
            "DETERMINISTIC_RANDOM": rng.choice(ordered),
            "GEOMETRY_MIN_RANGE": geometry,
            "DETECTOR_CONFIDENCE_PROXY": detector_proxy,
            "GT_RECALL_ORACLE": oracle,
        }
        for method, selected in policies.items():
            policy_rows.append(
                {
                    "frame_index": frame_index,
                    "method": method,
                    "selected_uav_id": selected["uav_id"],
                    "selected_recall_at_iou50": selected["recall_at_iou50"],
                    "selected_f1_at_iou50": selected["f1_at_iou50"],
                    "oracle_uav_id": oracle["uav_id"],
                    "oracle_tied_uav_ids": ";".join(oracle_tied_uav_ids),
                    "oracle_tie_count": len(oracle_ties),
                    "oracle_match_tie_aware": selected["uav_id"] in oracle_tied_uav_ids,
                    "oracle_recall_at_iou50": oracle["recall_at_iou50"],
                    "recall_regret": (
                        oracle["recall_at_iou50"] - selected["recall_at_iou50"]
                    ),
                    "ground_truth_outcome": True,
                }
            )

    uniform_random_expectation = {
        "expected_recall_at_iou50": sum(row["recall_at_iou50"] for row in rows)
        / len(rows),
        "expected_f1_at_iou50": sum(row["f1_at_iou50"] for row in rows) / len(rows),
        "expected_max_detector_confidence": sum(row["max_detector_confidence"] for row in rows)
        / len(rows),
    }
    _write_csv(output_dir / "detector_gt_per_view.csv", rows)
    _write_csv(output_dir / "detector_predictions.csv", prediction_rows)
    _write_csv(output_dir / "bbox_coordinate_audit.csv", coordinate_rows)
    _write_csv(output_dir / "view_selection.csv", policy_rows)

    result = {
        "status": "COMPLETE_SYNTHETIC_PROXY_GT_SMOKE",
        "scope": "Isaac proxy geometry with VisDrone-derived cutout overlays; not independent or real-city",
        "capture_dir": str(capture_dir),
        "checkpoint": str(checkpoint),
        "checkpoint_sha256": _sha256(checkpoint),
        "detector_model_names": model_names,
        "confidence_threshold": args.confidence,
        "iou_threshold": args.iou_threshold,
        "imgsz": args.imgsz,
        "seed": args.seed,
        "camera_count": len(camera_meta),
        "action_observation_count": len(rows),
        "scene_variant_count": len(grouped_rows),
        "benchmark_classes": evaluation_classes,
        "oracle_ties_by_frame": oracle_ties_by_frame,
        "uniform_random_expectation": uniform_random_expectation,
        "elapsed_seconds": time.perf_counter() - started,
        "per_view": rows,
        "view_selection": policy_rows,
        "limitations": [
            "The scene uses proxy geometry, not the final Cesium digital twin.",
            "Cutouts are derived from VisDrone training imagery and overlap the detector domain.",
            f"{len(grouped_rows)} deterministic variants of one synthetic proxy scene are a smoke test, not a benchmark.",
            "Unsupported proxy classes are excluded and counted explicitly.",
            "The target class set is fixed once across the full capture, not per image.",
            "Tied best views are all counted as oracle matches; a deterministic representative is retained only for file compatibility.",
        ],
    }
    (output_dir / "summary.json").write_text(
        json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    lines = [
        "# DOVE-WM Isaac Proxy GT Smoke",
        "",
        "이 평가는 실제 GT를 읽지만 proxy geometry와 VisDrone-derived cutout을 사용한 파이프라인 smoke test입니다.",
        "실제 도시, 독립 일반화, detector SOTA 근거로 사용할 수 없습니다.",
        "",
        "| Scene variant | View | GT evaluable | Pred | Precision@.5 | Recall@.5 | F1@.5 |",
        "| --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in rows:
        lines.append(
            f"| {row['frame_index']} | {row['uav_id']} | {row['gt_count_evaluable']} | {row['prediction_count_evaluable']} | "
            f"{row['precision_at_iou50']:.4f} | {row['recall_at_iou50']:.4f} | {row['f1_at_iou50']:.4f} |"
        )
    lines.extend(["", "## View selection", ""])
    for row in policy_rows:
        lines.append(
            f"- variant {row['frame_index']} / {row['method']}: {row['selected_uav_id']}, "
            f"recall={row['selected_recall_at_iou50']:.4f}, "
            f"oracle regret={row['recall_regret']:.4f}"
        )
    (output_dir / "SUMMARY_KO.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    completion = {"status": result["status"], "output_dir": str(output_dir)}
    (output_dir / "run.log").write_text(
        json.dumps(completion, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(json.dumps(completion))


if __name__ == "__main__":
    main()
