#!/usr/bin/env python3
"""Audit the frozen CoM3D-ACE temporal protocol without altering old runs.

The audit regenerates only upstream tracker outputs and evaluator checks. It
does not run appearance refinement. New artifacts are written below the
explicit output directory so historical JSON files remain immutable.
"""

from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import importlib.util
import inspect
import json
import os
import platform
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import numpy as np
import torch
from PIL import Image, ImageDraw


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


def json_ready(value: Any) -> Any:
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, dict):
        return {str(key): json_ready(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [json_ready(item) for item in value]
    return str(value)


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(json_ready(payload), ensure_ascii=False, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )


def write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = sorted({key for row in rows for key in row})
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def metric_close(actual: dict, expected: dict, tolerance: float = 1e-10) -> tuple[bool, dict]:
    differences = {}
    passed = True
    for key in ("HOTA", "AssA", "DetA", "IDF1", "MOTA", "IDSW", "valid_gt_boxes", "predicted_boxes"):
        delta = float(actual[key]) - float(expected[key])
        differences[key] = delta
        if abs(delta) > tolerance:
            passed = False
    return passed, differences


def prediction_multiset(predictions: dict, include_identity: bool) -> Counter:
    values = Counter()
    for frame, rows in predictions.items():
        for row in rows:
            key = (
                int(frame),
                int(row["id"]) if include_identity else None,
                round(float(row["x"]), 8),
                round(float(row["y"]), 8),
                round(float(row["w"]), 8),
                round(float(row["h"]), 8),
                round(float(row.get("conf", 1.0)), 8),
                int(row.get("class_id", -1)),
            )
            values[key] += 1
    return values


def duplicate_frame_identity_count(predictions: dict) -> int:
    duplicates = 0
    for rows in predictions.values():
        counts = Counter(int(row["id"]) for row in rows)
        duplicates += sum(count - 1 for count in counts.values() if count > 1)
    return duplicates


def evaluator_sanity(mmot) -> dict:
    gt = {
        1: [
            {"id": 10, "x": 10.0, "y": 10.0, "w": 12.0, "h": 14.0, "conf": 1.0, "class_id": 0},
            {"id": 20, "x": 50.0, "y": 30.0, "w": 16.0, "h": 10.0, "conf": 1.0, "class_id": 0},
        ],
        2: [
            {"id": 10, "x": 12.0, "y": 11.0, "w": 12.0, "h": 14.0, "conf": 1.0, "class_id": 0},
            {"id": 20, "x": 51.0, "y": 31.0, "w": 16.0, "h": 10.0, "conf": 1.0, "class_id": 0},
        ],
    }
    exact = {frame: [dict(row) for row in rows] for frame, rows in gt.items()}
    permutation = {10: 901, 20: 407}
    permuted = {
        frame: [{**row, "id": permutation[row["id"]]} for row in rows]
        for frame, rows in gt.items()
    }
    exact_metrics = mmot.COMMON.evaluate(mmot.COMMON.metric_data(gt, exact))
    permuted_metrics = mmot.COMMON.evaluate(mmot.COMMON.metric_data(gt, permuted))

    fragmented = {
        1: [{"id": 1, "x": 10.0, "y": 10.0, "w": 10.0, "h": 10.0, "conf": 1.0, "class_id": 0}],
        2: [{"id": 1, "x": 11.0, "y": 10.0, "w": 10.0, "h": 10.0, "conf": 1.0, "class_id": 0}],
        4: [{"id": 2, "x": 12.0, "y": 10.0, "w": 10.0, "h": 10.0, "conf": 1.0, "class_id": 0}],
        5: [{"id": 2, "x": 13.0, "y": 10.0, "w": 10.0, "h": 10.0, "conf": 1.0, "class_id": 0}],
    }
    descriptors = {1: np.asarray([1.0, 0.0]), 2: np.asarray([1.0, 0.0])}
    labels_a = {
        1: {"majority_gt_identity": 77},
        2: {"majority_gt_identity": 77},
    }
    labels_b = {
        1: {"majority_gt_identity": 77},
        2: {"majority_gt_identity": 88},
    }
    refined_a, graph_a = mmot.M3OT_GRAPH.apply_graph(
        fragmented, descriptors, labels_a, "geometry_reid_reciprocal"
    )
    refined_b, graph_b = mmot.M3OT_GRAPH.apply_graph(
        fragmented, descriptors, labels_b, "geometry_reid_reciprocal"
    )
    perfect_keys = ("HOTA", "AssA", "DetA", "IDF1", "MOTA")
    exact_pass = all(abs(exact_metrics[key] - 100.0) < 1e-9 for key in perfect_keys) and exact_metrics["IDSW"] == 0
    permutation_pass = all(abs(permuted_metrics[key] - 100.0) < 1e-9 for key in perfect_keys) and permuted_metrics["IDSW"] == 0
    geometry_invariant = prediction_multiset(fragmented, False) == prediction_multiset(refined_a, False)
    identity_diagnostic_noncausal = prediction_multiset(refined_a, True) == prediction_multiset(refined_b, True)
    duplicate_free = duplicate_frame_identity_count(refined_a) == 0
    return {
        "status": "PASS" if all((exact_pass, permutation_pass, geometry_invariant, identity_diagnostic_noncausal, duplicate_free)) else "FAIL",
        "tests": {
            "perfect_prediction": {"passed": exact_pass, "metrics": exact_metrics},
            "global_one_to_one_id_permutation": {"passed": permutation_pass, "metrics": permuted_metrics},
            "id_only_refinement_preserves_frame_box_score_class_multiset": {"passed": geometry_invariant},
            "posthoc_gt_labels_do_not_change_selected_or_remapped_ids": {
                "passed": identity_diagnostic_noncausal,
                "labels_a_relation": graph_a["accepted_edges"][0].get("gt_relation") if graph_a["accepted_edges"] else None,
                "labels_b_relation": graph_b["accepted_edges"][0].get("gt_relation") if graph_b["accepted_edges"] else None,
            },
            "no_duplicate_identity_within_frame_after_merge": {
                "passed": duplicate_free,
                "duplicate_count": duplicate_frame_identity_count(refined_a),
            },
        },
    }


def tracker_config_audit(workspace: Path, mmot) -> dict:
    from boxmot.trackers.bbox.bytetrack import ByteTrack
    from boxmot.trackers.bbox.ocsort import OcSort
    from boxmot.trackers.registry import get_tracker_config

    bytetrack = ByteTrack()
    ocsort = OcSort()
    deep_config = get_tracker_config("deepocsort")

    def selected_attributes(obj, keys):
        return {
            key: json_ready(getattr(obj, key)) if hasattr(obj, key) else "constructor-only/not-retained"
            for key in keys
        }

    official_runner = workspace / "third_party/mmot_official/TrackByDetection/association/track_by_dets.py"
    return {
        "runtime_environment": {
            "python": sys.version,
            "platform": platform.platform(),
            "torch": torch.__version__,
            "cuda_available": torch.cuda.is_available(),
            "cuda_device_count": torch.cuda.device_count(),
            "numpy": np.__version__,
        },
        "implementation_commits": {
            "boxmot": os.popen(f"git -C {workspace / 'third_party/boxmot_official'} rev-parse HEAD").read().strip(),
            "trackeval": os.popen(f"git -C {workspace / 'third_party/trackeval_official'} rev-parse HEAD").read().strip(),
            "mmot_official": os.popen(f"git -C {workspace / 'third_party/mmot_official'} rev-parse HEAD").read().strip(),
        },
        "historical_adapter": {
            "source": str(workspace / "scripts/run_mmot_locked_temporal.py"),
            "source_sha256": sha256(workspace / "scripts/run_mmot_locked_temporal.py"),
            "common_source": inspect.getsourcefile(mmot.COMMON),
            "input": "official OBB GT converted to AABB envelope, score=1.0",
            "class_handling": "one independent tracker instance per official fine-grained class",
            "pre_tracker_filters": "invalid annotation/box only; no min-area, height, or aspect-ratio filter",
            "frame_mapping": "numeric NPY/TXT stem mapped directly to 1-based frame_id; no frames skipped",
            "sampling": "every released frame in each selected sequence",
        },
        "boxmot_bytetrack_defaults": selected_attributes(
            bytetrack,
            ("det_thresh", "max_age", "min_hits", "iou_threshold", "per_class", "min_conf", "track_thresh", "match_thresh", "track_buffer", "frame_rate", "buffer_size", "max_time_lost"),
        ),
        "boxmot_ocsort_defaults": selected_attributes(
            ocsort,
            ("det_thresh", "max_age", "min_hits", "iou_threshold", "per_class", "min_conf", "delta_t", "inertia", "use_byte", "Q_xy_scaling", "Q_s_scaling"),
        ),
        "boxmot_deepocsort_config": {
            "path": str(deep_config),
            "sha256": sha256(deep_config),
            "text": deep_config.read_text(encoding="utf-8"),
            "adapter_overrides": {"precomputed_reid": True, "half": False, "per_class": False},
        },
        "official_mmot_tracker_reference": {
            "source": str(official_runner),
            "source_sha256": sha256(official_runner),
            "note": "Not the implementation used for historical CoM3D results; official MMOT uses rotated trackers and detector outputs.",
            "parser_defaults": {
                "ByteTrack": {"track_thresh": 0.6, "track_buffer": 30, "match_thresh": 0.9, "min_box_area": 0},
                "OC-SORT": {"oc_track_thresh": 0.6, "max_age": 30, "min_hits": 3, "iou_threshold": 0.3, "use_byte": False},
                "shared_detector_confidence_from_paper": 0.1,
            },
        },
        "audit_finding": "Historical CoM3D association baselines use newer BoxMOT AABB defaults, not the official MMOT rotated-tracker implementation or its runtime thresholds.",
    }


def channel_audit(workspace: Path, data_cache: Path, output_dir: Path, mmot) -> dict:
    data_roots = {
        "data28": data_cache / "raw/MMOT/extracted/test",
        "data30": data_cache / "raw/MMOT/extracted/confirmatory_data30",
    }
    sample_rows = []
    evidence_dir = output_dir / "evidence/channel_audit"
    evidence_dir.mkdir(parents=True, exist_ok=True)
    selections = {
        "historical_first3_as_rgb": (0, 1, 2),
        "correct_rgb_band_5_3_2": (4, 2, 1),
        "official_bgr_band_2_3_5": (1, 2, 4),
    }
    visual_sources = []
    for family, root in data_roots.items():
        for sequence_dir in sorted(path for path in root.iterdir() if path.is_dir()):
            npy_files = sorted(sequence_dir.glob("*.npy"))
            chosen = sorted({0, len(npy_files) // 2, len(npy_files) - 1})
            for index in chosen:
                path = npy_files[index]
                array = np.load(path, mmap_mode="r")
                row = {
                    "family": family,
                    "sequence": sequence_dir.name,
                    "file": str(path),
                    "sha256": sha256(path),
                    "shape": list(array.shape),
                    "dtype": str(array.dtype),
                    "global_min": int(array.min()),
                    "global_max": int(array.max()),
                    "channels": [],
                }
                for channel in range(array.shape[2]):
                    values = np.asarray(array[:, :, channel])
                    row["channels"].append({
                        "zero_based_index": channel,
                        "one_based_band": channel + 1,
                        "min": int(values.min()),
                        "max": int(values.max()),
                        "mean": float(values.mean()),
                        "std": float(values.std()),
                        "p01": float(np.percentile(values, 1)),
                        "p99": float(np.percentile(values, 99)),
                    })
                sample_rows.append(row)
            visual_sources.append((family, sequence_dir, npy_files[0]))

    for family, sequence_dir, path in visual_sources[:2]:
        array = np.load(path)
        annotations = mmot.parse_frame_annotation(sequence_dir / f"{path.stem}.txt")
        first_box = annotations[0]
        x1 = max(0, int(np.floor(first_box["x"])))
        y1 = max(0, int(np.floor(first_box["y"])))
        x2 = min(array.shape[1], int(np.ceil(first_box["x"] + first_box["w"])) + 1)
        y2 = min(array.shape[0], int(np.ceil(first_box["y"] + first_box["h"])) + 1)
        panels = []
        for name, indices in selections.items():
            image = Image.fromarray(np.ascontiguousarray(array[:, :, indices]), mode="RGB")
            image.thumbnail((600, 450))
            canvas = Image.new("RGB", (620, 510), "white")
            canvas.paste(image, (10, 45))
            ImageDraw.Draw(canvas).text((10, 12), f"{name}: {indices}", fill="black")
            panels.append(canvas)
            crop = np.ascontiguousarray(array[y1:y2, x1:x2, indices])
            crop_image = Image.fromarray(crop, mode="RGB").resize((128, 256), Image.Resampling.BILINEAR)
            crop_image.save(evidence_dir / f"{family}_{sequence_dir.name}_{path.stem}_{name}_encoder_crop.png")
            normalized = (np.asarray(crop_image, dtype=np.float32).transpose(2, 0, 1) - np.asarray([123.675, 116.28, 103.53])[:, None, None]) / np.asarray([58.395, 57.12, 57.375])[:, None, None]
            np.save(evidence_dir / f"{family}_{sequence_dir.name}_{path.stem}_{name}_encoder_tensor.npy", normalized.astype(np.float32))
        montage = Image.new("RGB", (620 * len(panels), 510), "white")
        for index, panel in enumerate(panels):
            montage.paste(panel, (620 * index, 0))
        montage.save(evidence_dir / f"{family}_{sequence_dir.name}_{path.stem}_channel_permutations.png")

    official_loader = workspace / "third_party/mmot_official/mmot/mmot/datasets/pipelines/loading.py"
    official_memotr = workspace / "third_party/mmot_official/TrackByQuery/MeMOTR/data/seq_dataset.py"
    official_motip = workspace / "third_party/mmot_official/TrackByQuery/MOTIP/data/seq_dataset.py"
    historical = workspace / "scripts/run_mmot_locked_temporal.py"
    deepoc = workspace / "scripts/run_ivc_deepocsort_mmot.py"
    result = {
        "status": "FAIL_HISTORICAL_CHANNEL_SELECTION_REQUIRES_CORRECTED_RERUN",
        "raw_storage": {
            "axis_order": "HWC",
            "shape": [900, 1200, 8],
            "dtype": "uint8",
            "physical_channel_order": "spectral bands 1 through 8 in increasing center wavelength",
            "band_centers_nm": [422.5, 487.5, 550.0, 602.5, 660.0, 725.0, 785.0, 887.2],
            "evidence": "MMOT paper Appendix A.6 and official code's direct channel indexing",
        },
        "official_paper": {
            "arxiv": "2510.12565v1",
            "experimental_setting": "pseudo-RGB selects bands 5, 3, and 2",
            "appendix_a6": "band 5=red, band 3=green, band 2=blue",
            "rgb_hwc_zero_based_indices": [4, 2, 1],
        },
        "official_code": {
            "tracking_paths_select_bgr_zero_based": [1, 2, 4],
            "normalization_order": "to_rgb=False before/around CHW conversion in official tracking paths",
            "files": [
                {"path": str(official_memotr), "sha256": sha256(official_memotr)},
                {"path": str(official_motip), "sha256": sha256(official_motip)},
            ],
            "stale_or_unused_loader_conflict": {
                "path": str(official_loader),
                "sha256": sha256(official_loader),
                "behavior": "LoadRgbImageFromNpy slices img[:, :, :3]",
                "usage_search_result": "class definition found, but no instantiation in official tracked source paths",
            },
        },
        "historical_com3d": {
            "tracklet_reid": {
                "path": str(historical),
                "sha256": sha256(historical),
                "selection": [0, 1, 2],
                "interpretation": "PIL RGB",
                "resize": [128, 256],
                "resize_mode": "bilinear",
                "normalization_mean": [123.675, 116.28, 103.53],
                "normalization_std": [58.395, 57.12, 57.375],
            },
            "deep_ocsort": {
                "path": str(deepoc),
                "sha256": sha256(deepoc),
                "selection": [0, 1, 2],
                "interpretation": "PIL RGB",
            },
            "finding": "Bands 1,2,3 were incorrectly treated as RGB. Correct RGB input for the PIL/ImageNet path is bands 5,3,2, zero-based [4,2,1].",
        },
        "conversion": {
            "clipping": "none; source is already uint8 0..255",
            "float_conversion": "after 128x256 bilinear resize",
            "corrected_policy": "array[:, :, [4,2,1]] -> contiguous uint8 -> PIL RGB -> 128x256 bilinear -> RGB ImageNet normalization",
        },
        "sample_statistics": sample_rows,
        "evidence_directory": str(evidence_dir),
    }
    return result


def save_predictions(path: Path, family: str, sequence: str, class_name: str, tracker: str, predictions: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(path, "wt", encoding="utf-8", newline="") as handle:
        for frame in sorted(predictions):
            for row in predictions[frame]:
                payload = {
                    "family": family,
                    "sequence": sequence,
                    "class_name": class_name,
                    "tracker": tracker,
                    "frame": int(frame),
                    **{key: json_ready(value) for key, value in row.items()},
                }
                handle.write(json.dumps(payload, sort_keys=True, allow_nan=False) + "\n")


def rerun_no_refinement(workspace: Path, data_cache: Path, runs: Path, output_dir: Path, mmot) -> tuple[list[dict], dict, list[dict]]:
    families = {
        "data28": {
            "root": data_cache / "raw/MMOT/extracted/test",
            "stored": runs / "results/rebuttal_r3/mmot_locked_external/mmot_data28_locked_results.json",
        },
        "data30": {
            "root": data_cache / "raw/MMOT/extracted/confirmatory_data30",
            "stored": runs / "results/rebuttal_r3/mmot_data30_confirmatory/mmot_data30_confirmatory_results.json",
        },
    }
    stage_rows: list[dict] = []
    input_rows: list[dict] = []
    audit = {}
    for family, item in families.items():
        root = item["root"]
        stored = json.loads(item["stored"].read_text(encoding="utf-8"))
        method_data = defaultdict(list)
        per_sequence = {}
        for sequence_dir in sorted(path for path in root.iterdir() if path.is_dir()):
            frames, image_map, shape, summary = mmot.load_sequence(sequence_dir)
            input_rows.append({
                "dataset": "MMOT",
                "family": family,
                "sequence": sequence_dir.name,
                "sequence_path": str(sequence_dir),
                "frame_count": summary["frame_count"],
                "annotation_rows": summary["box_count"],
                "identity_count": summary["identity_count"],
                "array_shape": "x".join(str(value) for value in summary["array_shape"]),
                "array_dtype": summary["array_dtype"],
                "first_npy_sha256": sha256(image_map[min(image_map)]),
                "last_npy_sha256": sha256(image_map[max(image_map)]),
                "all_frames_used": len(image_map) == max(image_map) and min(image_map) == 1,
                "gt_source": "per-frame official TXT",
                "box_conversion": "OBB polygon to AABB min/max envelope",
                "oracle_score": 1.0,
            })
            sequence_data = defaultdict(list)
            for class_id, class_name in enumerate(mmot.CLASS_NAMES):
                gt = mmot.class_frames(frames, class_id)
                if not gt:
                    continue
                gt_boxes = sum(len(rows) for rows in gt.values())
                for tracker_name in ("bytetrack", "ocsort"):
                    started = time.perf_counter()
                    predictions = mmot.COMMON.run_sequence(tracker_name, gt, shape)
                    elapsed = time.perf_counter() - started
                    data = mmot.COMMON.metric_data(gt, predictions)
                    method_data[tracker_name].append(data)
                    sequence_data[tracker_name].append(data)
                    eligible = mmot.attach_npy_observations(gt, predictions, image_map)
                    output_boxes = sum(len(rows) for rows in predictions.values())
                    eligible_boxes = sum(len(rows) for rows in eligible.values())
                    output_path = output_dir / "results_raw/tracker_outputs" / family / sequence_dir.name / class_name / f"{tracker_name}.jsonl.gz"
                    save_predictions(output_path, family, sequence_dir.name, class_name, tracker_name, predictions)
                    stage_rows.append({
                        "dataset": "MMOT",
                        "family": family,
                        "sequence": sequence_dir.name,
                        "class_name": class_name,
                        "tracker": tracker_name,
                        "released_frames": len(image_map),
                        "frames_with_gt": len(gt),
                        "zero_gt_frames": len(image_map) - len(gt),
                        "valid_gt_boxes": gt_boxes,
                        "adapter_input_detections": gt_boxes,
                        "score_gate_admitted_detections": gt_boxes,
                        "tracker_output_boxes": output_boxes,
                        "tracker_output_track_ids": len({row["id"] for rows in predictions.values() for row in rows}),
                        "descriptor_eligible_output_boxes_iou_ge_0_9": eligible_boxes,
                        "descriptor_eligible_track_ids": len(eligible),
                        "evaluated_gt_boxes": data["num_gt_dets"],
                        "evaluated_prediction_boxes": data["num_tracker_dets"],
                        "duplicate_frame_identity_count": duplicate_frame_identity_count(predictions),
                        "tracker_runtime_seconds": elapsed,
                        "saved_output": str(output_path),
                        "saved_output_sha256": sha256(output_path),
                    })
            per_sequence[sequence_dir.name] = {
                method: mmot.combined_metrics(values) for method, values in sorted(sequence_data.items())
            }
        combined = {method: mmot.combined_metrics(values) for method, values in sorted(method_data.items())}
        comparisons = {}
        family_pass = True
        for tracker_name in ("bytetrack", "ocsort"):
            passed, differences = metric_close(combined[tracker_name], stored["combined_metrics"][tracker_name])
            family_pass &= passed
            comparisons[tracker_name] = {
                "passed": passed,
                "rerun": combined[tracker_name],
                "stored": stored["combined_metrics"][tracker_name],
                "differences": differences,
            }
        audit[family] = {
            "status": "PASS" if family_pass else "FAIL",
            "stored_result": str(item["stored"]),
            "stored_result_sha256": sha256(item["stored"]),
            "comparisons": comparisons,
            "per_sequence_rerun": per_sequence,
        }
    return stage_rows, audit, input_rows


def protocol_markdown(channel: dict, sanity: dict, repeat: dict, tracker: dict) -> str:
    repeat_rows = []
    for family, family_result in repeat.items():
        for method, comparison in family_result["comparisons"].items():
            repeat_rows.append(
                f"| {family} | {method} | {comparison['passed']} | "
                f"{comparison['rerun']['HOTA']:.12f} | {comparison['rerun']['IDF1']:.12f} | "
                f"{comparison['rerun']['IDSW']} |"
            )
    return "\n".join([
        "# CoM3D-ACE Temporal Protocol Audit (E0)",
        "",
        "## Gate decision",
        "",
        f"- Channel provenance: **{channel['status']}**",
        f"- Evaluator sanity: **{sanity['status']}**",
        "- Historical no-refinement reproduction: **" + ("PASS" if all(item["status"] == "PASS" for item in repeat.values()) else "FAIL") + "**",
        f"- CUDA available during audit: **{tracker['runtime_environment']['cuda_available']}**",
        "",
        "The evaluator and upstream tracker baselines pass their deterministic checks. The appearance path does not pass E0 because the historical runner treated spectral bands 1,2,3 as PIL RGB. The official paper defines the RGB proxy as bands 5,3,2; the corrected PIL/ImageNet path is zero-based `[4,2,1]`. Appearance-based MMOT and Deep OC-SORT results must therefore be recomputed in a new result namespace before paper use.",
        "",
        "## No-refinement reproduction",
        "",
        "| Family | Tracker | Exact match | HOTA | IDF1 | IDSW |",
        "|---|---|---:|---:|---:|---:|",
        *repeat_rows,
        "",
        "## Protocol boundaries",
        "",
        "- Inputs are official MMOT OBB ground truth converted to axis-aligned envelopes with score 1.0. These are oracle detections, not detector outputs.",
        "- A separate tracker instance is run for each of the eight MMOT classes. All released frames in the selected data28 and data30 families are traversed.",
        "- The historical CoM3D baselines use BoxMOT AABB defaults, not MMOT's official rotated trackers or their published settings.",
        "- GT identities are used after predictions for evaluation and accepted-link diagnostics. GT geometry is also used by the historical adapter to decide which tracker observations receive appearance crops (IoU >= 0.9); this must be disclosed as part of the oracle-box protocol.",
        "- MMOT's paper describes a relatively low frame rate but does not provide a per-sequence timestamp/FPS manifest in the downloaded archives. No physical-time conversion is asserted here.",
        "",
        "## E0 disposition",
        "",
        "`corrected-rerun-required`: proceed only with a versioned corrected channel adapter; preserve historical values as invalidated-by-input-audit rather than overwriting them.",
        "",
    ])


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workspace", type=Path, required=True)
    parser.add_argument("--data-cache", type=Path, required=True)
    parser.add_argument("--runs", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    trackeval_root = args.workspace / "third_party/trackeval_official"
    boxmot_root = args.workspace / "third_party/boxmot_official"
    sys.path.insert(0, str(trackeval_root))
    sys.path.insert(0, str(boxmot_root))
    mmot = load_module("com3d_e0_mmot", args.workspace / "scripts/run_mmot_locked_temporal.py")

    started = time.perf_counter()
    channel = channel_audit(args.workspace, args.data_cache, args.output_dir, mmot)
    sanity = evaluator_sanity(mmot)
    tracker = tracker_config_audit(args.workspace, mmot)
    stage_rows, repeat, input_rows = rerun_no_refinement(args.workspace, args.data_cache, args.runs, args.output_dir, mmot)

    write_json(args.output_dir / "channel_audit.json", channel)
    write_json(args.output_dir / "evaluator_sanity_tests.json", {**sanity, "no_refinement_reproduction": repeat})
    write_json(args.output_dir / "tracker_runtime_configs.json", tracker)
    write_csv(args.output_dir / "stage_counts.csv", stage_rows)
    write_csv(args.output_dir / "input_manifest.csv", input_rows)
    (args.output_dir / "protocol_audit.md").write_text(protocol_markdown(channel, sanity, repeat, tracker), encoding="utf-8")
    execution = {
        "status": "PASS_WITH_CORRECTED_RERUN_REQUIRED" if sanity["status"] == "PASS" and all(item["status"] == "PASS" for item in repeat.values()) else "FAIL",
        "command": " ".join(sys.argv),
        "started_unix": time.time() - (time.perf_counter() - started),
        "runtime_seconds": time.perf_counter() - started,
        "script_sha256": sha256(Path(__file__)),
        "outputs": {
            path.name: sha256(path)
            for path in args.output_dir.iterdir()
            if path.is_file()
        },
    }
    write_json(args.output_dir / "e0_execution_manifest.json", execution)
    print(json.dumps({
        "status": execution["status"],
        "runtime_seconds": execution["runtime_seconds"],
        "channel_status": channel["status"],
        "evaluator_status": sanity["status"],
        "repeat_status": {key: value["status"] for key, value in repeat.items()},
    }, indent=2))
    return 0 if execution["status"] == "PASS_WITH_CORRECTED_RERUN_REQUIRED" else 2


if __name__ == "__main__":
    raise SystemExit(main())
