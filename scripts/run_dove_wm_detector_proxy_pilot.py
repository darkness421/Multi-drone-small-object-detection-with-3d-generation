#!/usr/bin/env python3
"""Run a frozen-detector DOVE-WM counterfactual asset pilot.

The measured outcome is detector output, not ground truth. The script is meant
to establish whether materialized candidate views differ enough to justify a
proper GT-labelled viewpoint benchmark; it must not be reported as AP/recall.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import random
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
import sys
import time
from typing import Any, Iterable, Mapping

import numpy as np
from PIL import Image
from sklearn.linear_model import Ridge
from sklearn.multioutput import MultiOutputRegressor
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from detectors.wrappers import UltralyticsWrapper  # noqa: E402
from dove_wm.asset_audit import audit_assets  # noqa: E402
from evidence import save_tokens_jsonl  # noqa: E402


TARGET_ALIASES = {
    "pedestrian": {"pedestrian", "people", "person"},
    "car": {"car"},
    "bus": {"bus"},
}
FEATURE_FIELDS = ("altitude_m", "horizontal_range_m", "range_m", "inverse_range")
RANDOM_SEED = 20261015


def write_csv(path: Path, rows: Iterable[Mapping[str, Any]]) -> None:
    materialized = list(rows)
    fields = list(dict.fromkeys(key for row in materialized for key in row)) or ["status"]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(materialized)


def read_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise ValueError(path)
    return value


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def normalise_label(value: Any) -> str:
    return str(value or "").strip().lower().replace(" ", "_")


def view_metadata(actions: list[dict[str, Any]]) -> dict[tuple[str, str], dict[str, Any]]:
    index: dict[tuple[str, str], dict[str, Any]] = {}
    for session_path in sorted({row["session_path"] for row in actions}):
        plan = read_json(Path(session_path) / "capture_plan.json")
        for view in plan.get("views", []):
            if isinstance(view, dict):
                index[(Path(session_path).name, str(view.get("frame_id") or ""))] = view
    return index


def action_geometry(view: Mapping[str, Any]) -> dict[str, float]:
    pose = view.get("uav_pose") or {}
    metadata = view.get("metadata") or {}
    target = metadata.get("target_scene_units") or []
    if len(target) != 3 or not all(key in pose for key in ("x", "y", "z")):
        return {
            "altitude_m": float(view.get("altitude_m") or math.nan),
            "horizontal_range_m": math.nan,
            "range_m": math.nan,
            "inverse_range": math.nan,
        }
    dx = float(pose["x"]) - float(target[0])
    dy = float(pose["y"]) - float(target[1])
    dz = float(pose["z"]) - float(target[2])
    horizontal = math.hypot(dx, dy)
    distance = math.sqrt(dx * dx + dy * dy + dz * dz)
    return {
        "altitude_m": float(view.get("altitude_m") or pose["z"]),
        "horizontal_range_m": horizontal,
        "range_m": distance,
        "inverse_range": 1.0 / max(distance, 1.0e-9),
    }


def group_key(row: Mapping[str, Any]) -> tuple[str, str, str]:
    return str(row["session"]), str(row["scenario_id"]), str(row["hypothesis_id"])


def detector_actions(
    actions: list[dict[str, Any]],
    metadata: dict[tuple[str, str], dict[str, Any]],
    wrapper: UltralyticsWrapper,
    token_path: Path,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    tokens_all = []
    started = time.perf_counter()
    for index, action in enumerate(actions, start=1):
        view = metadata[(action["session"], action["frame_id"])]
        geometry = action_geometry(view)
        image_path = Path(action["rgb_path"])
        with Image.open(image_path) as image:
            width, height = image.size
        infer_started = time.perf_counter()
        tokens = wrapper.predict(
            image_path,
            {
                "image_id": action["image_id"],
                "uav_id": action["uav_id"],
                "timestamp": 0.0,
                "depth_path": action["depth_path"],
                "camera_intrinsic": view.get("camera_intrinsic", []),
                "camera_extrinsic": view.get("camera_extrinsic", []),
                "uav_pose": view.get("uav_pose", {}),
                "dove_session": action["session"],
                "dove_scenario_id": action["scenario_id"],
                "dove_hypothesis_id": action["hypothesis_id"],
                "dove_target_class": action["target_class"],
            },
        )
        inference_seconds = time.perf_counter() - infer_started
        tokens_all.extend(tokens)
        target = normalise_label(action["target_class"])
        aliases = TARGET_ALIASES.get(target, {target})
        target_tokens = [
            token
            for token in tokens
            if normalise_label(token.metadata.get("class_name")) in aliases
        ]
        confidences = [float(token.confidence) for token in target_tokens]
        area_ratio = sum(
            max(0.0, float(token.bbox_2d[2])) * max(0.0, float(token.bbox_2d[3]))
            for token in target_tokens
        ) / max(float(width * height), 1.0)
        row = {
            **{key: action[key] for key in (
                "session", "scenario_id", "hypothesis_id", "frame_id", "image_id",
                "uav_id", "target_class", "rgb_path", "depth_path",
            )},
            **geometry,
            "image_width": width,
            "image_height": height,
            "processed_pixels": width * height,
            "detector_token_count": len(tokens),
            "target_token_count": len(target_tokens),
            "target_max_confidence": max(confidences, default=0.0),
            "target_confidence_sum": sum(confidences),
            "target_bbox_area_ratio": area_ratio,
            "detector_proxy_utility": max(confidences, default=0.0),
            "inference_seconds": inference_seconds,
            "ground_truth_outcome": False,
        }
        rows.append(row)
        print(
            json.dumps(
                {
                    "track": "DOVE_WM_GPU0",
                    "action": index,
                    "actions": len(actions),
                    "group": "/".join(group_key(action)),
                    "target": target,
                    "utility": row["detector_proxy_utility"],
                    "seconds": inference_seconds,
                }
            ),
            flush=True,
        )
    save_tokens_jsonl(tokens_all, token_path)
    print(
        json.dumps(
            {
                "track": "DOVE_WM_GPU0",
                "status": "DETECTOR_COMPLETE",
                "actions": len(rows),
                "tokens": len(tokens_all),
                "seconds": time.perf_counter() - started,
            }
        ),
        flush=True,
    )
    return rows


def choose_policy_rows(actions: list[dict[str, Any]], seed: int) -> list[dict[str, Any]]:
    groups: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in actions:
        groups[group_key(row)].append(row)
    output = []
    for key, group in sorted(groups.items()):
        ordered = sorted(group, key=lambda row: row["frame_id"])
        oracle = max(ordered, key=lambda row: (row["detector_proxy_utility"], row["frame_id"]))
        geometry = min(ordered, key=lambda row: (row["range_m"], row["frame_id"]))
        rng = random.Random(f"{seed}:{'/'.join(key)}")
        selections = {
            "FIXED_FIRST_FEASIBLE": ordered[0],
            "DETERMINISTIC_RANDOM": rng.choice(ordered),
            "GEOMETRY_MIN_RANGE": geometry,
            "DETECTOR_PROXY_ORACLE": oracle,
        }
        for policy, selected in selections.items():
            output.append(
                {
                    "session": key[0],
                    "scenario_id": key[1],
                    "hypothesis_id": key[2],
                    "policy": policy,
                    "candidate_count": len(group),
                    "selected_frame_id": selected["frame_id"],
                    "selected_utility": selected["detector_proxy_utility"],
                    "oracle_utility": oracle["detector_proxy_utility"],
                    "regret": oracle["detector_proxy_utility"]
                    - selected["detector_proxy_utility"],
                    "selected_range_m": selected["range_m"],
                    "selected_target_count": selected["target_token_count"],
                    "outcome_scope": "frozen_detector_proxy_not_ground_truth",
                }
            )
    return output


def feature_matrix(rows: list[dict[str, Any]]) -> np.ndarray:
    return np.asarray([[float(row[field]) for field in FEATURE_FIELDS] for row in rows])


def leave_one_scene_predictions(actions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Small cross-scenario pilot; each original scenario is one held-out fold."""

    output = []
    scenarios = sorted({row["scenario_id"] for row in actions})
    for held_out in scenarios:
        train = [row for row in actions if row["scenario_id"] != held_out]
        test = [row for row in actions if row["scenario_id"] == held_out]
        x_train = feature_matrix(train)
        x_test = feature_matrix(test)
        y_train = np.asarray([row["detector_proxy_utility"] for row in train], dtype=float)
        direct = make_pipeline(StandardScaler(), Ridge(alpha=1.0)).fit(x_train, y_train)
        direct_prediction = direct.predict(x_test)

        latent_targets = np.asarray(
            [
                [
                    row["detector_proxy_utility"],
                    min(float(row["target_token_count"]) / 3.0, 1.0),
                    min(float(row["target_bbox_area_ratio"]) * 100.0, 1.0),
                ]
                for row in train
            ],
            dtype=float,
        )
        latent = make_pipeline(
            StandardScaler(), MultiOutputRegressor(Ridge(alpha=1.0))
        ).fit(x_train, latent_targets)
        latent_prediction = latent.predict(x_test)[:, 0]

        train_inverse = np.asarray([row["inverse_range"] for row in train], dtype=float)
        low, high = float(train_inverse.min()), float(train_inverse.max())
        scale = max(high - low, 1.0e-9)
        prior_train = np.clip((train_inverse - low) / scale, 0.0, 1.0)
        prior_test = np.clip(
            (np.asarray([row["inverse_range"] for row in test]) - low) / scale,
            0.0,
            1.0,
        )
        residual = make_pipeline(StandardScaler(), Ridge(alpha=1.0)).fit(
            x_train, y_train - prior_train
        )
        residual_prediction = prior_test + residual.predict(x_test)

        for row, direct_value, latent_value, residual_value in zip(
            test, direct_prediction, latent_prediction, residual_prediction
        ):
            output.append(
                {
                    **row,
                    "held_out_scenario": held_out,
                    "geometry_score": -float(row["range_m"]),
                    "direct_utility_prediction": float(direct_value),
                    "latent_outcome_utility_prediction": float(latent_value),
                    "geometry_structured_residual_prediction": float(residual_value),
                }
            )
    return output


def model_selection(predictions: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    groups: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in predictions:
        groups[group_key(row)].append(row)
    fields = {
        "GEOMETRY_ONLY": "geometry_score",
        "DIRECT_UTILITY_RIDGE": "direct_utility_prediction",
        "LATENT_OUTCOME_RIDGE": "latent_outcome_utility_prediction",
        "GEOMETRY_STRUCTURED_RESIDUAL": "geometry_structured_residual_prediction",
    }
    rows = []
    for key, group in sorted(groups.items()):
        oracle = max(group, key=lambda row: (row["detector_proxy_utility"], row["frame_id"]))
        for method, field in fields.items():
            selected = max(group, key=lambda row: (row[field], row["frame_id"]))
            rows.append(
                {
                    "session": key[0],
                    "scenario_id": key[1],
                    "hypothesis_id": key[2],
                    "method": method,
                    "selected_frame_id": selected["frame_id"],
                    "selected_utility": selected["detector_proxy_utility"],
                    "oracle_utility": oracle["detector_proxy_utility"],
                    "regret": oracle["detector_proxy_utility"]
                    - selected["detector_proxy_utility"],
                    "oracle_match": int(selected["frame_id"] == oracle["frame_id"]),
                    "held_out_scenario": selected["held_out_scenario"],
                }
            )
    summary = []
    for method in fields:
        selected = [row for row in rows if row["method"] == method]
        prediction_field = fields[method]
        action_error = [
            float(row[prediction_field]) - float(row["detector_proxy_utility"])
            for row in predictions
        ]
        summary.append(
            {
                "method": method,
                "group_count": len(selected),
                "mean_selected_detector_proxy_utility": float(
                    np.mean([row["selected_utility"] for row in selected])
                ),
                "mean_best_view_regret": float(np.mean([row["regret"] for row in selected])),
                "oracle_match_rate": float(np.mean([row["oracle_match"] for row in selected])),
                "action_utility_rmse": float(np.sqrt(np.mean(np.square(action_error)))),
                "evaluation_scope": "leave_one_original_scenario_out_detector_proxy_pilot",
            }
        )
    return rows, summary


def summary_markdown(
    actions: list[dict[str, Any]], policies: list[dict[str, Any]], models: list[dict[str, Any]]
) -> str:
    policy_summary = {
        policy: (
            float(np.mean([row["selected_utility"] for row in policies if row["policy"] == policy])),
            float(np.mean([row["regret"] for row in policies if row["policy"] == policy])),
        )
        for policy in sorted({row["policy"] for row in policies})
    }
    model_lines = "\n".join(
        f"- {row['method']}: utility {row['mean_selected_detector_proxy_utility']:.4f}, "
        f"regret {row['mean_best_view_regret']:.4f}, oracle match {row['oracle_match_rate']:.3f}"
        for row in models
    )
    policy_lines = "\n".join(
        f"- {name}: utility {values[0]:.4f}, regret {values[1]:.4f}"
        for name, values in policy_summary.items()
    )
    return f"""# DOVE-WM Detector-Proxy Pilot

## Measured scope

- Materialized actions: {len(actions)}
- Multi-action groups: {len({group_key(row) for row in actions})}
- Original scenarios: {len({row['scenario_id'] for row in actions})}
- Outcome: frozen detector maximum target-class confidence, not GT AP/recall.

## Fixed policies

{policy_lines}

## Minimal model pilot

{model_lines}

## Claim boundary

This run establishes pipeline execution and detector-output variation only. It does not establish true viewpoint utility, world-model accuracy, dense-scene AP, or online UAV performance. Confidence/uncertainty selection from the current observation is not evaluated because a frozen current-observation-to-candidate tuple is not yet present.
"""


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--capture-root", type=Path, required=True)
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--device", default="0")
    parser.add_argument("--imgsz", type=int, default=1280)
    parser.add_argument("--conf", type=float, default=0.01)
    parser.add_argument("--seed", type=int, default=RANDOM_SEED)
    args = parser.parse_args()
    if args.output_dir.exists():
        raise FileExistsError(args.output_dir)
    args.output_dir.mkdir(parents=True)

    audit = audit_assets(args.capture_root)
    complete_keys = {
        (row["session"], row["scenario_id"], row["hypothesis_id"])
        for row in audit["action_groups"]
        if row["complete_multi_action_materialization"]
    }
    actions = [
        row
        for row in audit["actions"]
        if group_key(row) in complete_keys and row["rgb_exists"] and row["depth_exists"]
    ]
    if len(complete_keys) != 12 or len(actions) != 45:
        raise RuntimeError(
            f"Frozen preflight mismatch: groups={len(complete_keys)}, actions={len(actions)}"
        )
    metadata = view_metadata(actions)
    wrapper = UltralyticsWrapper(
        str(args.checkpoint),
        predict_kwargs={"device": args.device, "imgsz": args.imgsz, "conf": args.conf},
    )
    outcome_rows = detector_actions(
        actions, metadata, wrapper, args.output_dir / "evidence_tokens.jsonl"
    )
    policy_rows = choose_policy_rows(outcome_rows, args.seed)
    predictions = leave_one_scene_predictions(outcome_rows)
    model_rows, model_summary = model_selection(predictions)
    write_csv(args.output_dir / "action_outcomes.csv", outcome_rows)
    write_csv(args.output_dir / "fixed_policy_selections.csv", policy_rows)
    write_csv(args.output_dir / "model_action_predictions.csv", predictions)
    write_csv(args.output_dir / "model_selection_results.csv", model_rows)
    write_csv(args.output_dir / "model_summary.csv", model_summary)
    (args.output_dir / "SUMMARY.md").write_text(
        summary_markdown(outcome_rows, policy_rows, model_summary), encoding="utf-8"
    )
    manifest = {
        "status": "COMPLETE_DETECTOR_PROXY_PILOT",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "capture_root": str(args.capture_root.resolve()),
        "checkpoint": str(args.checkpoint.resolve()),
        "checkpoint_sha256": sha256(args.checkpoint),
        "device": args.device,
        "imgsz": args.imgsz,
        "confidence_threshold": args.conf,
        "random_seed": args.seed,
        "actions": len(outcome_rows),
        "groups": len(complete_keys),
        "original_scenarios": sorted({row["scenario_id"] for row in outcome_rows}),
        "outcome_definition": "maximum frozen-detector confidence among target-class detections",
        "ground_truth_outcomes": False,
        "implemented": [
            "frozen detector outcome materialization",
            "fixed-first, deterministic-random, geometry-min-range, detector-proxy oracle",
            "leave-one-original-scenario-out geometry/direct/latent/structured-residual pilot",
        ],
        "not_implemented_or_not_validated": [
            "GT AP/recall viewpoint benchmark",
            "current-observation confidence/uncertainty selector",
            "temporal memory",
            "unknown-object discovery",
            "listwise neural ranker",
            "closed-loop simulator or UAV flight",
        ],
    }
    (args.output_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps({"status": manifest["status"], "output_dir": str(args.output_dir)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
