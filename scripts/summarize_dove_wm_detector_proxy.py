#!/usr/bin/env python3
"""Add calibration, ranking, and runtime diagnostics to a DOVE-WM proxy run."""

from __future__ import annotations

import argparse
from collections import defaultdict
import csv
import json
from pathlib import Path
import sys
import time
from typing import Any, Iterable, Mapping

import numpy as np
from scipy.stats import spearmanr


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.run_dove_wm_detector_proxy_pilot import (  # noqa: E402
    group_key,
    leave_one_scene_predictions,
)


METHOD_FIELDS = {
    "GEOMETRY_ONLY": "geometry_score",
    "DIRECT_UTILITY_RIDGE": "direct_utility_prediction",
    "LATENT_OUTCOME_RIDGE": "latent_outcome_utility_prediction",
    "GEOMETRY_STRUCTURED_RESIDUAL": "geometry_structured_residual_prediction",
}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: Iterable[Mapping[str, Any]]) -> None:
    materialized = list(rows)
    fields = list(dict.fromkeys(key for row in materialized for key in row)) or ["status"]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(materialized)


def pairwise_accuracy(rows: list[dict[str, str]], field: str) -> tuple[int, int, float]:
    groups: dict[tuple[str, str, str], list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        groups[group_key(row)].append(row)
    correct = comparable = 0
    for group in groups.values():
        for left_index, left in enumerate(group):
            for right in group[left_index + 1:]:
                true_delta = float(left["detector_proxy_utility"]) - float(right["detector_proxy_utility"])
                if abs(true_delta) <= 1.0e-12:
                    continue
                predicted_delta = float(left[field]) - float(right[field])
                comparable += 1
                correct += int(predicted_delta * true_delta > 0)
    return correct, comparable, correct / comparable if comparable else float("nan")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--benchmark-repeats", type=int, default=100)
    args = parser.parse_args()
    predictions = read_csv(args.run_dir / "model_action_predictions.csv")
    actions = read_csv(args.run_dir / "action_outcomes.csv")
    selections = read_csv(args.run_dir / "model_selection_results.csv")
    true = np.asarray([float(row["detector_proxy_utility"]) for row in predictions])
    diagnostics = []
    for method, field in METHOD_FIELDS.items():
        predicted = np.asarray([float(row[field]) for row in predictions])
        chosen = [row for row in selections if row["method"] == method]
        correct, comparable, pair_accuracy = pairwise_accuracy(predictions, field)
        calibration_available = method != "GEOMETRY_ONLY"
        correlation = spearmanr(predicted, true).statistic
        diagnostics.append({
            "method": method,
            "action_count": len(predictions),
            "group_count": len(chosen),
            "mean_selected_detector_proxy_utility": float(np.mean([float(row["selected_utility"]) for row in chosen])),
            "mean_best_view_regret": float(np.mean([float(row["regret"]) for row in chosen])),
            "oracle_match_rate": float(np.mean([int(row["oracle_match"]) for row in chosen])),
            "spearman_action_utility": float(correlation),
            "pairwise_ranking_correct": correct,
            "pairwise_ranking_comparable": comparable,
            "pairwise_ranking_accuracy": pair_accuracy,
            "utility_calibration_available": int(calibration_available),
            "action_utility_mae": float(np.mean(np.abs(predicted - true))) if calibration_available else "",
            "action_utility_rmse": float(np.sqrt(np.mean(np.square(predicted - true)))) if calibration_available else "",
            "action_utility_bias": float(np.mean(predicted - true)) if calibration_available else "",
            "evaluation_scope": "leave_one_original_scenario_out_detector_proxy_pilot",
        })

    direct = np.asarray([float(row["direct_utility_prediction"]) for row in predictions])
    latent = np.asarray([float(row["latent_outcome_utility_prediction"]) for row in predictions])
    inference = np.asarray([float(row["inference_seconds"]) for row in actions])
    repeats = []
    for _ in range(args.benchmark_repeats):
        started = time.perf_counter()
        leave_one_scene_predictions(actions)
        repeats.append(time.perf_counter() - started)
    runtime = {
        "detector_actions": len(actions),
        "detector_seconds_total": float(inference.sum()),
        "detector_seconds_mean": float(inference.mean()),
        "detector_seconds_median": float(np.median(inference)),
        "detector_seconds_p95": float(np.quantile(inference, 0.95)),
        "detector_seconds_first_action_warmup": float(inference[0]),
        "detector_seconds_mean_excluding_first": float(inference[1:].mean()),
        "model_fit_predict_repeats": args.benchmark_repeats,
        "model_fit_predict_seconds_mean": float(np.mean(repeats)),
        "model_fit_predict_seconds_p95": float(np.quantile(repeats, 0.95)),
        "direct_latent_predictions_identical": bool(np.allclose(direct, latent, atol=1.0e-12, rtol=0.0)),
        "direct_latent_max_abs_difference": float(np.max(np.abs(direct - latent))),
        "runtime_boundary": "Detector time is per materialized image; model overhead refits all three leave-one-scenario folds for 45 cached action rows.",
    }
    write_csv(args.run_dir / "model_diagnostics.csv", diagnostics)
    (args.run_dir / "runtime_diagnostics.json").write_text(
        json.dumps(runtime, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    lines = [
        "# DOVE-WM Proxy Diagnostics",
        "",
        "This audit uses detector confidence as the outcome. It is not GT AP, recall, or viewpoint utility.",
        "",
        f"- Original scenarios: {len({row['scenario_id'] for row in actions})}",
        f"- Multi-action groups: {len({group_key(row) for row in actions})}",
        f"- Materialized actions: {len(actions)}",
        f"- Direct and latent utility predictions identical: {runtime['direct_latent_predictions_identical']}",
        f"- Detector mean time excluding first warmup: {runtime['detector_seconds_mean_excluding_first']:.4f} s/action",
        "",
        "## Model Diagnostics",
        "",
    ]
    for row in diagnostics:
        calibration = (
            f", MAE {float(row['action_utility_mae']):.4f}"
            if row["utility_calibration_available"] else ", calibration N/A (ranking score only)"
        )
        lines.append(
            f"- {row['method']}: utility {row['mean_selected_detector_proxy_utility']:.4f}, "
            f"regret {row['mean_best_view_regret']:.4f}, pairwise accuracy "
            f"{row['pairwise_ranking_accuracy']:.3f}{calibration}"
        )
    lines.extend([
        "",
        "The latent model's first output is an independently fitted Ridge target identical to the direct model, so this pilot shows no separate latent-decomposition benefit.",
        "",
    ])
    (args.run_dir / "DIAGNOSTICS.md").write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps({"status": "COMPLETE", **runtime}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
