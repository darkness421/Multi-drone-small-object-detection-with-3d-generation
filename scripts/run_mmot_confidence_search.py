#!/usr/bin/env python3
"""Evaluate confidence/competition variants on shared MMOT tracker inputs."""

from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import json
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
import torch


CLASS_NAMES = ("car", "bike", "pedestrian", "van", "truck", "bus", "tricycle", "awning-bike")


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
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = sorted({key for row in rows for key in row})
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")


def lazy_reid(mmot, checkpoint: Path, device: torch.device, state: dict):
    if "model" not in state:
        state["model"], state["manifest"] = mmot.REID.load_reid(checkpoint, device)
        state["model"].eval()
    return state["model"]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workspace", type=Path, required=True)
    parser.add_argument("--baseline-script", type=Path, required=True)
    parser.add_argument("--enhancement-core", type=Path, required=True)
    parser.add_argument("--reid-checkpoint", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--tracker-cache-dir", type=Path, required=True)
    parser.add_argument("--descriptor-cache-dir", type=Path, required=True)
    parser.add_argument("--family-root", nargs=2, action="append", metavar=("NAME", "PATH"), required=True)
    parser.add_argument("--trackers", nargs="+", choices=("bytetrack", "ocsort", "deepocsort"), default=["bytetrack", "ocsort"])
    parser.add_argument("--methods", nargs="+")
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--batch-size", type=int, default=64)
    parser.add_argument("--selection-mode", action="store_true")
    parser.add_argument(
        "--include-empty-gt-classes",
        action="store_true",
        help="Match the detector-input protocol by retaining classes with predictions but no GT.",
    )
    args = parser.parse_args()
    if args.output_dir.exists() and any(args.output_dir.iterdir()):
        raise SystemExit(f"refusing to overwrite non-empty output directory: {args.output_dir}")
    args.output_dir.mkdir(parents=True, exist_ok=True)
    args.tracker_cache_dir.mkdir(parents=True, exist_ok=True)
    args.descriptor_cache_dir.mkdir(parents=True, exist_ok=True)

    sys.path.insert(0, str(args.workspace / "third_party/trackeval_official"))
    sys.path.insert(0, str(args.workspace / "third_party/boxmot_official"))
    baseline = load_module("regr_enhancement_baseline", args.baseline_script)
    core = load_module("regr_enhancement_core", args.enhancement_core)
    mmot = load_module("regr_enhancement_mmot", args.workspace / "scripts/run_mmot_locked_temporal.py")
    methods = tuple(args.methods or core.METHODS)
    unknown = sorted(set(methods) - set(core.METHODS))
    if unknown:
        raise SystemExit(f"unknown methods: {unknown}")

    device = torch.device(args.device)
    if device.type == "cuda" and not torch.cuda.is_available():
        raise SystemExit("CUDA requested but unavailable")
    torch.manual_seed(0)
    np.random.seed(0)
    model_state = {}
    families = {name: Path(path) for name, path in args.family_root}
    records = []
    link_rows = []
    decision_rows = []
    runtime_rows = []
    descriptor_rows = []
    invariant_failures = []
    started_all = time.perf_counter()

    for family, root in families.items():
        for sequence_dir in sorted(path for path in root.iterdir() if path.is_dir()):
            print(f"{family}/{sequence_dir.name}", flush=True)
            frames, image_map, shape, _ = mmot.load_sequence(sequence_dir)
            for class_id, class_name in enumerate(CLASS_NAMES):
                gt = mmot.class_frames(frames, class_id)
                if not gt and not args.include_empty_gt_classes:
                    continue
                for tracker in args.trackers:
                    context = {
                        "family": family,
                        "sequence": sequence_dir.name,
                        "class_name": class_name,
                        "tracker": tracker,
                    }
                    relative = Path(family) / sequence_dir.name / class_name / tracker
                    prediction_path = args.tracker_cache_dir / "tracker_outputs" / relative.with_suffix(".jsonl.gz")
                    if prediction_path.is_file():
                        predictions = baseline.load_predictions(prediction_path)
                        tracker_status = "reused_immutable_cache"
                    else:
                        tracker_started = time.perf_counter()
                        if tracker in {"bytetrack", "ocsort"}:
                            predictions = mmot.COMMON.run_sequence(tracker, gt, shape)
                        else:
                            model = lazy_reid(mmot, args.reid_checkpoint, device, model_state)
                            predictions = baseline.corrected_deepocsort(
                                mmot, gt, image_map, model, device, args.batch_size
                            )
                        baseline.save_predictions(prediction_path, context, predictions)
                        tracker_status = f"generated_{time.perf_counter() - tracker_started:.6f}s"

                    descriptor_path = args.descriptor_cache_dir / "descriptors" / relative.with_suffix(".npz")
                    if descriptor_path.is_file():
                        descriptors = baseline.load_descriptors(descriptor_path)
                        descriptor_status = "reused_immutable_cache"
                    else:
                        model = lazy_reid(mmot, args.reid_checkpoint, device, model_state)
                        descriptors, descriptor_info = baseline.extract_descriptors(
                            predictions, image_map, model, device, args.batch_size
                        )
                        descriptor_path.parent.mkdir(parents=True, exist_ok=True)
                        np.savez_compressed(
                            descriptor_path,
                            **{str(identity): value for identity, value in descriptors.items()},
                        )
                        descriptor_status = "generated"
                        descriptor_rows.append({**context, **descriptor_info})

                    labels = mmot.M3OT_GRAPH.tracklet_gt_labels(gt, predictions)
                    candidates, _ = baseline.build_candidates(predictions, descriptors)
                    input_geometry = baseline.geometry_multiset(predictions)
                    for method in methods:
                        method_started = time.perf_counter()
                        proposed, sort_key, details = core.select(method, predictions, candidates)
                        candidate_decisions = details.pop("candidate_decisions", [])
                        if method == "no_refinement":
                            output, accepted, rejected = predictions, [], []
                        else:
                            output, accepted, rejected = baseline.apply_union_edges(
                                predictions, proposed, True, sort_key
                            )
                        duplicates = baseline.duplicate_frame_identity_count(output)
                        geometry_preserved = input_geometry == baseline.geometry_multiset(output)
                        valid = duplicates == 0 and geometry_preserved
                        if not valid:
                            invariant_failures.append({
                                **context,
                                "method": method,
                                "duplicate_count": duplicates,
                                "geometry_preserved": geometry_preserved,
                            })
                        audited, counts = baseline.edge_audit(accepted, labels)
                        for edge in audited:
                            link_rows.append({**context, "method": method, **edge})
                        audited_candidates, _ = baseline.edge_audit(candidate_decisions, labels)
                        accepted_ids = {
                            (int(edge["earlier"]), int(edge["later"])) for edge in accepted
                        }
                        for edge in audited_candidates:
                            decision_rows.append({
                                **context,
                                "method": method,
                                "accepted_after_component_check": (
                                    int(edge["earlier"]), int(edge["later"])
                                ) in accepted_ids,
                                **edge,
                            })
                        records.append({
                            **context,
                            "method": method,
                            "metric_data": mmot.COMMON.metric_data(gt, output),
                            "valid_output": valid,
                            "accepted_correct": counts["correct"],
                            "accepted_false": counts["false"],
                            "accepted_unknown": counts["unknown"],
                            "eligible_source_tracklets": len({edge["earlier"] for edge in candidates}),
                        })
                        runtime_rows.append({
                            **context,
                            "method": method,
                            "runtime_seconds": time.perf_counter() - method_started,
                            "accepted_links": len(accepted),
                            "component_rejections": len(rejected),
                            "tracker_cache_status": tracker_status,
                            "descriptor_cache_status": descriptor_status,
                            **details,
                        })

    sequence_rows, aggregate_rows = baseline.summarize_records(
        mmot.COMMON,
        records,
        list(families),
        list(args.trackers),
        list(methods),
        include_pooled=False,
    )
    results = args.output_dir / "results"
    write_csv(results / "metrics_per_sequence.csv", sequence_rows)
    write_csv(results / "metrics_aggregate.csv", aggregate_rows)
    write_csv(results / "accepted_links.csv", link_rows)
    write_csv(results / "candidate_decisions.csv", decision_rows)
    write_csv(results / "runtime.csv", runtime_rows)
    write_csv(results / "descriptor_generation.csv", descriptor_rows)

    selection = None
    if args.selection_mode:
        equal = [
            row for row in aggregate_rows
            if row["scope"] == "all_sequences"
            and row["aggregation"] == "equal_sequence_mean_metrics_total_counts"
            and row["valid_output"]
        ]
        grouped = defaultdict(list)
        for row in equal:
            grouped[row["method"]].append(row)
        summary = []
        for method, values in sorted(grouped.items()):
            summary.append({
                "method": method,
                "tracker_count": len(values),
                "mean_IDF1": float(np.mean([float(row["IDF1"]) for row in values])),
                "mean_HOTA": float(np.mean([float(row["HOTA"]) for row in values])),
                "mean_AssA": float(np.mean([float(row["AssA"]) for row in values])),
                "total_IDSW": int(sum(int(row["IDSW"]) for row in values)),
                "tracker_IDF1": json.dumps({row["tracker"]: row["IDF1"] for row in values}, sort_keys=True),
            })
        lookup = {row["method"]: row for row in summary}
        candidates = [row for row in summary if row["method"] in core.ENHANCEMENTS]
        candidates.sort(key=lambda row: (-row["mean_IDF1"], row["total_IDSW"], row["method"]))
        winner = candidates[0]
        winner["delta_vs_regr_v1_pp"] = winner["mean_IDF1"] - lookup["regr_v1"]["mean_IDF1"]
        winner["delta_vs_greedy_pp"] = winner["mean_IDF1"] - lookup["geometry_reid_greedy_guard"]["mean_IDF1"]
        winner["proceed_to_frozen_evaluation"] = (
            winner["delta_vs_regr_v1_pp"] > 0.0 and winner["delta_vs_greedy_pp"] > 0.0
        )
        selection = {
            "selected_method": winner["method"],
            "selection_rule": "highest equal-sequence mean IDF1 across ByteTrack and OC-SORT; tie by lower total IDSW then method name",
            "development_only": True,
            "winner": winner,
            "all_methods": summary,
        }
        write_csv(results / "development_method_summary.csv", summary)
        write_json(results / "selected_method.json", selection)

    manifest = {
        "status": "COMPLETE" if not invariant_failures else "FAILED_INVARIANTS",
        "claim_scope": "MMOT oracle-AABB post-linking diagnostic",
        "ground_truth_use": "oracle tracker inputs, metrics, and post-hoc link labels only; no GT in ReID crop admission or edge selection",
        "families": {name: str(path) for name, path in families.items()},
        "trackers": list(args.trackers),
        "methods": list(methods),
        "selection_mode": args.selection_mode,
        "include_empty_gt_classes": args.include_empty_gt_classes,
        "selection": selection,
        "fixed_parameters": {
            "max_gap_frames": 30,
            "geometry_radius_pixels": 55.0,
            "appearance_cosine_distance": 0.30,
            "bidirectional_appearance_margin": 0.02,
        },
        "inputs": {
            str(path): sha256(path)
            for path in (args.baseline_script, args.enhancement_core, args.reid_checkpoint)
        },
        "invariant_failures": invariant_failures,
        "runtime_seconds": time.perf_counter() - started_all,
        "environment": {
            "python": sys.version,
            "torch": torch.__version__,
            "device": str(device),
            "cuda_available": torch.cuda.is_available(),
        },
    }
    write_json(args.output_dir / "manifest.json", manifest)
    print(json.dumps({
        "status": manifest["status"],
        "runtime_seconds": manifest["runtime_seconds"],
        "selection": selection,
    }, indent=2))
    return 0 if not invariant_failures else 2


if __name__ == "__main__":
    raise SystemExit(main())
