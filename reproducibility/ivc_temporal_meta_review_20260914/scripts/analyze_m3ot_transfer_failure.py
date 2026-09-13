#!/usr/bin/env python3
"""Enrich locked M3OT development/test results with failure diagnostics.

The frozen result JSON supplies accepted links. Tracker outputs are regenerated
only to recover geometry, tracklet size, and post-hoc GT correspondence; no
threshold or link decision is changed.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import json
import math
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import numpy as np


POLICY = "geometry_reid_reciprocal"
MAX_GAP = 30


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


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")


def write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = sorted({key for row in rows for key in row})
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def tracklets(predictions: dict[int, list[dict]]) -> tuple[dict[int, set[int]], dict[int, list[tuple[int, dict]]]]:
    frames = defaultdict(set)
    rows = defaultdict(list)
    for frame, values in predictions.items():
        for row in values:
            identity = int(row["id"])
            frames[identity].add(int(frame))
            rows[identity].append((int(frame), row))
    for identity in rows:
        rows[identity].sort(key=lambda item: item[0])
    return dict(frames), dict(rows)


def median_area(rows: list[tuple[int, dict]]) -> float:
    return float(np.median([float(row["w"]) * float(row["h"]) for _, row in rows]))


def chronological_gap(left: set[int], right: set[int]) -> tuple[int | None, int | None, int | None]:
    if left & right:
        return None, None, None
    if max(left) < min(right):
        return min(right) - max(left), max(left), min(right)
    if max(right) < min(left):
        return min(left) - max(right), max(right), min(left)
    return None, None, None


def reproduce_baseline(common, stored: dict, tracker: str, gt: dict, predictions: dict) -> dict:
    observed = common.evaluate(common.metric_data(gt, predictions))
    expected = stored[tracker]
    differences = {
        key: float(observed[key]) - float(expected[key])
        for key in ("HOTA", "AssA", "DetA", "IDF1", "MOTA", "IDSW", "valid_gt_boxes", "predicted_boxes")
    }
    return {
        "tracker": tracker,
        "exact_within_1e_10": all(abs(value) <= 1e-10 for value in differences.values()),
        "maximum_absolute_difference": max(abs(value) for value in differences.values()),
        "differences": differences,
    }


def union_component_sizes(frames: dict[int, set[int]], edges: list[dict]) -> dict[tuple[int, int], dict]:
    parent = {identity: identity for identity in frames}
    members = {identity: {identity} for identity in frames}
    support = {identity: set(values) for identity, values in frames.items()}

    def find(identity: int) -> int:
        while parent[identity] != identity:
            parent[identity] = parent[parent[identity]]
            identity = parent[identity]
        return identity

    output = {}
    for edge in edges:
        left, right = int(edge["earlier"]), int(edge["later"])
        left_root, right_root = find(left), find(right)
        overlap = support[left_root] & support[right_root]
        output[(left, right)] = {
            "source_component_tracklets_before": len(members[left_root]),
            "destination_component_tracklets_before": len(members[right_root]),
            "component_size_after": len(members[left_root]) + len(members[right_root]),
            "component_frame_overlap_count": len(overlap),
        }
        if not overlap and left_root != right_root:
            parent[right_root] = left_root
            members[left_root] |= members[right_root]
            support[left_root] |= support[right_root]
    return output


def opportunity_rows(split: str, sequence: str, modality: str, tracker: str, frames: dict, rows: dict, labels: dict) -> list[dict]:
    output = []
    identities = sorted(frames)
    for index, left in enumerate(identities):
        for right in identities[index + 1:]:
            if left not in labels or right not in labels:
                continue
            if labels[left]["majority_gt_identity"] != labels[right]["majority_gt_identity"]:
                continue
            gap, source_frame, destination_frame = chronological_gap(frames[left], frames[right])
            if gap is None or gap > MAX_GAP:
                continue
            if max(frames[right]) < min(frames[left]):
                source_id, destination_id = right, left
            else:
                source_id, destination_id = left, right
            source = rows[source_id][-1][1]
            destination = rows[destination_id][0][1]
            source_center = np.asarray([source["x"] + source["w"] / 2, source["y"] + source["h"] / 2])
            destination_center = np.asarray([destination["x"] + destination["w"] / 2, destination["y"] + destination["h"] / 2])
            output.append({
                "split": split, "dataset": "M3OT", "sequence": sequence,
                "modality": modality, "tracker": tracker,
                "source_id": source_id, "destination_id": destination_id,
                "source_frame": source_frame, "destination_frame": destination_frame,
                "gap": gap,
                "endpoint_center_distance_pixels": float(np.linalg.norm(source_center - destination_center)),
                "source_crop_area_median_px2": median_area(rows[source_id]),
                "destination_crop_area_median_px2": median_area(rows[destination_id]),
                "posthoc_gt_identity": labels[source_id]["majority_gt_identity"],
                "source_gt_purity": labels[source_id]["purity"],
                "destination_gt_purity": labels[destination_id]["purity"],
            })
    return output


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workspace", type=Path, required=True)
    parser.add_argument("--val-manifest", type=Path, required=True)
    parser.add_argument("--val-results", type=Path, required=True)
    parser.add_argument("--test-manifest", type=Path, required=True)
    parser.add_argument("--test-results", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    module = load_module("m3ot_failure_diagnostic_source", args.workspace / "scripts/run_m3ot_ambiguity_aware.py")
    common = module.COMMON
    inputs = [
        ("development", args.val_manifest, args.val_results),
        ("held_out", args.test_manifest, args.test_results),
    ]
    failure_rows = []
    opportunity_output = []
    sequence_summary = []
    reproduction = []
    started = time.perf_counter()

    for split, manifest_path, results_path in inputs:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        results = json.loads(results_path.read_text(encoding="utf-8"))
        stored_sequences = {row["sequence"]: row["methods"] for row in results["sequence_results"]}
        root = Path(manifest["data_root"])
        for sequence in manifest["sequences"]:
            name = sequence["sequence_relative_path"]
            modality = sequence["tags"][0]
            gt = common.parse_gt(root / sequence["gt_relative_path"])
            shape = common.image_shape(root / sequence["img_relative_path"])
            diagonal = math.hypot(shape[1], shape[0])
            for tracker in ("bytetrack", "ocsort"):
                predictions = common.run_sequence(tracker, gt, shape)
                frames, rows = tracklets(predictions)
                labels = module.tracklet_gt_labels(gt, predictions)
                reproduction.append({
                    "split": split, "sequence": name,
                    **reproduce_baseline(common, stored_sequences[name], tracker, gt, predictions),
                })
                opportunities = opportunity_rows(split, name, modality, tracker, frames, rows, labels)
                opportunity_output.extend(opportunities)
                method = f"{tracker}__{POLICY}"
                graph = stored_sequences[name][method]["graph"]
                accepted = graph["accepted_edges"]
                components = union_component_sizes(frames, accepted)
                for edge in accepted:
                    source_id, destination_id = int(edge["earlier"]), int(edge["later"])
                    source_row = rows[source_id][-1][1]
                    destination_row = rows[destination_id][0][1]
                    source_area = median_area(rows[source_id])
                    destination_area = median_area(rows[destination_id])
                    left_label = labels.get(source_id, {})
                    right_label = labels.get(destination_id, {})
                    failure_rows.append({
                        "dataset": "M3OT", "split": split, "sequence": name,
                        "modality": modality, "tracker": tracker,
                        "source_id": source_id, "destination_id": destination_id,
                        "source_last_frame": max(frames[source_id]),
                        "destination_first_frame": min(frames[destination_id]),
                        "gap": int(edge["gap"]),
                        "displacement_px": float(edge["endpoint_center_distance_pixels"]),
                        "displacement_normalized_by_frame_diagonal": float(edge["endpoint_center_distance_pixels"]) / diagonal,
                        "appearance_distance": float(edge["cosine_distance"]),
                        "source_crop_area_median_px2": source_area,
                        "destination_crop_area_median_px2": destination_area,
                        "crop_area_min_median_px2": min(source_area, destination_area),
                        "source_tracklet_length": len(frames[source_id]),
                        "destination_tracklet_length": len(frames[destination_id]),
                        "source_majority_gt_identity": left_label.get("majority_gt_identity"),
                        "destination_majority_gt_identity": right_label.get("majority_gt_identity"),
                        "source_gt_purity": left_label.get("purity"),
                        "destination_gt_purity": right_label.get("purity"),
                        "posthoc_GT_correctness": edge["gt_relation"],
                        "source_endpoint_area_px2": float(source_row["w"] * source_row["h"]),
                        "destination_endpoint_area_px2": float(destination_row["w"] * destination_row["h"]),
                        **components[(source_id, destination_id)],
                    })
                baseline = stored_sequences[name][tracker]
                refined = stored_sequences[name][method]
                sequence_summary.append({
                    "dataset": "M3OT", "split": split, "sequence": name,
                    "modality": modality, "tracker": tracker,
                    "tracklet_count": len(frames),
                    "GT_labeled_tracklets": len(labels),
                    "correct_fragment_opportunities_gap_le_30": len(opportunities),
                    "candidate_support_edges": graph["candidate_support_edges"],
                    "accepted_links": graph["accepted_support_edges"],
                    "accepted_correct": graph["accepted_edges_correct_gt"],
                    "accepted_false": graph["accepted_edges_false_merge_gt"],
                    "baseline_HOTA": baseline["HOTA"],
                    "refined_HOTA": refined["HOTA"],
                    "delta_HOTA": refined["HOTA"] - baseline["HOTA"],
                    "baseline_AssA": baseline["AssA"],
                    "refined_AssA": refined["AssA"],
                    "delta_AssA": refined["AssA"] - baseline["AssA"],
                    "baseline_IDF1": baseline["IDF1"],
                    "refined_IDF1": refined["IDF1"],
                    "delta_IDF1": refined["IDF1"] - baseline["IDF1"],
                    "baseline_IDSW": baseline["IDSW"],
                    "refined_IDSW": refined["IDSW"],
                    "delta_IDSW": refined["IDSW"] - baseline["IDSW"],
                })

    write_csv(args.output_dir / "m3ot_failure_links.csv", failure_rows)
    write_csv(args.output_dir / "m3ot_correct_fragment_opportunities.csv", opportunity_output)
    write_csv(args.output_dir / "m3ot_sequence_diagnostics.csv", sequence_summary)
    write_json(args.output_dir / "m3ot_baseline_reproduction.json", reproduction)
    all_reproduced = all(row["exact_within_1e_10"] for row in reproduction)
    manifest = {
        "status": "COMPLETE" if all_reproduced else "FAILED_REPRODUCTION_CHECK",
        "claim_scope": "Post-hoc diagnostic of frozen M3OT development and held-out results; no retuning.",
        "policy": POLICY,
        "maximum_gap_frames": MAX_GAP,
        "ground_truth_use": "Only tracker inputs mandated by the historical oracle-box protocol, metrics, and post-hoc edge/opportunity labels.",
        "normalized_displacement_definition": "Endpoint center distance divided by native frame diagonal.",
        "crop_area_definition": "Median native-pixel tracker-box area within each endpoint tracklet.",
        "inputs": {
            str(path): sha256(path)
            for path in (args.val_manifest, args.val_results, args.test_manifest, args.test_results)
        },
        "script_sha256": sha256(Path(__file__)),
        "baseline_reproduction_passed": all_reproduced,
        "accepted_links": len(failure_rows),
        "correct_fragment_opportunities": len(opportunity_output),
        "runtime_seconds": time.perf_counter() - started,
    }
    write_json(args.output_dir / "manifest.json", manifest)
    print(json.dumps(manifest, indent=2))
    return 0 if all_reproduced else 2


if __name__ == "__main__":
    raise SystemExit(main())
