#!/usr/bin/env python3
"""Measure CoM3D-ACE candidate construction and graph decision cost.

Frozen tracker outputs and cached descriptors are loaded before each timed
region. The benchmark therefore reports post-tracking graph computation, not
disk I/O, upstream tracking, or ReID extraction.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import json
import resource
import sys
import time
from pathlib import Path

import numpy as np


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--benchmark-script", type=Path, required=True)
    parser.add_argument("--tracker-cache-dir", type=Path, required=True)
    parser.add_argument("--descriptor-cache-dir", type=Path, required=True)
    parser.add_argument(
        "--family-root", nargs=2, action="append", metavar=("NAME", "PATH"), required=True
    )
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument(
        "--trackers", nargs="+", choices=("bytetrack", "ocsort", "deepocsort"),
        default=("bytetrack", "ocsort", "deepocsort"),
    )
    return parser.parse_args()


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load module from {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = sorted({key for row in rows for key in row})
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    bench = load_module("graph_runtime_benchmark", args.benchmark_script)
    family_roots = {name: Path(path) for name, path in args.family_root}
    rows: list[dict] = []
    wall_started = time.perf_counter()

    for family, root in family_roots.items():
        for sequence_dir in sorted(path for path in root.iterdir() if path.is_dir()):
            for class_name in bench.CLASS_NAMES:
                for tracker in args.trackers:
                    prediction_path = (
                        args.tracker_cache_dir / "tracker_outputs" / family /
                        sequence_dir.name / class_name / f"{tracker}.jsonl.gz"
                    )
                    descriptor_path = (
                        args.descriptor_cache_dir / "descriptors" / family /
                        sequence_dir.name / class_name / f"{tracker}.npz"
                    )
                    if not prediction_path.exists() or not descriptor_path.exists():
                        continue
                    predictions = bench.load_predictions(prediction_path)
                    descriptors = bench.load_descriptors(descriptor_path)

                    started = time.perf_counter()
                    candidates, eligible_sources = bench.build_candidates(predictions, descriptors)
                    candidate_seconds = time.perf_counter() - started

                    started = time.perf_counter()
                    output, accepted, rejected, details = bench.method_output(
                        "com3d_reciprocal_guard", predictions, candidates, None, 0
                    )
                    decision_seconds = time.perf_counter() - started
                    duplicates = bench.duplicate_frame_identity_count(output)
                    preserved = bench.geometry_multiset(predictions) == bench.geometry_multiset(output)
                    if duplicates or not preserved:
                        raise RuntimeError(
                            f"Output invariant failed for {family}/{sequence_dir.name}/{class_name}/{tracker}"
                        )
                    rows.append({
                        "family": family,
                        "sequence": sequence_dir.name,
                        "class_name": class_name,
                        "tracker": tracker,
                        "tracklets": len(bench.prediction_tracklets(predictions)[0]),
                        "candidate_edges": len(candidates),
                        "eligible_source_tracklets": len(eligible_sources),
                        "gated_edges": details.get("candidate_edges", 0),
                        "proposed_edges": details.get("proposed_edges", 0),
                        "accepted_links": len(accepted),
                        "rejected_component_links": len(rejected),
                        "candidate_seconds": candidate_seconds,
                        "decision_seconds": decision_seconds,
                        "graph_seconds": candidate_seconds + decision_seconds,
                    })

    wall_seconds = time.perf_counter() - wall_started
    write_csv(args.output_dir / "graph_runtime_per_instance.csv", rows)
    summary = []
    for tracker in args.trackers:
        selected = [row for row in rows if row["tracker"] == tracker]
        graph_times = np.asarray([row["graph_seconds"] for row in selected], dtype=float)
        summary.append({
            "tracker": tracker,
            "instance_count": len(selected),
            "tracklets": sum(row["tracklets"] for row in selected),
            "candidate_edges": sum(row["candidate_edges"] for row in selected),
            "gated_edges": sum(row["gated_edges"] for row in selected),
            "accepted_links": sum(row["accepted_links"] for row in selected),
            "candidate_seconds_sum": sum(row["candidate_seconds"] for row in selected),
            "decision_seconds_sum": sum(row["decision_seconds"] for row in selected),
            "graph_seconds_sum": float(graph_times.sum()),
            "graph_seconds_median_instance": float(np.median(graph_times)),
            "graph_seconds_p95_instance": float(np.quantile(graph_times, 0.95)),
        })
    write_csv(args.output_dir / "graph_runtime_summary.csv", summary)
    manifest = {
        "status": "COMPLETE",
        "timing_scope": "In-memory candidate construction plus CoM3D-ACE reciprocal/union decision.",
        "excluded": ["disk I/O", "upstream tracking", "ReID extraction", "metric evaluation"],
        "ground_truth_use": "None.",
        "family_roots": {name: str(path) for name, path in family_roots.items()},
        "tracker_cache_dir": str(args.tracker_cache_dir.resolve()),
        "descriptor_cache_dir": str(args.descriptor_cache_dir.resolve()),
        "trackers": list(args.trackers),
        "instance_count": len(rows),
        "wall_seconds_including_cache_reads": wall_seconds,
        "maximum_resident_set_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        "benchmark_script": str(args.benchmark_script.resolve()),
        "benchmark_script_sha256": sha256(args.benchmark_script),
        "script_sha256": sha256(Path(__file__)),
        "command": " ".join(sys.argv),
    }
    (args.output_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps({
        "status": "COMPLETE",
        "instance_count": len(rows),
        "wall_seconds": wall_seconds,
        "summary": summary,
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
