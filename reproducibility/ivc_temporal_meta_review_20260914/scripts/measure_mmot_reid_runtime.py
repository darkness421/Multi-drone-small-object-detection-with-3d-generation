#!/usr/bin/env python3
"""Measure direct-crop MMOT ReID extraction on frozen tracker outputs.

This benchmark does not write or alter descriptors. It replays the exact
first/middle/last crop policy used by the temporal refiner and records runtime
per sequence/class/tracker instance so extraction and graph costs can be
reported separately.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import json
import sys
import time
from pathlib import Path

import numpy as np
import torch


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--benchmark-script", type=Path, required=True)
    parser.add_argument("--workspace", type=Path, required=True)
    parser.add_argument("--tracker-cache-dir", type=Path, required=True)
    parser.add_argument("--reid-checkpoint", type=Path, required=True)
    parser.add_argument(
        "--family-root", nargs=2, action="append", metavar=("NAME", "PATH"), required=True
    )
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--device", default="cuda:1")
    parser.add_argument("--batch-size", type=int, default=128)
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
    sys.path.insert(0, str(args.workspace / "third_party/trackeval_official"))
    sys.path.insert(0, str(args.workspace / "third_party/boxmot_official"))
    bench = load_module("runtime_benchmark", args.benchmark_script)
    mmot = bench.load_module(
        "runtime_mmot", args.workspace / "scripts/run_mmot_locked_temporal.py"
    )

    device = torch.device(args.device)
    if device.type == "cuda" and not torch.cuda.is_available():
        raise SystemExit("CUDA requested but unavailable")
    model, reid_manifest = mmot.REID.load_reid(args.reid_checkpoint, device)
    family_roots = {name: Path(path) for name, path in args.family_root}

    # Warm-up uses the real model shape but no benchmark sample.
    with torch.inference_mode():
        model(torch.zeros((args.batch_size, 3, 256, 128), device=device))
    bench.cuda_sync(device)

    rows: list[dict] = []
    total_started = time.perf_counter()
    for family, root in family_roots.items():
        for sequence_dir in sorted(path for path in root.iterdir() if path.is_dir()):
            frames, image_map, _, _ = mmot.load_sequence(sequence_dir)
            del frames
            for class_name in bench.CLASS_NAMES:
                for tracker in args.trackers:
                    prediction_path = (
                        args.tracker_cache_dir / "tracker_outputs" / family /
                        sequence_dir.name / class_name / f"{tracker}.jsonl.gz"
                    )
                    if not prediction_path.exists():
                        continue
                    predictions = bench.load_predictions(prediction_path)
                    _, audit = bench.extract_descriptors(
                        predictions, image_map, model, device, args.batch_size
                    )
                    rows.append({
                        "family": family,
                        "sequence": sequence_dir.name,
                        "class_name": class_name,
                        "tracker": tracker,
                        **audit,
                    })

    total_seconds = time.perf_counter() - total_started
    write_csv(args.output_dir / "reid_runtime_per_instance.csv", rows)
    summary = []
    for tracker in args.trackers:
        selected = [row for row in rows if row["tracker"] == tracker]
        summary.append({
            "tracker": tracker,
            "instance_count": len(selected),
            "sampled_crops": sum(int(row["sampled_crops"]) for row in selected),
            "descriptors": sum(int(row["descriptors"]) for row in selected),
            "rejected_invalid_crops": sum(
                int(row["rejected_invalid_crops"]) for row in selected
            ),
            "runtime_seconds_sum": sum(float(row["runtime_seconds"]) for row in selected),
            "runtime_seconds_median_instance": float(
                np.median([float(row["runtime_seconds"]) for row in selected])
            ),
        })
    write_csv(args.output_dir / "reid_runtime_summary.csv", summary)

    manifest = {
        "status": "COMPLETE",
        "purpose": "Runtime replay only; frozen tracker outputs and fixed crop policy.",
        "ground_truth_use": "None during crop selection or descriptor extraction.",
        "family_roots": {name: str(path) for name, path in family_roots.items()},
        "tracker_cache_dir": str(args.tracker_cache_dir.resolve()),
        "trackers": list(args.trackers),
        "instance_count": len(rows),
        "batch_size": args.batch_size,
        "device": str(device),
        "gpu": torch.cuda.get_device_name(device) if device.type == "cuda" else None,
        "torch": torch.__version__,
        "total_wall_seconds": total_seconds,
        "reid_checkpoint": str(args.reid_checkpoint.resolve()),
        "reid_checkpoint_sha256": sha256(args.reid_checkpoint),
        "reid_checkpoint_metadata": reid_manifest,
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
        "total_wall_seconds": total_seconds,
        "summary": summary,
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
