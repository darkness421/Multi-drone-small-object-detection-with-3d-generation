#!/usr/bin/env python3
"""Evaluate minimal GT-supervised DOVE viewpoint models without scene leakage.

The current observation is one fixed camera RGB image. Candidate actions are
camera poses; candidate RGB images are outcomes and are never model inputs.
Every fold holds out one complete synthetic scene variant.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import time
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable, Mapping

import numpy as np
from PIL import Image
from sklearn.decomposition import PCA
from sklearn.linear_model import Ridge
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler


SEED = 20261016
TARGET_FIELD = "recall_at_iou50"
SECONDARY_FIELD = "f1_at_iou50"


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _write_csv(path: Path, rows: Iterable[Mapping[str, Any]]) -> None:
    materialised = list(rows)
    fields = list(dict.fromkeys(key for row in materialised for key in row)) or ["status"]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(materialised)


def _visual_features(path: Path) -> np.ndarray:
    """Compact deterministic encoder shared by both visual models."""

    with Image.open(path).convert("RGB") as image:
        image = image.resize((64, 36), Image.Resampling.BILINEAR)
        rgb = np.asarray(image, dtype=np.float64) / 255.0
    means = rgb.mean(axis=(0, 1))
    stds = rgb.std(axis=(0, 1))
    gray = 0.299 * rgb[..., 0] + 0.587 * rgb[..., 1] + 0.114 * rgb[..., 2]
    quadrants = np.asarray(
        [
            gray[:18, :32].mean(),
            gray[:18, 32:].mean(),
            gray[18:, :32].mean(),
            gray[18:, 32:].mean(),
        ]
    )
    gradients = np.asarray(
        [np.abs(np.diff(gray, axis=1)).mean(), np.abs(np.diff(gray, axis=0)).mean()]
    )
    return np.concatenate([means, stds, quadrants, gradients])


def _action_features(row: Mapping[str, Any], uav_ids: list[str]) -> np.ndarray:
    one_hot = np.asarray([float(row["uav_id"] == value) for value in uav_ids])
    continuous = np.asarray(
        [
            float(row["candidate_x_m"]),
            float(row["candidate_y_m"]),
            float(row["candidate_z_m"]),
            float(row["candidate_pitch_deg"]),
            float(row["candidate_yaw_deg"]),
            float(row["range_to_origin_m"]),
            float(row["movement_from_current_m"]),
        ]
    )
    return np.concatenate([continuous, one_hot])


def _conditional_visual_features(
    action: np.ndarray, visual: np.ndarray, one_hot: np.ndarray
) -> np.ndarray:
    """Add action-conditioned visual terms so RGB can change the ranking."""

    return np.concatenate([action, visual, np.outer(one_hot, visual).ravel()])


def _camera_distance(left: Mapping[str, Any], right: Mapping[str, Any]) -> float:
    return math.sqrt(
        sum(
            (float(left[key]) - float(right[key])) ** 2
            for key in ("x", "y", "z")
        )
    )


def build_dataset(
    capture_dir: Path,
    evaluation_dir: Path,
    current_uav_id: str,
    visual_embedding_csv: Path | None = None,
) -> tuple[list[dict[str, Any]], list[str], list[str]]:
    capture = json.loads(
        (capture_dir / "proxy_capture_summary.json").read_text(encoding="utf-8")
    )
    plan = json.loads((capture_dir / "capture_plan.json").read_text(encoding="utf-8"))
    metrics = _read_csv(evaluation_dir / "detector_gt_per_view.csv")
    views = {str(row["uav_id"]): row for row in plan["views"]}
    uav_ids = sorted(views)
    if current_uav_id not in views:
        raise ValueError(f"current UAV {current_uav_id!r} is not in {uav_ids}")
    records = {
        (str(row["uav_id"]), int(row["frame_index"])): row
        for row in capture["direct_capture"]["records"]
    }
    metric_rows = {
        (str(row["uav_id"]), int(row["frame_index"])): row for row in metrics
    }
    if set(records) != set(metric_rows):
        raise RuntimeError("capture records and detector evaluation rows do not match")

    visual_cache: dict[int, np.ndarray] = {}
    if visual_embedding_csv is not None:
        embedding_rows = _read_csv(visual_embedding_csv)
        embedding_fields = sorted(
            key for key in embedding_rows[0] if key.startswith("embedding_")
        )
        visual_cache = {
            int(row["scene_variant"]): np.asarray(
                [float(row[field]) for field in embedding_fields], dtype=np.float64
            )
            for row in embedding_rows
        }
        expected_variants = {key[1] for key in records}
        if set(visual_cache) != expected_variants:
            raise RuntimeError("visual embedding rows do not match capture scene variants")
    dataset = []
    current_pose = views[current_uav_id]["uav_pose"]
    for (uav_id, frame_index), record in sorted(records.items(), key=lambda item: item[0][1:]+item[0][:1]):
        current_record = records[(current_uav_id, frame_index)]
        current_path = capture_dir / current_record["rgb_path"]
        if frame_index not in visual_cache:
            visual_cache[frame_index] = _visual_features(current_path)
        visual = visual_cache[frame_index]
        view = views[uav_id]
        pose = view["uav_pose"]
        metric = metric_rows[(uav_id, frame_index)]
        row: dict[str, Any] = {
            "scene_variant": frame_index,
            "uav_id": uav_id,
            "view_angle": view["view_angle"],
            "current_uav_id": current_uav_id,
            "current_rgb_path": str(current_path),
            "candidate_rgb_outcome_path": str(capture_dir / record["rgb_path"]),
            "candidate_x_m": float(pose["x"]),
            "candidate_y_m": float(pose["y"]),
            "candidate_z_m": float(pose["z"]),
            "candidate_pitch_deg": float(pose["pitch"]),
            "candidate_yaw_deg": float(pose["yaw"]),
            "range_to_origin_m": float(metric["range_to_origin_m"]),
            "movement_from_current_m": _camera_distance(current_pose, pose),
            "object_layout_rotation_deg": float(record["object_layout_rotation_deg"]),
            "object_layout_offset_x_m": float(record["object_layout_offset_x_m"]),
            "object_layout_offset_y_m": float(record["object_layout_offset_y_m"]),
            "recall_at_iou50": float(metric["recall_at_iou50"]),
            "f1_at_iou50": float(metric["f1_at_iou50"]),
            "tp": int(metric["tp"]),
            "fp": int(metric["fp"]),
            "fn": int(metric["fn"]),
            "processed_pixels": int(metric["image_width"]) * int(metric["image_height"]),
        }
        for index, value in enumerate(visual):
            row[f"current_visual_{index:02d}"] = float(value)
        dataset.append(row)
    visual_fields = sorted(key for key in dataset[0] if key.startswith("current_visual_"))
    return dataset, uav_ids, visual_fields


def _feature_matrices(
    rows: list[dict[str, Any]],
    uav_ids: list[str],
    visual_fields: list[str],
    visual_projector: PCA | None = None,
) -> tuple[np.ndarray, np.ndarray]:
    geometry = []
    conditional = []
    for row in rows:
        action = _action_features(row, uav_ids)
        visual = np.asarray([float(row[field]) for field in visual_fields])
        if visual_projector is not None:
            visual = visual_projector.transform(visual.reshape(1, -1))[0]
        one_hot = np.asarray([float(row["uav_id"] == value) for value in uav_ids])
        geometry.append(action)
        conditional.append(_conditional_visual_features(action, visual, one_hot))
    return np.asarray(geometry), np.asarray(conditional)


def leave_one_scene_out_predictions(
    rows: list[dict[str, Any]],
    uav_ids: list[str],
    visual_fields: list[str],
    alpha: float,
    target_field: str = TARGET_FIELD,
    visual_pca_components: int = 0,
) -> list[dict[str, Any]]:
    """Fit every preprocessing step on seven variants and predict the eighth."""

    variants = sorted({int(row["scene_variant"]) for row in rows})
    output = []
    for held_out in variants:
        train = [row for row in rows if int(row["scene_variant"]) != held_out]
        test = [row for row in rows if int(row["scene_variant"]) == held_out]
        visual_projector = None
        if visual_pca_components > 0:
            scene_visuals = []
            for scene in sorted({int(row["scene_variant"]) for row in train}):
                representative = next(
                    row for row in train if int(row["scene_variant"]) == scene
                )
                scene_visuals.append(
                    [float(representative[field]) for field in visual_fields]
                )
            component_count = min(
                visual_pca_components,
                len(scene_visuals) - 1,
                len(visual_fields),
            )
            visual_projector = PCA(n_components=component_count, random_state=0).fit(
                np.asarray(scene_visuals)
            )
        xg_train, xv_train = _feature_matrices(
            train, uav_ids, visual_fields, visual_projector
        )
        xg_test, xv_test = _feature_matrices(
            test, uav_ids, visual_fields, visual_projector
        )
        y_train = np.asarray([float(row[target_field]) for row in train])

        geometry = make_pipeline(StandardScaler(), Ridge(alpha=alpha)).fit(xg_train, y_train)
        direct = make_pipeline(StandardScaler(), Ridge(alpha=alpha)).fit(xv_train, y_train)
        geometry_train = geometry.predict(xg_train)
        residual = make_pipeline(StandardScaler(), Ridge(alpha=alpha)).fit(
            xv_train, y_train - geometry_train
        )

        geometry_test = geometry.predict(xg_test)
        direct_test = direct.predict(xv_test)
        residual_test = geometry_test + residual.predict(xv_test)
        for row, geom, direct_value, residual_value in zip(
            test, geometry_test, direct_test, residual_test
        ):
            output.append(
                {
                    **row,
                    "held_out_scene_variant": held_out,
                    "geometry_ridge_prediction": float(geom),
                    "visual_direct_prediction": float(direct_value),
                    "geometry_visual_residual_prediction": float(residual_value),
                }
            )
    return sorted(output, key=lambda row: (row["scene_variant"], row["uav_id"]))


def _best(rows: list[dict[str, Any]], field: str) -> dict[str, Any]:
    return max(rows, key=lambda row: (float(row[field]), row["uav_id"]))


def select_actions(predictions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for row in predictions:
        grouped[int(row["scene_variant"])].append(row)
    prediction_fields = {
        "GEOMETRY_RIDGE": "geometry_ridge_prediction",
        "VISUAL_DIRECT_RIDGE": "visual_direct_prediction",
        "GEOMETRY_VISUAL_RESIDUAL_RIDGE": "geometry_visual_residual_prediction",
    }
    output = []
    for variant, group in sorted(grouped.items()):
        ordered = sorted(group, key=lambda row: row["uav_id"])
        oracle_value = max(float(row[TARGET_FIELD]) for row in ordered)
        oracle_ids = sorted(
            row["uav_id"]
            for row in ordered
            if math.isclose(float(row[TARGET_FIELD]), oracle_value, abs_tol=1.0e-12)
        )
        fixed = next(row for row in ordered if row["uav_id"] == row["current_uav_id"])
        minimum_movement = min(
            ordered, key=lambda row: (float(row["movement_from_current_m"]), row["uav_id"])
        )
        selections = {
            "FIXED_CURRENT_VIEW": fixed,
            "GEOMETRY_MIN_MOVEMENT": minimum_movement,
        }
        selections.update(
            {method: _best(ordered, field) for method, field in prediction_fields.items()}
        )
        for method, selected in selections.items():
            output.append(
                {
                    "scene_variant": variant,
                    "method": method,
                    "selected_uav_id": selected["uav_id"],
                    "selected_recall_at_iou50": selected[TARGET_FIELD],
                    "selected_f1_at_iou50": selected[SECONDARY_FIELD],
                    "movement_from_current_m": selected["movement_from_current_m"],
                    "oracle_recall_at_iou50": oracle_value,
                    "oracle_tied_uav_ids": ";".join(oracle_ids),
                    "oracle_match_tie_aware": selected["uav_id"] in oracle_ids,
                    "recall_regret": oracle_value - float(selected[TARGET_FIELD]),
                    "selection_mode": "single_held_out_scene_prediction",
                }
            )
        output.append(
            {
                "scene_variant": variant,
                "method": "UNIFORM_RANDOM_EXPECTATION",
                "selected_uav_id": "EXPECTED_OVER_ACTIONS",
                "selected_recall_at_iou50": float(
                    np.mean([float(row[TARGET_FIELD]) for row in ordered])
                ),
                "selected_f1_at_iou50": float(
                    np.mean([float(row[SECONDARY_FIELD]) for row in ordered])
                ),
                "movement_from_current_m": float(
                    np.mean([float(row["movement_from_current_m"]) for row in ordered])
                ),
                "oracle_recall_at_iou50": oracle_value,
                "oracle_tied_uav_ids": ";".join(oracle_ids),
                "oracle_match_tie_aware": len(oracle_ids) / len(ordered),
                "recall_regret": oracle_value
                - float(np.mean([float(row[TARGET_FIELD]) for row in ordered])),
                "selection_mode": "exact_uniform_expectation_not_sampled",
            }
        )
        oracle = min(
            (row for row in ordered if row["uav_id"] in oracle_ids),
            key=lambda row: (float(row["movement_from_current_m"]), row["uav_id"]),
        )
        output.append(
            {
                "scene_variant": variant,
                "method": "GT_RECALL_ORACLE",
                "selected_uav_id": oracle["uav_id"],
                "selected_recall_at_iou50": oracle[TARGET_FIELD],
                "selected_f1_at_iou50": oracle[SECONDARY_FIELD],
                "movement_from_current_m": oracle["movement_from_current_m"],
                "oracle_recall_at_iou50": oracle_value,
                "oracle_tied_uav_ids": ";".join(oracle_ids),
                "oracle_match_tie_aware": True,
                "recall_regret": 0.0,
                "selection_mode": "post_hoc_upper_bound",
            }
        )
    return output


def summarise(
    predictions: list[dict[str, Any]], selections: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    prediction_fields = {
        "GEOMETRY_RIDGE": "geometry_ridge_prediction",
        "VISUAL_DIRECT_RIDGE": "visual_direct_prediction",
        "GEOMETRY_VISUAL_RESIDUAL_RIDGE": "geometry_visual_residual_prediction",
    }
    output = []
    for method in sorted({row["method"] for row in selections}):
        rows = [row for row in selections if row["method"] == method]
        summary = {
            "method": method,
            "scene_variant_count": len(rows),
            "mean_selected_recall_at_iou50": float(
                np.mean([float(row["selected_recall_at_iou50"]) for row in rows])
            ),
            "mean_selected_f1_at_iou50": float(
                np.mean([float(row["selected_f1_at_iou50"]) for row in rows])
            ),
            "mean_recall_regret": float(
                np.mean([float(row["recall_regret"]) for row in rows])
            ),
            "oracle_match_rate_tie_aware": float(
                np.mean([float(row["oracle_match_tie_aware"]) for row in rows])
            ),
            "mean_movement_from_current_m": float(
                np.mean([float(row["movement_from_current_m"]) for row in rows])
            ),
        }
        field = prediction_fields.get(method)
        if field:
            errors = [float(row[field]) - float(row[TARGET_FIELD]) for row in predictions]
            summary["action_recall_rmse"] = float(np.sqrt(np.mean(np.square(errors))))
        output.append(summary)
    return output


def paired_bootstrap(
    selections: list[dict[str, Any]], repeats: int, seed: int
) -> list[dict[str, Any]]:
    by_method = {
        method: {
            int(row["scene_variant"]): float(row["selected_recall_at_iou50"])
            for row in selections
            if row["method"] == method
        }
        for method in {row["method"] for row in selections}
    }
    comparisons = [
        ("VISUAL_DIRECT_RIDGE", "GEOMETRY_RIDGE"),
        ("GEOMETRY_VISUAL_RESIDUAL_RIDGE", "GEOMETRY_RIDGE"),
        ("GEOMETRY_VISUAL_RESIDUAL_RIDGE", "VISUAL_DIRECT_RIDGE"),
    ]
    rng = np.random.default_rng(seed)
    output = []
    for left, right in comparisons:
        variants = sorted(set(by_method[left]) & set(by_method[right]))
        differences = np.asarray(
            [by_method[left][variant] - by_method[right][variant] for variant in variants]
        )
        indices = rng.integers(0, len(variants), size=(repeats, len(variants)))
        samples = differences[indices].mean(axis=1)
        output.append(
            {
                "left_method": left,
                "right_method": right,
                "scene_variant_count": len(variants),
                "mean_recall_difference": float(differences.mean()),
                "ci95_low": float(np.quantile(samples, 0.025)),
                "ci95_high": float(np.quantile(samples, 0.975)),
                "bootstrap_repeats": repeats,
                "seed": seed,
                "scope": "synthetic_proxy_scene_variants_not_independent_real_scenes",
            }
        )
    return output


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--capture-dir", required=True)
    parser.add_argument("--evaluation-dir", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--current-uav-id", default="uav_01")
    parser.add_argument("--visual-embedding-csv")
    parser.add_argument("--visual-pca-components", type=int, default=0)
    parser.add_argument("--ridge-alpha", type=float, default=1.0)
    parser.add_argument("--bootstrap-repeats", type=int, default=20000)
    parser.add_argument("--seed", type=int, default=SEED)
    args = parser.parse_args()

    capture_dir = Path(args.capture_dir).resolve()
    evaluation_dir = Path(args.evaluation_dir).resolve()
    output_dir = Path(args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    started = time.perf_counter()
    embedding_csv = (
        Path(args.visual_embedding_csv).resolve() if args.visual_embedding_csv else None
    )
    dataset, uav_ids, visual_fields = build_dataset(
        capture_dir, evaluation_dir, args.current_uav_id, embedding_csv
    )
    target_values = np.asarray([float(row[TARGET_FIELD]) for row in dataset])
    positive_variants = len(
        {
            int(row["scene_variant"])
            for row in dataset
            if float(row[TARGET_FIELD]) > 0.0
        }
    )
    identifiable = len(np.unique(target_values)) > 1 and positive_variants >= 2
    if identifiable:
        predictions = leave_one_scene_out_predictions(
            dataset,
            uav_ids,
            visual_fields,
            args.ridge_alpha,
            visual_pca_components=args.visual_pca_components,
        )
        selections = select_actions(predictions)
        model_summary = summarise(predictions, selections)
        bootstrap = paired_bootstrap(selections, args.bootstrap_repeats, args.seed)
        status = "COMPLETE_SYNTHETIC_PROXY_VISUAL_MODEL_PILOT"
    else:
        predictions = dataset
        selections = []
        model_summary = []
        bootstrap = []
        status = "NON_IDENTIFIABLE_GT_OUTCOME"

    _write_csv(output_dir / "gt_action_dataset.csv", dataset)
    _write_csv(output_dir / "oof_predictions.csv", predictions)
    _write_csv(output_dir / "selection_by_scene.csv", selections)
    _write_csv(output_dir / "model_summary.csv", model_summary)
    _write_csv(output_dir / "paired_scene_bootstrap.csv", bootstrap)
    scene_variant_count = len({row["scene_variant"] for row in dataset})
    visual_encoder_label = (
        "frozen detector embedding from current RGB"
        if embedding_csv
        else "shared deterministic 64x36 RGB moments, luminance quadrants, and gradient means"
    )
    result = {
        "status": status,
        "scope": f"{scene_variant_count} deterministic variants of one synthetic proxy scene",
        "claim_boundary": "pipeline and model pilot only; not real-scene generalization or paper-level world-model validation",
        "capture_dir": str(capture_dir),
        "evaluation_dir": str(evaluation_dir),
        "current_observation": args.current_uav_id,
        "candidate_actions": uav_ids,
        "target": TARGET_FIELD,
        "secondary_metric": SECONDARY_FIELD,
        "scene_variant_count": scene_variant_count,
        "action_count": len(dataset),
        "positive_target_scene_count": positive_variants,
        "ridge_alpha": args.ridge_alpha,
        "seed": args.seed,
        "split": "leave_one_complete_scene_variant_out; all preprocessing fit on training fold",
        "visual_encoder": visual_encoder_label,
        "visual_embedding_csv": str(embedding_csv) if embedding_csv else None,
        "raw_visual_feature_dimensions": len(visual_fields),
        "fold_local_visual_pca_components": args.visual_pca_components,
        "feature_model_bootstrap_elapsed_seconds": time.perf_counter() - started,
        "candidate_rgb_used_as_input": False,
        "model_summary": model_summary,
        "bootstrap": bootstrap,
        "limitations": [
            f"The {scene_variant_count} variants come from one proxy USD scene and are not independent real scenes.",
            "VisDrone-derived cutouts overlap the detector training domain.",
            f"Only {positive_variants} variants have non-zero recall, so estimates are high variance.",
            "This is a minimum frozen-encoder visual baseline, not a final deep world model.",
            "Memory, discovery, and closed-loop control are not implemented in this pilot.",
        ],
    }
    (output_dir / "summary.json").write_text(
        json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    lines = [
        "# DOVE GT 기반 최소 시각 모델 파일럿",
        "",
        f"- 상태: `{status}`",
        f"- 범위: 하나의 합성 proxy 장면에서 만든 {scene_variant_count}개 결정적 변형",
        f"- GT recall이 0보다 큰 장면: {positive_variants}/{scene_variant_count}",
        f"- 분할: 장면 변형 하나를 통째로 제외하는 {scene_variant_count}-fold 평가",
        f"- 시각 인코더: {visual_encoder_label}",
        "- 입력: 현재 uav_01 RGB와 후보 카메라 행동. 후보 결과 RGB는 입력에 사용하지 않음.",
        "",
        "| 방법 | Recall@.5 | F1@.5 | Recall regret | Oracle match | 이동 거리(m) |",
        "| --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in model_summary:
        lines.append(
            f"| {row['method']} | {row['mean_selected_recall_at_iou50']:.6f} | "
            f"{row['mean_selected_f1_at_iou50']:.6f} | {row['mean_recall_regret']:.6f} | "
            f"{row['oracle_match_rate_tie_aware']:.3f} | {row['mean_movement_from_current_m']:.3f} |"
        )
    lines.extend(
        [
            "",
            "이 결과는 시각 입력을 사용하는 코드 경로와 GT 기반 평가가 동작함을 확인하는 파일럿이다.",
            "실제 장면 일반화, 최종 world model 우위, closed-loop 성능의 근거로 사용할 수 없다.",
        ]
    )
    (output_dir / "SUMMARY_KO.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    completion = {"status": status, "output_dir": str(output_dir)}
    (output_dir / "run.log").write_text(
        json.dumps(completion, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(json.dumps(completion))


if __name__ == "__main__":
    main()
