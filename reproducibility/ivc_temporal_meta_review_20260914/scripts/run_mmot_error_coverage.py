#!/usr/bin/env python3
"""Generate descriptive MMOT link error-coverage curves on frozen tracklets.

The grids are reported in full and are not used to select a new operating
point. Every curve point is evaluated as a complete trajectory remapping.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import json
import os
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
import torch
from scipy.optimize import linear_sum_assignment


APPEARANCE_GRID = (0.05, 0.10, 0.15, 0.20, 0.25, 0.30)
AFLINK_COST_GRID = (0.01, 0.025, 0.05, 0.10, 0.20, 0.40)


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")


def write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = sorted({key for row in rows for key in row})
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def load_descriptors(path: Path) -> dict[int, np.ndarray]:
    with np.load(path) as payload:
        return {int(key): payload[key] for key in payload.files}


def aflink_scores(bench, runtime, predictions: dict, batch_size: int) -> tuple[list[dict], float]:
    frames, rows = bench.prediction_tracklets(predictions)
    identities = sorted(frames)
    candidates = []
    pairs = []
    for source in identities:
        source_track = np.asarray([
            [frame, row["x"], row["y"], row["w"], row["h"]]
            for frame, row in rows[source]
        ], dtype=np.float32)
        fi, xi, yi = source_track[-1, :3]
        for destination in identities:
            if source == destination:
                continue
            destination_track = np.asarray([
                [frame, row["x"], row["y"], row["w"], row["h"]]
                for frame, row in rows[destination]
            ], dtype=np.float32)
            fj, xj, yj = destination_track[0, :3]
            gap = float(fj - fi)
            spatial = float(np.hypot(xi - xj, yi - yj))
            if not (bench.AF_THR_T[0] <= gap < bench.AF_THR_T[1]) or spatial > bench.AF_THR_S:
                continue
            candidates.append({
                "earlier": source, "later": destination, "gap": int(gap),
                "endpoint_top_left_distance_pixels": spatial,
            })
            pairs.append((source_track, destination_track))
    started = time.perf_counter()
    bench.cuda_sync(runtime.device)
    probabilities = runtime.scores(pairs, batch_size)
    bench.cuda_sync(runtime.device)
    elapsed = time.perf_counter() - started
    for edge, probability in zip(candidates, probabilities):
        edge["aflink_probability"] = float(probability)
        edge["aflink_cost"] = float(1.0 - probability)
    return candidates, elapsed


def aflink_assignment(edges: list[dict], threshold: float) -> list[dict]:
    valid = [edge for edge in edges if edge["aflink_cost"] <= threshold]
    if not valid:
        return []
    identities = sorted({edge["earlier"] for edge in valid} | {edge["later"] for edge in valid})
    index = {identity: position for position, identity in enumerate(identities)}
    matrix = np.full((len(identities), len(identities)), 1e5, dtype=float)
    lookup = {}
    for edge in valid:
        row, column = index[edge["earlier"]], index[edge["later"]]
        if edge["aflink_cost"] < matrix[row, column]:
            matrix[row, column] = edge["aflink_cost"]
            lookup[(row, column)] = edge
    row_mask = matrix.min(axis=1) < threshold
    column_mask = matrix.min(axis=0) < threshold
    if not row_mask.any() or not column_mask.any():
        return []
    compressed = matrix[row_mask][:, column_mask]
    row_ids = np.asarray(identities)[row_mask]
    column_ids = np.asarray(identities)[column_mask]
    rr, cc = linear_sum_assignment(compressed)
    output = []
    for row, column in zip(rr, cc):
        source, destination = int(row_ids[row]), int(column_ids[column])
        original = (index[source], index[destination])
        if compressed[row, column] < threshold:
            output.append(lookup[original])
    return output


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--benchmark-script", type=Path, required=True)
    parser.add_argument("--workspace", type=Path, required=True)
    parser.add_argument("--data-cache", type=Path, required=True)
    parser.add_argument("--e0-dir", type=Path, required=True)
    parser.add_argument("--byte-oc-result-dir", type=Path, required=True)
    parser.add_argument("--deepoc-result-dir", type=Path, required=True)
    parser.add_argument("--deepoc-tracker-dir", type=Path, required=True)
    parser.add_argument("--aflink-root", type=Path, required=True)
    parser.add_argument("--aflink-checkpoint", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--device", default="cuda:0")
    parser.add_argument("--aflink-batch-size", type=int, default=512)
    parser.add_argument("--trackers", nargs="+", choices=("bytetrack", "ocsort", "deepocsort"), default=["bytetrack", "ocsort", "deepocsort"])
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    sys.path.insert(0, str(args.workspace / "third_party/trackeval_official"))
    sys.path.insert(0, str(args.workspace / "third_party/boxmot_official"))
    bench = load_module("error_coverage_benchmark", args.benchmark_script)
    mmot = bench.load_module("error_coverage_mmot", args.workspace / "scripts/run_mmot_locked_temporal.py")
    device = torch.device(args.device)
    if device.type == "cuda" and not torch.cuda.is_available():
        raise SystemExit("CUDA requested but unavailable")
    af_runtime, af_manifest = bench.load_aflink(args.aflink_root, args.aflink_checkpoint, device)
    with torch.inference_mode():
        af_runtime.model(
            torch.zeros((2, 1, 30, 5), device=device),
            torch.zeros((2, 1, 30, 5), device=device),
        )
    bench.cuda_sync(device)

    family_roots = {
        "data28": args.data_cache / "raw/MMOT/extracted/test",
        "data30": args.data_cache / "raw/MMOT/extracted/confirmatory_data30",
    }
    records = []
    link_records = []
    runtime_rows = []
    accepted_rows = []
    invalid_outputs = []
    started_all = time.perf_counter()
    for family, family_root in family_roots.items():
        for sequence_dir in sorted(path for path in family_root.iterdir() if path.is_dir()):
            frames, image_map, _, _ = mmot.load_sequence(sequence_dir)
            for class_id, class_name in enumerate(bench.CLASS_NAMES):
                gt = mmot.class_frames(frames, class_id)
                if not gt:
                    continue
                for tracker in args.trackers:
                    context = {
                        "family": family, "sequence": sequence_dir.name,
                        "class_name": class_name, "tracker": tracker,
                    }
                    if tracker in {"bytetrack", "ocsort"}:
                        prediction_path = (
                            args.e0_dir / "results_raw/tracker_outputs" / family /
                            sequence_dir.name / class_name / f"{tracker}.jsonl.gz"
                        )
                        descriptor_path = (
                            args.byte_oc_result_dir / "descriptors" / family /
                            sequence_dir.name / class_name / f"{tracker}.npz"
                        )
                    else:
                        prediction_path = (
                            args.deepoc_tracker_dir / "tracker_outputs" / family /
                            sequence_dir.name / class_name / "deepocsort.jsonl.gz"
                        )
                        descriptor_path = (
                            args.deepoc_result_dir / "descriptors" / family /
                            sequence_dir.name / class_name / "deepocsort.npz"
                        )
                    predictions = bench.load_predictions(prediction_path)
                    descriptors = load_descriptors(descriptor_path)
                    candidates, eligible_sources = bench.build_candidates(predictions, descriptors)
                    labels = mmot.M3OT_GRAPH.tracklet_gt_labels(gt, predictions)
                    af_candidates, af_seconds = aflink_scores(
                        bench, af_runtime, predictions, args.aflink_batch_size
                    )
                    runtime_rows.append({**context, "aflink_candidate_count": len(af_candidates), "aflink_model_seconds": af_seconds})

                    points = []
                    for threshold in APPEARANCE_GRID:
                        gated = [
                            edge for edge in candidates
                            if edge["cosine_distance"] is not None
                            and edge["endpoint_center_distance_pixels"] <= bench.GEOMETRY_RADIUS
                            and edge["cosine_distance"] <= threshold
                        ]
                        proposed = bench.reciprocal(gated, use_appearance=True)
                        output, accepted, rejected = bench.apply_union_edges(
                            predictions, proposed, True,
                            lambda edge: (edge["cosine_distance"], edge["gap"], edge["earlier"], edge["later"]),
                        )
                        points.append(("com3d_reciprocal_guard", "appearance_cosine", threshold, output, accepted, rejected))

                        proposed = bench.hungarian_with_unmatched(gated, unmatched_cost=1.0)
                        output, accepted, rejected = bench.apply_union_edges(
                            predictions, proposed, True,
                            lambda edge: (edge["controlled_cost"], edge["gap"], edge["earlier"], edge["later"]),
                        )
                        points.append(("geometry_reid_hungarian", "appearance_cosine", threshold, output, accepted, rejected))

                    for threshold in AFLINK_COST_GRID:
                        proposed = aflink_assignment(af_candidates, threshold)
                        output, accepted, rejected = bench.apply_aflink_mapping(predictions, proposed)
                        points.append(("aflink_official", "aflink_cost", threshold, output, accepted, rejected))

                    for method, parameter, threshold, output, accepted, rejected in points:
                        method_key = f"{method}__{parameter}_{threshold:.3f}"
                        duplicates = bench.duplicate_frame_identity_count(output)
                        geometry_preserved = bench.geometry_multiset(output) == bench.geometry_multiset(predictions)
                        valid = duplicates == 0 and geometry_preserved
                        if not valid:
                            invalid_outputs.append({
                                **context, "method": method, "parameter": parameter,
                                "threshold": threshold, "duplicate_count": duplicates,
                                "geometry_preserved": geometry_preserved,
                            })
                        audited, counts = bench.edge_audit(accepted, labels)
                        records.append({
                            **context, "method": method_key,
                            "metric_data": mmot.COMMON.metric_data(gt, output),
                            "valid_output": valid,
                            "accepted_correct": counts["correct"],
                            "accepted_false": counts["false"],
                            "accepted_unknown": counts["unknown"],
                            "eligible_source_tracklets": len(eligible_sources),
                        })
                        link_records.append({
                            **context, "method": method, "parameter": parameter,
                            "threshold": threshold,
                            "accepted_correct": counts["correct"],
                            "accepted_false": counts["false"],
                            "accepted_unknown": counts["unknown"],
                            "eligible_source_tracklets": len(eligible_sources),
                            "valid_output": valid,
                        })
                        for edge in audited:
                            accepted_rows.append({
                                **context, "method": method, "parameter": parameter,
                                "threshold": threshold, **edge,
                            })

    methods = sorted({row["method"] for row in records})
    sequence_rows, aggregate_rows = bench.summarize_records(
        mmot.COMMON, records, list(family_roots), args.trackers, methods
    )
    decoded = {}
    for method in ("com3d_reciprocal_guard", "geometry_reid_hungarian"):
        for threshold in APPEARANCE_GRID:
            decoded[f"{method}__appearance_cosine_{threshold:.3f}"] = (method, "appearance_cosine", threshold)
    for threshold in AFLINK_COST_GRID:
        decoded[f"aflink_official__aflink_cost_{threshold:.3f}"] = ("aflink_official", "aflink_cost", threshold)
    for row in sequence_rows + aggregate_rows:
        method, parameter, threshold = decoded[row["method"]]
        row.update({"method": method, "parameter": parameter, "threshold": threshold})

    link_summary = []
    for scope in ("data28", "data30", "all12"):
        for tracker in args.trackers:
            for method, parameter, grid in (
                ("com3d_reciprocal_guard", "appearance_cosine", APPEARANCE_GRID),
                ("geometry_reid_hungarian", "appearance_cosine", APPEARANCE_GRID),
                ("aflink_official", "aflink_cost", AFLINK_COST_GRID),
            ):
                for threshold in grid:
                    selected = [
                        row for row in link_records
                        if row["tracker"] == tracker and row["method"] == method
                        and row["parameter"] == parameter and row["threshold"] == threshold
                        and (scope == "all12" or row["family"] == scope)
                    ]
                    if not selected:
                        continue
                    counts = Counter()
                    for row in selected:
                        counts.update({
                            "correct": row["accepted_correct"],
                            "false": row["accepted_false"],
                            "unknown": row["accepted_unknown"],
                            "eligible": row["eligible_source_tracklets"],
                        })
                    known = counts["correct"] + counts["false"]
                    link_summary.append({
                        "scope": scope, "tracker": tracker, "method": method,
                        "parameter": parameter, "threshold": threshold,
                        "valid_output": all(row["valid_output"] for row in selected),
                        "accepted_correct": counts["correct"],
                        "accepted_false": counts["false"],
                        "accepted_unknown": counts["unknown"],
                        "eligible_source_tracklets": counts["eligible"],
                        "accepted_link_error_rate": counts["false"] / known if known else None,
                        "accepted_link_precision": counts["correct"] / known if known else None,
                        "known_link_coverage": known / counts["eligible"] if counts["eligible"] else None,
                        "all_accepted_coverage": (known + counts["unknown"]) / counts["eligible"] if counts["eligible"] else None,
                    })

    write_csv(args.output_dir / "trajectory_error_coverage_per_sequence.csv", sequence_rows)
    write_csv(args.output_dir / "trajectory_error_coverage_aggregate.csv", aggregate_rows)
    write_csv(args.output_dir / "link_error_coverage.csv", link_summary)
    write_csv(args.output_dir / "accepted_links_by_curve_point.csv", accepted_rows)
    write_csv(args.output_dir / "aflink_score_runtime.csv", runtime_rows)
    manifest = {
        "status": "COMPLETE",
        "claim_scope": "Descriptive error-coverage audit on known MMOT sequences; not threshold selection or calibration.",
        "appearance_threshold_grid": list(APPEARANCE_GRID),
        "aflink_cost_threshold_grid": list(AFLINK_COST_GRID),
        "fixed_geometry_radius_pixels": bench.GEOMETRY_RADIUS,
        "fixed_maximum_gap_frames": bench.MAX_GAP,
        "hungarian_unmatched_cost": 1.0,
        "coverage_denominator": "Source tracklets with at least one temporally admissible non-overlapping successor within 30 frames, fixed across curve points.",
        "ground_truth_use": "Post-hoc edge correctness and trajectory evaluation only; no threshold is selected from these results.",
        "aflink": af_manifest,
        "invalid_outputs": invalid_outputs,
        "inputs": {
            "benchmark_script": {"path": str(args.benchmark_script), "sha256": sha256(args.benchmark_script)},
            "byte_oc_manifest": {"path": str(args.byte_oc_result_dir / 'manifest.json'), "sha256": sha256(args.byte_oc_result_dir / 'manifest.json')},
            "deepoc_manifest": {"path": str(args.deepoc_result_dir / 'manifest.json'), "sha256": sha256(args.deepoc_result_dir / 'manifest.json')},
        },
        "runtime_seconds": time.perf_counter() - started_all,
        "cuda": {"device": str(device), "name": torch.cuda.get_device_name(device) if device.type == "cuda" else None},
    }
    write_json(args.output_dir / "manifest.json", manifest)
    print(json.dumps({
        "status": manifest["status"], "runtime_seconds": manifest["runtime_seconds"],
        "invalid_outputs": len(invalid_outputs), "link_curve_rows": len(link_summary),
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
