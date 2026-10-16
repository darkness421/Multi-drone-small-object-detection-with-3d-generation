#!/usr/bin/env python3
"""Audit the controlled DOVE UV render A/B and tie-aware proxy selection."""

from __future__ import annotations

import argparse
from collections import defaultdict
import csv
import json
from pathlib import Path
from typing import Any, Iterable, Mapping

import numpy as np
from PIL import Image


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: Iterable[Mapping[str, Any]]) -> None:
    materialized = list(rows)
    fields = list(dict.fromkeys(key for row in materialized for key in row)) or ["status"]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(materialized)


def _group_key(row: Mapping[str, Any]) -> tuple[str, str, str]:
    return str(row["session"]), str(row["scenario_id"]), str(row["hypothesis_id"])


def tie_aware_proxy_audit(
    action_outcomes: Path,
    model_selections: Path,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    outcomes = read_csv(action_outcomes)
    selections = read_csv(model_selections)
    grouped: dict[tuple[str, str, str], list[dict[str, str]]] = defaultdict(list)
    lookup: dict[tuple[tuple[str, str, str], str], float] = {}
    for row in outcomes:
        key = _group_key(row)
        grouped[key].append(row)
        lookup[(key, row["frame_id"])] = float(row["detector_proxy_utility"])

    audit_rows = []
    for row in selections:
        key = _group_key(row)
        candidate_rows = grouped[key]
        utilities = [float(item["detector_proxy_utility"]) for item in candidate_rows]
        oracle_utility = max(utilities)
        oracle_frames = sorted(
            item["frame_id"]
            for item in candidate_rows
            if np.isclose(
                float(item["detector_proxy_utility"]),
                oracle_utility,
                rtol=0.0,
                atol=1.0e-12,
            )
        )
        selected_frame = row["selected_frame_id"]
        selected_utility = lookup[(key, selected_frame)]
        audit_rows.append(
            {
                "session": key[0],
                "scenario_id": key[1],
                "hypothesis_id": key[2],
                "method": row["method"],
                "selected_frame_id": selected_frame,
                "selected_utility_recomputed": selected_utility,
                "oracle_utility_recomputed": oracle_utility,
                "oracle_frame_ids": ";".join(oracle_frames),
                "oracle_tie_count": len(oracle_frames),
                "oracle_match_tie_aware": int(selected_frame in oracle_frames),
                "uniform_random_expected_utility": float(np.mean(utilities)),
                "candidate_count": len(candidate_rows),
            }
        )

    methods = sorted({row["method"] for row in audit_rows})
    summary_rows = []
    for method in methods:
        rows = [row for row in audit_rows if row["method"] == method]
        summary_rows.append(
            {
                "method": method,
                "group_count": len(rows),
                "tie_aware_oracle_matches": sum(
                    int(row["oracle_match_tie_aware"]) for row in rows
                ),
                "mean_selected_utility": float(
                    np.mean([float(row["selected_utility_recomputed"]) for row in rows])
                ),
                "mean_oracle_utility": float(
                    np.mean([float(row["oracle_utility_recomputed"]) for row in rows])
                ),
                "mean_uniform_random_expected_utility": float(
                    np.mean([float(row["uniform_random_expected_utility"]) for row in rows])
                ),
                "groups_with_oracle_ties": sum(
                    int(row["oracle_tie_count"]) > 1 for row in rows
                ),
            }
        )
    return audit_rows, summary_rows


def _image(path: Path) -> np.ndarray:
    return np.asarray(Image.open(path).convert("RGB"), dtype=np.int16)


def uv_pixel_audit(uv_root: Path, eval_root: Path) -> list[dict[str, Any]]:
    gt_rows = [
        row
        for row in read_csv(eval_root / "eval_uv_on" / "bbox_coordinate_audit.csv")
        if row["source"] == "gt"
    ]
    gt_by_uav: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in gt_rows:
        gt_by_uav[row["uav_id"]].append(row)

    rows = []
    for uav_id in sorted(gt_by_uav):
        off_path = uv_root / "uv_off" / "direct" / uav_id / "rgb_0000.png"
        on_path = uv_root / "uv_on" / "direct" / uav_id / "rgb_0000.png"
        off = _image(off_path)
        on = _image(on_path)
        diff = np.abs(on - off)
        rows.append(
            {
                "uav_id": uav_id,
                "region": "full_image",
                "gt_index": "",
                "canonical": "",
                "width": off.shape[1],
                "height": off.shape[0],
                "uv_off_mean": float(off.mean()),
                "uv_on_mean": float(on.mean()),
                "uv_off_std": float(off.std()),
                "uv_on_std": float(on.std()),
                "mean_absolute_pixel_delta": float(diff.mean()),
                "changed_pixel_count": int(np.any(diff > 0, axis=2).sum()),
                "max_absolute_channel_delta": int(diff.max()),
            }
        )
        for gt in gt_by_uav[uav_id]:
            x1 = int(np.floor(float(gt["x1"])))
            y1 = int(np.floor(float(gt["y1"])))
            x2 = int(np.ceil(float(gt["x2"])))
            y2 = int(np.ceil(float(gt["y2"])))
            off_crop = off[y1:y2, x1:x2]
            on_crop = on[y1:y2, x1:x2]
            crop_diff = np.abs(on_crop - off_crop)
            rows.append(
                {
                    "uav_id": uav_id,
                    "region": "gt_box",
                    "gt_index": gt["index"],
                    "canonical": gt["canonical"],
                    "width": x2 - x1,
                    "height": y2 - y1,
                    "uv_off_mean": float(off_crop.mean()),
                    "uv_on_mean": float(on_crop.mean()),
                    "uv_off_std": float(off_crop.std()),
                    "uv_on_std": float(on_crop.std()),
                    "mean_absolute_pixel_delta": float(crop_diff.mean()),
                    "changed_pixel_count": int(np.any(crop_diff > 0, axis=2).sum()),
                    "max_absolute_channel_delta": int(crop_diff.max()),
                }
            )
    return rows


def detector_ab_rows(eval_root: Path) -> list[dict[str, Any]]:
    rows = []
    evaluations = (
        ("off", "0.01", "eval_uv_off"),
        ("on", "0.01", "eval_uv_on"),
        ("off", "0.001", "eval_uv_off_conf001"),
        ("on", "0.001", "eval_uv_on_conf001"),
    )
    for uv_mode, threshold, directory in evaluations:
        per_view = read_csv(eval_root / directory / "detector_gt_per_view.csv")
        rows.append(
            {
                "uv_mode": uv_mode,
                "confidence_threshold": threshold,
                "view_count": len(per_view),
                "gt_evaluable": sum(int(row["gt_count_evaluable"]) for row in per_view),
                "predictions_all": sum(int(row["prediction_count_all"]) for row in per_view),
                "predictions_target_classes": sum(
                    int(row["prediction_count_evaluable"]) for row in per_view
                ),
                "true_positives": sum(int(row["tp"]) for row in per_view),
                "false_positives": sum(int(row["fp"]) for row in per_view),
                "false_negatives": sum(int(row["fn"]) for row in per_view),
                "mean_recall_at_iou50": float(
                    np.mean([float(row["recall_at_iou50"]) for row in per_view])
                ),
                "mean_target_max_confidence": float(
                    np.mean([float(row["max_detector_confidence"]) for row in per_view])
                ),
                "all_boxes_inside_saved_images": int(
                    all(
                        row["gt_boxes_inside_image"] == "True"
                        and row["prediction_boxes_inside_image"] == "True"
                        for row in per_view
                    )
                ),
            }
        )
    return rows


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--uv-root", type=Path, required=True)
    parser.add_argument("--proxy-pilot-root", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    if args.output_dir.exists():
        raise FileExistsError(args.output_dir)
    args.output_dir.mkdir(parents=True)

    tie_rows, tie_summary = tie_aware_proxy_audit(
        args.proxy_pilot_root / "action_outcomes.csv",
        args.proxy_pilot_root / "model_selection_results.csv",
    )
    pixel_rows = uv_pixel_audit(args.uv_root, args.uv_root)
    detector_rows = detector_ab_rows(args.uv_root)
    write_csv(args.output_dir / "proxy_selection_tie_aware.csv", tie_rows)
    write_csv(args.output_dir / "proxy_selection_tie_aware_summary.csv", tie_summary)
    write_csv(args.output_dir / "uv_pixel_ab.csv", pixel_rows)
    write_csv(args.output_dir / "uv_detector_ab.csv", detector_rows)

    on_summary = json.loads(
        (args.uv_root / "uv_on" / "proxy_capture_summary.json").read_text(
            encoding="utf-8"
        )
    )
    camera_rows = on_summary["stage_summary"]["uavs"]
    calibration = [
        {
            "uav_id": row["uav_id"],
            "configured_focal_px": row["configured_focal_px"],
            "recovered_focal_px": (
                float(row["focal_length_mm"])
                * int(row["render_resolution"][0])
                / float(row["horizontal_aperture_mm"])
            ),
            "focal_length_mm": row["focal_length_mm"],
            "horizontal_aperture_mm": row["horizontal_aperture_mm"],
            "vertical_aperture_mm": row["vertical_aperture_mm"],
            "render_width": row["render_resolution"][0],
            "render_height": row["render_resolution"][1],
            "look_at_target_xyz_m": json.dumps(row["look_at_target_xyz_m"]),
        }
        for row in camera_rows
    ]
    write_csv(args.output_dir / "camera_calibration_audit.csv", calibration)

    manifest = {
        "status": "COMPLETE",
        "uv_ab_scope": "same proxy scene, corrected intrinsics, UV wiring toggled only",
        "texture_coordinates_connected_in_uv_on": on_summary["stage_summary"][
            "texture_coordinates_connected"
        ],
        "proxy_tie_group_count": len({(_group_key(row)) for row in read_csv(
            args.proxy_pilot_root / "action_outcomes.csv"
        )}),
        "detector_outcome_informative_for_visual_model": any(
            int(row["true_positives"]) > 0 for row in detector_rows
        ),
        "limitations": [
            "The proxy scene remains synthetic and uses VisDrone-derived cutouts.",
            "UV wiring changes image pixels but zero TP means recall-based world-model training is not yet identified.",
            "The proxy pilot target is detector confidence, not GT detection success.",
        ],
        "command": " ".join(__import__("sys").argv),
    }
    (args.output_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(manifest, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
