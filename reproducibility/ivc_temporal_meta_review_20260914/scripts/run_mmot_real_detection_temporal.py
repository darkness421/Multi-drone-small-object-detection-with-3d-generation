#!/usr/bin/env python3
"""Evaluate frozen temporal refiners on cached official MMOT detections."""

from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import importlib.util
import json
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
import torch
from PIL import Image


METHODS = (
    "no_refinement",
    "geometry_greedy",
    "geometry_reid_hungarian",
    "aflink_official",
    "com3d_reciprocal_guard",
)


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
        for block in iter(lambda: handle.read(8 * 1024 * 1024), b""):
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


def load_detections(path: Path) -> dict[int, list[dict]]:
    output = defaultdict(list)
    with gzip.open(path, "rt", encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            output[int(row["frame"])].append({
                "x": float(row["x"]), "y": float(row["y"]),
                "w": float(row["w"]), "h": float(row["h"]),
                "conf": float(row["confidence"]),
                "class_id": int(row["class_id"]), "visibility": 1.0,
            })
    return output


def class_detections(detections: dict[int, list[dict]], class_id: int) -> dict[int, list[dict]]:
    return {
        frame: [row for row in rows if row["class_id"] == class_id]
        for frame, rows in detections.items()
        if any(row["class_id"] == class_id for row in rows)
    }


def detector_crop(image_rgb: np.ndarray, row: dict) -> torch.Tensor | None:
    height, width = image_rgb.shape[:2]
    x1 = max(0, int(round(row["x"])))
    y1 = max(0, int(round(row["y"])))
    x2 = min(width, int(round(row["x"] + row["w"])) + 1)
    y2 = min(height, int(round(row["y"] + row["h"])) + 1)
    if x2 <= x1 or y2 <= y1:
        return None
    crop = Image.fromarray(
        np.ascontiguousarray(image_rgb[y1:y2, x1:x2]), mode="RGB"
    ).resize((128, 256), Image.Resampling.BILINEAR)
    tensor = torch.from_numpy(np.asarray(crop, dtype=np.float32).copy()).permute(2, 0, 1)
    mean = torch.tensor([123.675, 116.28, 103.53])[:, None, None]
    std = torch.tensor([58.395, 57.12, 57.375])[:, None, None]
    return (tensor - mean) / std


def run_deepocsort(detections: dict, image_map: dict[int, Path], model, device: torch.device, batch_size: int) -> tuple[dict, int]:
    from boxmot.trackers.registry import create_tracker, get_tracker_config

    tracker = create_tracker(
        "deepocsort", tracker_config=get_tracker_config("deepocsort"),
        precomputed_reid=True, device=str(device), half=False, per_class=False,
    )
    predictions = defaultdict(list)
    rejected_invalid_boxes = 0
    for frame in range(1, max(image_map, default=0) + 1):
        rows = detections.get(frame, [])
        array = np.load(image_map[frame], mmap_mode="r")
        image_rgb = np.ascontiguousarray(array[:, :, [4, 2, 1]])
        image_bgr = np.ascontiguousarray(array[:, :, [1, 2, 4]])
        tensors = []
        valid_rows = []
        for row in rows:
            tensor = detector_crop(image_rgb, row)
            if tensor is None:
                rejected_invalid_boxes += 1
                continue
            tensors.append(tensor)
            valid_rows.append(row)
        if tensors:
            parts = []
            with torch.inference_mode():
                for begin in range(0, len(tensors), batch_size):
                    batch = torch.stack(tensors[begin:begin + batch_size]).to(device)
                    parts.append(model(batch).detach().float().cpu().numpy())
            embeddings = np.concatenate(parts)
            norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
            if not np.isfinite(embeddings).all() or np.any(norms <= 0):
                raise RuntimeError("non-finite detector-box ReID embedding")
            embeddings /= norms
        else:
            embeddings = np.empty((0, 128), dtype=np.float32)
        dets = np.asarray([
            [row["x"], row["y"], row["x"] + row["w"], row["y"] + row["h"], row["conf"], row["class_id"]]
            for row in valid_rows
        ], dtype=np.float32).reshape(-1, 6)
        outputs = tracker.update(dets, image_bgr, embeddings)
        for output in outputs:
            x1, y1, x2, y2, identity, confidence, class_id = output[:7]
            predictions[frame].append({
                "id": int(identity), "x": float(x1), "y": float(y1),
                "w": float(x2 - x1), "h": float(y2 - y1),
                "conf": float(confidence), "class_id": int(class_id),
                "visibility": 1.0,
            })
    return predictions, rejected_invalid_boxes


def direct_tracklet_descriptors(bench, predictions: dict, image_map: dict[int, Path], model, device: torch.device, batch_size: int) -> tuple[dict[int, np.ndarray], dict]:
    _, rows = bench.prediction_tracklets(predictions)
    work = []
    for identity, track_rows in sorted(rows.items()):
        ordered = track_rows
        if len(ordered) <= 3:
            selected = ordered
        else:
            selected = [ordered[0], ordered[len(ordered) // 2], ordered[-1]]
        for frame, row in selected:
            work.append((identity, frame, row))
    features = defaultdict(list)
    started = time.perf_counter()
    bench.cuda_sync(device)
    with torch.inference_mode():
        for begin in range(0, len(work), batch_size):
            batch_items = work[begin:begin + batch_size]
            tensors = []
            admitted = []
            for identity, frame, row in batch_items:
                array = np.load(image_map[frame], mmap_mode="r")
                image_rgb = np.ascontiguousarray(array[:, :, [4, 2, 1]])
                tensor = detector_crop(image_rgb, row)
                if tensor is not None:
                    tensors.append(tensor)
                    admitted.append(identity)
            if not tensors:
                continue
            output = model(torch.stack(tensors).to(device)).detach().float().cpu().numpy()
            norms = np.linalg.norm(output, axis=1, keepdims=True)
            if not np.isfinite(output).all() or np.any(norms <= 0):
                raise RuntimeError("non-finite direct tracklet ReID feature")
            output /= norms
            for identity, feature in zip(admitted, output):
                features[identity].append(feature)
    bench.cuda_sync(device)
    descriptors = {}
    for identity, values in features.items():
        value = np.mean(values, axis=0)
        norm = np.linalg.norm(value)
        if np.isfinite(value).all() and norm > 0:
            descriptors[identity] = (value / norm).astype(np.float32)
    return descriptors, {
        "tracklet_count": len(rows), "sampled_boxes": len(work),
        "descriptors": len(descriptors),
        "runtime_seconds": time.perf_counter() - started,
        "crop_admission": "tracker output box only; no GT matching or GT identity",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--benchmark-script", type=Path, required=True)
    parser.add_argument("--workspace", type=Path, required=True)
    parser.add_argument("--detection-dir", type=Path, required=True)
    parser.add_argument("--detector-manifest", type=Path, required=True)
    parser.add_argument("--reid-checkpoint", type=Path, required=True)
    parser.add_argument("--aflink-root", type=Path, required=True)
    parser.add_argument("--aflink-checkpoint", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--family-root", nargs=2, action="append", metavar=("NAME", "PATH"), required=True)
    parser.add_argument("--trackers", nargs="+", choices=("bytetrack", "ocsort", "deepocsort"), default=["bytetrack", "ocsort", "deepocsort"])
    parser.add_argument("--device", default="cuda:0")
    parser.add_argument("--batch-size", type=int, default=128)
    parser.add_argument("--aflink-batch-size", type=int, default=512)
    parser.add_argument("--max-sequences-per-family", type=int)
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    sys.path.insert(0, str(args.workspace / "third_party/trackeval_official"))
    sys.path.insert(0, str(args.workspace / "third_party/boxmot_official"))
    bench = load_module("real_detection_benchmark", args.benchmark_script)
    mmot = bench.load_module("real_detection_mmot", args.workspace / "scripts/run_mmot_locked_temporal.py")
    device = torch.device(args.device)
    if device.type == "cuda" and not torch.cuda.is_available():
        raise SystemExit("CUDA requested but unavailable")
    torch.manual_seed(0)
    np.random.seed(0)
    model, reid_manifest = mmot.REID.load_reid(args.reid_checkpoint, device)
    af_runtime, af_manifest = bench.load_aflink(args.aflink_root, args.aflink_checkpoint, device)
    with torch.inference_mode():
        model(torch.zeros((2, 3, 256, 128), device=device))
        af_runtime.model(
            torch.zeros((2, 1, 30, 5), device=device),
            torch.zeros((2, 1, 30, 5), device=device),
        )
    bench.cuda_sync(device)

    records = []
    runtime_rows = []
    descriptor_rows = []
    accepted_rows = []
    rejected_rows = []
    stage_rows = []
    invariant_failures = []
    started_all = time.perf_counter()
    family_names = [item[0] for item in args.family_root]
    for family, raw_root in args.family_root:
        sequences = sorted(path for path in Path(raw_root).iterdir() if path.is_dir())
        if args.max_sequences_per_family is not None:
            sequences = sequences[:args.max_sequences_per_family]
        for sequence_dir in sequences:
            frames, image_map, shape, summary = mmot.load_sequence(sequence_dir)
            detection_path = args.detection_dir / "detections" / family / f"{sequence_dir.name}.jsonl.gz"
            detections = load_detections(detection_path)
            for class_id, class_name in enumerate(bench.CLASS_NAMES):
                gt = mmot.class_frames(frames, class_id)
                predicted_detections = class_detections(detections, class_id)
                detection_count = sum(len(values) for values in predicted_detections.values())
                gt_count = sum(len(values) for values in gt.values())
                for tracker in args.trackers:
                    context = {
                        "family": family, "sequence": sequence_dir.name,
                        "class_name": class_name, "tracker": tracker,
                    }
                    tracker_started = time.perf_counter()
                    if tracker in {"bytetrack", "ocsort"}:
                        predictions = mmot.COMMON.run_sequence(tracker, predicted_detections, shape)
                        invalid_detection_boxes = 0
                    else:
                        predictions, invalid_detection_boxes = run_deepocsort(
                            predicted_detections, image_map, model, device, args.batch_size
                        )
                    bench.cuda_sync(device)
                    tracker_seconds = time.perf_counter() - tracker_started
                    tracker_path = (
                        args.output_dir / "tracker_outputs" / family / sequence_dir.name /
                        class_name / f"{tracker}.jsonl.gz"
                    )
                    bench.save_predictions(tracker_path, context, predictions)
                    descriptors, descriptor_info = direct_tracklet_descriptors(
                        bench, predictions, image_map, model, device, args.batch_size
                    )
                    descriptor_path = (
                        args.output_dir / "descriptors" / family / sequence_dir.name /
                        class_name / f"{tracker}.npz"
                    )
                    descriptor_path.parent.mkdir(parents=True, exist_ok=True)
                    np.savez_compressed(
                        descriptor_path,
                        **{str(identity): value for identity, value in descriptors.items()},
                    )
                    descriptor_rows.append({
                        **context, **descriptor_info,
                        "path": str(descriptor_path), "sha256": sha256(descriptor_path),
                    })
                    labels = mmot.M3OT_GRAPH.tracklet_gt_labels(gt, predictions)
                    candidates, eligible_sources = bench.build_candidates(predictions, descriptors)
                    stage_rows.append({
                        **context, "GT_boxes": gt_count,
                        "detector_boxes": detection_count,
                        "tracker_output_boxes": sum(len(values) for values in predictions.values()),
                        "tracker_tracklets": len(bench.prediction_tracklets(predictions)[0]),
                        "descriptor_tracklets": len(descriptors),
                        "eligible_source_tracklets": len(eligible_sources),
                        "temporal_candidates": len(candidates),
                        "invalid_detector_boxes_rejected": invalid_detection_boxes,
                    })
                    for method in METHODS:
                        bench.cuda_sync(device)
                        method_started = time.perf_counter()
                        output, accepted, rejected, details = bench.method_output(
                            method, predictions, candidates, af_runtime, args.aflink_batch_size
                        )
                        bench.cuda_sync(device)
                        elapsed = time.perf_counter() - method_started
                        duplicates = bench.duplicate_frame_identity_count(output)
                        geometry_preserved = bench.geometry_multiset(output) == bench.geometry_multiset(predictions)
                        valid = duplicates == 0 and geometry_preserved
                        if not valid:
                            invariant_failures.append({
                                **context, "method": method,
                                "duplicate_count": duplicates,
                                "geometry_preserved": geometry_preserved,
                            })
                        audited, counts = bench.edge_audit(accepted, labels)
                        for edge in audited:
                            accepted_rows.append({**context, "method": method, **edge})
                        for edge in rejected:
                            rejected_rows.append({**context, "method": method, **edge})
                        records.append({
                            **context, "method": method,
                            "metric_data": mmot.COMMON.metric_data(gt, output),
                            "valid_output": valid,
                            "accepted_correct": counts["correct"],
                            "accepted_false": counts["false"],
                            "accepted_unknown": counts["unknown"],
                            "eligible_source_tracklets": len(eligible_sources),
                        })
                        runtime_rows.append({
                            **context, "method": method,
                            "tracker_runtime_seconds": tracker_seconds,
                            "refiner_runtime_seconds": elapsed,
                            "accepted_links": len(accepted),
                            "valid_output": valid, **details,
                        })

    sequence_rows, aggregate_rows = bench.summarize_records(
        mmot.COMMON, records, family_names, args.trackers, METHODS
    )
    link_counts = defaultdict(Counter)
    eligible_counts = defaultdict(int)
    for row in records:
        key = (row["family"], row["tracker"], row["method"])
        link_counts[key].update({
            "correct": row["accepted_correct"], "false": row["accepted_false"],
            "unknown": row["accepted_unknown"],
        })
        eligible_counts[key] += row["eligible_source_tracklets"]
    link_summary = []
    for key, counts in sorted(link_counts.items()):
        known = counts["correct"] + counts["false"]
        link_summary.append({
            "scope": key[0], "tracker": key[1], "method": key[2],
            "accepted_correct": counts["correct"], "accepted_false": counts["false"],
            "accepted_unknown": counts["unknown"],
            "accepted_link_precision": counts["correct"] / known if known else None,
            "eligible_source_tracklets": eligible_counts[key],
            "accepted_link_coverage": known / eligible_counts[key] if eligible_counts[key] else None,
        })

    results_dir = args.output_dir / "results"
    write_csv(results_dir / "detector_input_temporal_per_sequence.csv", sequence_rows)
    write_csv(results_dir / "detector_input_temporal_results.csv", aggregate_rows)
    write_csv(results_dir / "detector_input_link_summary.csv", link_summary)
    write_csv(results_dir / "accepted_links.csv", accepted_rows)
    write_csv(results_dir / "rejected_links.csv", rejected_rows)
    write_csv(results_dir / "stage_counts.csv", stage_rows)
    write_csv(results_dir / "runtime.csv", runtime_rows)
    write_csv(results_dir / "descriptor_runtime.csv", descriptor_rows)
    detector_manifest = json.loads(args.detector_manifest.read_text(encoding="utf-8"))
    manifest = {
        "status": "COMPLETE" if not invariant_failures else "COMPLETE_WITH_NA_OUTPUT_VARIANTS",
        "claim_scope": "End-to-end detector-input single-view MMOT temporal tracking on cached official YOLO11L-3ch detections; not cross-UAV association.",
        "detector_manifest": {
            "path": str(args.detector_manifest), "sha256": sha256(args.detector_manifest),
            "detector": detector_manifest["detector"],
            "checkpoint_sha256": detector_manifest["checkpoint"]["sha256"],
        },
        "upstream_trackers": args.trackers,
        "methods": list(METHODS),
        "fixed_thresholds": {
            "maximum_gap_frames": bench.MAX_GAP,
            "geometry_radius_pixels": bench.GEOMETRY_RADIUS,
            "appearance_cosine_distance": bench.APPEARANCE_DISTANCE,
        },
        "descriptor_crop_admission": "Direct tracker output boxes; no GT detection, crop matching, class, or identity enters tracker/refiner decisions.",
        "ground_truth_use": "Metrics and post-hoc accepted-link audit only.",
        "aabb_policy": "Axis-aligned envelope of each official detector OBB; linking never creates/interpolates boxes.",
        "reid": reid_manifest,
        "aflink": af_manifest,
        "invariant_failures": invariant_failures,
        "invalid_output_policy": "Sequence and aggregate metrics are N/A if a refiner creates duplicate same-frame identities or changes the box/score/class multiset.",
        "runtime_seconds": time.perf_counter() - started_all,
        "script_sha256": sha256(Path(__file__)),
        "command": " ".join(sys.argv),
        "outputs": {},
    }
    for path in sorted(results_dir.glob("*")):
        manifest["outputs"][path.name] = {"path": str(path), "sha256": sha256(path)}
    write_json(args.output_dir / "manifest.json", manifest)
    print(json.dumps({
        "status": manifest["status"], "runtime_seconds": manifest["runtime_seconds"],
        "class_tracker_instances": len(stage_rows),
        "invariant_failures": len(invariant_failures),
        "results": str(results_dir / "detector_input_temporal_results.csv"),
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
