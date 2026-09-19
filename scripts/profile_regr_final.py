#!/usr/bin/env python3
"""Profile the frozen final REGR graph phases on immutable MMOT caches."""

from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import json
import statistics
import sys
import time
import tracemalloc
from pathlib import Path


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


def write_csv(path: Path, rows: list[dict]) -> None:
    fields = sorted({key for row in rows for key in row})
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def median_ms(call, repeats: int) -> float:
    call()
    values = []
    for _ in range(repeats):
        started = time.perf_counter_ns()
        call()
        values.append((time.perf_counter_ns() - started) / 1e6)
    return statistics.median(values)


def output_signature(predictions: dict[int, list[dict]]) -> tuple:
    return tuple(sorted(
        (int(frame), int(row["id"]))
        for frame, rows in predictions.items()
        for row in rows
    ))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--baseline-script", type=Path, required=True)
    parser.add_argument("--core", type=Path, required=True)
    parser.add_argument("--cache-root", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--repeats", type=int, default=3)
    args = parser.parse_args()
    if args.output_dir.exists() and any(args.output_dir.iterdir()):
        raise SystemExit(f"refusing to overwrite non-empty output directory: {args.output_dir}")
    args.output_dir.mkdir(parents=True, exist_ok=True)
    baseline = load_module("regr_final_profile_baseline", args.baseline_script)
    core = load_module("regr_final_profile_core", args.core)
    prediction_root = args.cache_root / "tracker_outputs"
    descriptor_root = args.cache_root / "descriptors"
    rows = []
    paths = sorted(prediction_root.glob("*/*/*/*.jsonl.gz"))
    started_all = time.perf_counter()

    for index, prediction_path in enumerate(paths, start=1):
        relative = prediction_path.relative_to(prediction_root)
        family, sequence, class_name, tracker_file = relative.parts
        tracker = tracker_file.removesuffix(".jsonl.gz")
        descriptor_path = descriptor_root / family / sequence / class_name / f"{tracker}.npz"
        if not descriptor_path.is_file():
            raise FileNotFoundError(descriptor_path)
        if index % 100 == 0 or index == len(paths):
            print(f"[{index}/{len(paths)}] {family}/{sequence}/{class_name}/{tracker}", flush=True)
        predictions = baseline.load_predictions(prediction_path)
        descriptors = baseline.load_descriptors(descriptor_path)

        candidate_call = lambda: baseline.build_candidates(predictions, descriptors)[0]
        candidate_ms = median_ms(candidate_call, args.repeats)
        candidates = candidate_call()
        gate_call = lambda: core.fixed_gated(candidates)
        gate_ms = median_ms(gate_call, args.repeats)
        gated = gate_call()

        def motion_call():
            edges = [dict(edge) for edge in gated]
            core.add_candidate_motion_features(edges, predictions, 3, "object_scale")
            for edge in edges:
                edge["motion_informative"] = bool(float(edge["motion_confidence"]) >= 0.50)
            return edges

        motion_ms = median_ms(motion_call, args.repeats)
        motion_edges = motion_call()

        filter_call = lambda: core._conditional_motion_filter(motion_edges, 0.50, 1.0)
        filter_ms = median_ms(filter_call, args.repeats)
        admissible, activation = filter_call()
        temporal_key = core._temporal_key(gated, 0.05, 0.005)
        ranking_call = lambda: sorted(admissible, key=temporal_key)
        ranking_ms = median_ms(ranking_call, args.repeats)
        ranking_call()
        merge_call = lambda: baseline.apply_union_edges(
            predictions, admissible, True, temporal_key
        )
        merge_ms = median_ms(merge_call, args.repeats)
        output, accepted, rejected = merge_call()

        exact_proposed, exact_key, _ = core.select("regr_final", predictions, candidates)
        exact_output, _, _ = baseline.apply_union_edges(
            predictions, exact_proposed, True, exact_key
        )
        exact_match = output_signature(output) == output_signature(exact_output)
        tracemalloc.start()
        selected, selected_key, _ = core.select("regr_final", predictions, candidates)
        baseline.apply_union_edges(predictions, selected, True, selected_key)
        _, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        total_ms = candidate_ms + gate_ms + motion_ms + filter_ms + ranking_ms + merge_ms
        rows.append({
            "family": family,
            "sequence": sequence,
            "class_name": class_name,
            "tracker": tracker,
            "method": "regr_final",
            "candidate_count": len(candidates),
            "gated_edge_count": len(gated),
            "admissible_edge_count": len(admissible),
            "accepted_links": len(accepted),
            "component_rejections": len(rejected),
            "guard_active": activation["guard_active"],
            "candidate_build_ms": candidate_ms,
            "fixed_gate_ms": gate_ms,
            "motion_confidence_ms": motion_ms,
            "conditional_filter_ms": filter_ms,
            "ranking_ms": ranking_ms,
            "component_merge_ms": merge_ms,
            "graph_total_ms": total_ms,
            "select_and_merge_peak_bytes": peak,
            "exact_output_match": exact_match,
            "repeats": args.repeats,
        })

    write_csv(args.output_dir / "phase_runtime_per_instance.csv", rows)
    summaries = []
    for tracker in sorted({row["tracker"] for row in rows}):
        values = [row for row in rows if row["tracker"] == tracker]
        summaries.append({
            "tracker": tracker,
            "method": "regr_final",
            "class_instances": len(values),
            "all_exact_output_match": all(row["exact_output_match"] for row in values),
            **{
                f"sum_{field}": sum(float(row[field]) for row in values)
                for field in (
                    "candidate_build_ms", "fixed_gate_ms", "motion_confidence_ms",
                    "conditional_filter_ms", "ranking_ms", "component_merge_ms",
                    "graph_total_ms",
                )
            },
            "peak_select_and_merge_bytes_max": max(
                int(row["select_and_merge_peak_bytes"]) for row in values
            ),
        })
    write_csv(args.output_dir / "phase_runtime_summary.csv", summaries)
    manifest = {
        "status": "COMPLETE" if all(row["exact_output_match"] for row in rows) else "FAILED_EQUIVALENCE",
        "scope": "MMOT oracle-cache CPU graph-stage profiling; descriptor extraction excluded",
        "warmup_calls": 1,
        "timed_repeats": args.repeats,
        "timer": "time.perf_counter_ns",
        "memory": "tracemalloc peak for exact final selector plus component merge",
        "inputs": {
            str(args.baseline_script): sha256(args.baseline_script),
            str(args.core): sha256(args.core),
            "cache_root": str(args.cache_root),
        },
        "runtime_seconds": time.perf_counter() - started_all,
        "command": " ".join(sys.argv),
    }
    (args.output_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(manifest, indent=2, sort_keys=True))
    return 0 if manifest["status"] == "COMPLETE" else 2


if __name__ == "__main__":
    raise SystemExit(main())
