#!/usr/bin/env python3
"""Evaluate confidence/competition variants on immutable M3OT caches."""

from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import importlib.util
import json
import statistics
import sys
import time
import tracemalloc
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
import torch


TRACKERS = ("bytetrack", "ocsort")


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


def load_predictions(path: Path) -> dict[int, list[dict]]:
    output: dict[int, list[dict]] = defaultdict(list)
    with gzip.open(path, "rt", encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            frame = int(row.pop("frame"))
            output[frame].append(row)
    return dict(output)


def load_descriptors(path: Path) -> dict[int, np.ndarray]:
    with np.load(path) as payload:
        return {int(key): payload[key] for key in payload.files}


def write_csv(path: Path, rows: list[dict]) -> None:
    fields = sorted({key for row in rows for key in row})
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def relation(edge: dict, labels: dict[int, dict]) -> str:
    left = labels.get(int(edge["earlier"]))
    right = labels.get(int(edge["later"]))
    if left is None or right is None:
        return "unknown"
    return "correct" if left["majority_gt_identity"] == right["majority_gt_identity"] else "false"


def tracklet_areas(predictions: dict[int, list[dict]]) -> dict[int, float]:
    values: dict[int, list[float]] = defaultdict(list)
    for rows in predictions.values():
        for row in rows:
            values[int(row["id"])].append(float(row["w"]) * float(row["h"]))
    return {identity: float(np.median(areas)) for identity, areas in values.items()}


def area_bin(area: float) -> str:
    if area < 32.0 ** 2:
        return "tiny_lt_32sq"
    if area < 96.0 ** 2:
        return "small_32sq_to_96sq"
    return "larger_ge_96sq"


def gap_bin(gap: int) -> str:
    if gap <= 5:
        return "gap_1_5"
    if gap <= 15:
        return "gap_6_15"
    return "gap_16_30"


def aggregate(rows: list[dict]) -> list[dict]:
    groups: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for row in rows:
        groups[(row["tracker"], row["method"])].append(row)
    output = []
    for (tracker, method), values in sorted(groups.items()):
        output.append({
            "tracker": tracker,
            "method": method,
            "sequence_count": len(values),
            "scene_group_count": len({row["scene_group"] for row in values}),
            "aggregation": "equal_stream_mean_metrics_total_counts",
            **{
                metric: float(np.mean([float(row[metric]) for row in values]))
                for metric in ("HOTA", "AssA", "DetA", "IDF1", "MOTA")
            },
            "IDSW": int(sum(int(row["IDSW"]) for row in values)),
            "accepted_correct": int(sum(int(row["accepted_correct"]) for row in values)),
            "accepted_false": int(sum(int(row["accepted_false"]) for row in values)),
            "accepted_unknown": int(sum(int(row["accepted_unknown"]) for row in values)),
        })
    return output


def scene_aggregate(rows: list[dict]) -> tuple[list[dict], list[dict]]:
    groups: dict[tuple[str, str, str], list[dict]] = defaultdict(list)
    for row in rows:
        groups[(row["scene_group"], row["tracker"], row["method"])].append(row)
    scene_rows = []
    for (scene, tracker, method), values in sorted(groups.items()):
        scene_rows.append({
            "scene_group": scene,
            "tracker": tracker,
            "method": method,
            "stream_count": len(values),
            **{
                metric: float(np.mean([float(row[metric]) for row in values]))
                for metric in ("HOTA", "AssA", "DetA", "IDF1", "MOTA")
            },
            "IDSW": int(sum(int(row["IDSW"]) for row in values)),
        })
    summary_groups: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for row in scene_rows:
        summary_groups[(row["tracker"], row["method"])].append(row)
    summaries = []
    for (tracker, method), values in sorted(summary_groups.items()):
        summaries.append({
            "tracker": tracker,
            "method": method,
            "scene_group_count": len(values),
            "aggregation": "equal_scene_group_mean_of_stream_means",
            **{
                metric: float(np.mean([float(row[metric]) for row in values]))
                for metric in ("HOTA", "AssA", "DetA", "IDF1", "MOTA")
            },
            "IDSW": int(sum(int(row["IDSW"]) for row in values)),
        })
    return scene_rows, summaries


def timed(call, repeats: int = 3):
    call()
    values = []
    for _ in range(repeats):
        started = time.perf_counter_ns()
        call()
        values.append((time.perf_counter_ns() - started) / 1e6)
    tracemalloc.start()
    call()
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    return statistics.median(values), peak


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workspace", type=Path, required=True)
    parser.add_argument("--diagnostic-script", type=Path, required=True)
    parser.add_argument("--baseline-script", type=Path, required=True)
    parser.add_argument("--extended-core", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--cache-root", type=Path, required=True)
    parser.add_argument("--cache-split", required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--aflink-root", type=Path, required=True)
    parser.add_argument("--aflink-checkpoint", type=Path, required=True)
    parser.add_argument("--aflink-batch-size", type=int, default=512)
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--methods", nargs="+")
    args = parser.parse_args()
    if args.output_dir.exists() and any(args.output_dir.iterdir()):
        raise SystemExit(f"refusing to overwrite non-empty output directory: {args.output_dir}")
    args.output_dir.mkdir(parents=True, exist_ok=True)
    sys.path.insert(0, str(args.workspace / "third_party/trackeval_official"))
    sys.path.insert(0, str(args.workspace / "third_party/boxmot_official"))
    module = load_module("regr_extended_m3ot_module", args.workspace / "scripts/run_m3ot_ambiguity_aware.py")
    diagnostic = load_module("regr_extended_m3ot_diagnostic", args.diagnostic_script)
    baseline = load_module("regr_extended_m3ot_baseline", args.baseline_script)
    core = load_module("regr_extended_core", args.extended_core)
    device = torch.device(args.device)
    # AFLink is opt-in because its model inference is not part of the A/B
    # development search. Final comparison runs can request it explicitly.
    methods = tuple(args.methods or tuple(core.METHODS))
    unknown = sorted(set(methods) - (set(core.METHODS) | {"aflink_va"}))
    if unknown:
        raise SystemExit(f"unknown methods: {unknown}")
    if "aflink_va" in methods:
        af_runtime, af_manifest = baseline.load_aflink(
            args.aflink_root, args.aflink_checkpoint, device
        )
    else:
        af_runtime = None
        af_manifest = {"status": "not_requested"}
    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    root = Path(manifest["data_root"])
    rows = []
    links = []
    decision_rows = []
    runtime_rows = []
    input_hashes = {str(args.manifest): sha256(args.manifest)}
    started_all = time.perf_counter()
    for index, spec in enumerate(manifest["sequences"], start=1):
        sequence = spec["sequence_relative_path"]
        scene_group = str(spec.get("scene_group") or Path(sequence).name.replace("T", "").split("-")[-1])
        print(f"[{index}/{len(manifest['sequences'])}] {sequence}", flush=True)
        gt = module.COMMON.parse_gt(root / spec["gt_relative_path"])
        cache_sequence = sequence.replace("/", "__")
        for tracker in TRACKERS:
            prediction_path = args.cache_root / "tracker_outputs" / args.cache_split / cache_sequence / f"{tracker}.jsonl.gz"
            descriptor_path = args.cache_root / "descriptors" / args.cache_split / cache_sequence / f"{tracker}.npz"
            if not prediction_path.is_file() or not descriptor_path.is_file():
                raise FileNotFoundError(f"missing immutable cache for {sequence}/{tracker}")
            predictions = load_predictions(prediction_path)
            descriptors = load_descriptors(descriptor_path)
            labels = module.tracklet_gt_labels(gt, predictions)
            candidate_started = time.perf_counter_ns()
            candidates = diagnostic.complete_temporal_edges(predictions, descriptors)
            candidate_ms = (time.perf_counter_ns() - candidate_started) / 1e6
            areas = tracklet_areas(predictions)
            context = {
                "scene_group": scene_group,
                "sequence": sequence,
                "modality": spec.get("modality", spec.get("tags", [""])[0]),
                "drone": spec.get("drone", ""),
                "tracker": tracker,
            }
            if "aflink_va" in methods:
                af_started = time.perf_counter_ns()
                af_edges, af_details = baseline.aflink_select(
                    af_runtime, predictions, args.aflink_batch_size
                )
                af_select_ms = (time.perf_counter_ns() - af_started) / 1e6
            else:
                af_edges, af_details, af_select_ms = [], {}, 0.0
            for method in methods:
                candidate_decisions = []
                if method == "no_refinement":
                    output, accepted, rejected, details = predictions, [], [], {
                        "selection": "identity input",
                        "gated_edges": 0,
                        "proposed_edges": 0,
                    }
                    select_ms = 0.0
                    assignment_ms = 0.0
                    peak = 0
                elif method == "aflink_va":
                    select_ms = af_select_ms
                    assignment_call = lambda: baseline.apply_union_edges(
                        predictions,
                        af_edges,
                        True,
                        lambda edge: (
                            edge["aflink_cost"], edge["gap"],
                            edge["earlier"], edge["later"],
                        ),
                    )
                    assignment_ms, peak = timed(assignment_call)
                    output, accepted, rejected = assignment_call()
                    details = {"selection": "official AFLink assignments plus overlap-validity adapter", **af_details}
                else:
                    select_started = time.perf_counter_ns()
                    proposed, sort_key, details = core.select(method, predictions, candidates)
                    candidate_decisions = details.pop("candidate_decisions", [])
                    select_ms = (time.perf_counter_ns() - select_started) / 1e6
                    assignment_call = lambda: diagnostic.apply_edges(predictions, proposed, sort_key)
                    assignment_ms, peak = timed(assignment_call)
                    output, accepted, rejected = assignment_call()
                counts = Counter(relation(edge, labels) for edge in accepted)
                metrics = module.COMMON.evaluate(module.COMMON.metric_data(gt, output))
                rows.append({
                    **context,
                    "method": method,
                    **metrics,
                    "accepted_correct": counts["correct"],
                    "accepted_false": counts["false"],
                    "accepted_unknown": counts["unknown"],
                    "component_rejections": len(rejected),
                })
                runtime_rows.append({
                    **context,
                    "method": method,
                    "candidate_build_ms": candidate_ms,
                    "selection_ms": select_ms,
                    "assignment_ms_median": assignment_ms,
                    "solver_peak_bytes": peak,
                    "accepted_links": len(accepted),
                    "component_rejections": len(rejected),
                    **details,
                })
                for accepted_edge in accepted:
                    source_area = areas.get(int(accepted_edge["earlier"]), float("nan"))
                    destination_area = areas.get(int(accepted_edge["later"]), float("nan"))
                    link_area = min(source_area, destination_area)
                    links.append({
                        **context,
                        "method": method,
                        **accepted_edge,
                        "posthoc_gt_correctness": relation(accepted_edge, labels),
                        "source_median_area": source_area,
                        "destination_median_area": destination_area,
                        "link_area_bin": area_bin(link_area),
                        "gap_bin": gap_bin(int(accepted_edge["gap"])),
                        "motion_available": int(accepted_edge.get("motion_estimate_count", 0)) > 0,
                        "reciprocal_consensus": accepted_edge.get("reciprocal_consensus", "N/A"),
                        "guard_active_for_instance": details.get("guard_active", "N/A"),
                    })
                accepted_ids = {
                    (int(edge["earlier"]), int(edge["later"])) for edge in accepted
                }
                for candidate_edge in candidate_decisions:
                    decision_rows.append({
                        **context,
                        "method": method,
                        **candidate_edge,
                        "accepted_after_component_check": (
                            int(candidate_edge["earlier"]), int(candidate_edge["later"])
                        ) in accepted_ids,
                        "posthoc_gt_correctness": relation(candidate_edge, labels),
                    })
            input_hashes[str(prediction_path)] = sha256(prediction_path)
            input_hashes[str(descriptor_path)] = sha256(descriptor_path)

    scene_rows, scene_summary = scene_aggregate(rows)
    write_csv(args.output_dir / "metrics_per_sequence.csv", rows)
    write_csv(args.output_dir / "metrics_aggregate_stream.csv", aggregate(rows))
    write_csv(args.output_dir / "metrics_per_scene_group.csv", scene_rows)
    write_csv(args.output_dir / "metrics_aggregate_scene_group.csv", scene_summary)
    write_csv(args.output_dir / "accepted_links.csv", links)
    write_csv(args.output_dir / "candidate_decisions.csv", decision_rows)
    write_csv(args.output_dir / "runtime.csv", runtime_rows)
    output_manifest = {
        "status": "COMPLETE",
        "claim_scope": manifest["role"],
        "methods": list(methods),
        "sequence_count": len(manifest["sequences"]),
        "scene_group_count": len({str(item.get("scene_group", "")) for item in manifest["sequences"]}),
        "trackers": list(TRACKERS),
        "ground_truth_use": "oracle tracker input, metrics, and post-hoc link labels only; no GT in edge selection",
        "aggregation": {
            "stream": "equal stream mean",
            "scene": "equal scene-group mean after averaging camera/modality streams",
        },
        "aflink": af_manifest,
        "inputs": input_hashes,
        "extended_core_sha256": sha256(args.extended_core),
        "runtime_seconds": time.perf_counter() - started_all,
        "command": " ".join(sys.argv),
    }
    (args.output_dir / "manifest.json").write_text(
        json.dumps(output_manifest, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({"status": "COMPLETE", "rows": len(rows), "runtime_seconds": output_manifest["runtime_seconds"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
