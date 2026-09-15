#!/usr/bin/env python3
"""Select ACE-V on M3OT val using direct tracker-box crops, then retest held-out."""

from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import importlib.util
import json
import math
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
import torch
from scipy.optimize import linear_sum_assignment


TAU_A = (0.00, 0.05, 0.10)
TAU_M = (1.0, 2.0, 4.0, 8.0)
TRACKERS = ("bytetrack", "ocsort")


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def sha256(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = sorted({key for row in rows for key in row})
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )


def save_predictions(path: Path, predictions: dict[int, list[dict]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(path, "wt", encoding="utf-8") as handle:
        for frame in sorted(predictions):
            for row in predictions[frame]:
                handle.write(json.dumps({"frame": frame, **row}, sort_keys=True) + "\n")


def direct_tracker_observations(predictions: dict, image_map: dict[int, Path]) -> tuple[dict, dict]:
    tracklets: dict[int, list[dict]] = defaultdict(list)
    counts = Counter()
    for frame, rows in predictions.items():
        for row in rows:
            counts["tracker_observations"] += 1
            image_path = image_map.get(int(frame))
            if image_path is None or not image_path.is_file():
                counts["missing_image"] += 1
                continue
            x1 = int(round(float(row["x"])))
            y1 = int(round(float(row["y"])))
            x2 = int(round(float(row["x"]) + float(row["w"])))
            y2 = int(round(float(row["y"]) + float(row["h"])))
            if x2 <= x1 or y2 <= y1:
                counts["invalid_box"] += 1
                continue
            tracklets[int(row["id"])].append({
                "frame": int(frame),
                "image_path": image_path,
                "bbox_xyxy": (x1, y1, x2, y2),
                "class_id": int(row.get("class_id", 1)),
            })
            counts["admitted_direct_tracker_boxes"] += 1
    counts["tracklets_total"] = len({int(row["id"]) for rows in predictions.values() for row in rows})
    counts["tracklets_with_direct_crops"] = len(tracklets)
    return dict(tracklets), dict(counts)


def audit_labels(common, gt: dict, predictions: dict) -> dict[int, dict]:
    matched: dict[int, Counter] = defaultdict(Counter)
    tracklet_observations = Counter()
    for frame, prediction_rows in predictions.items():
        for row in prediction_rows:
            tracklet_observations[int(row["id"])] += 1
        gt_rows = gt.get(frame, [])
        if not gt_rows or not prediction_rows:
            continue
        gt_boxes = np.asarray([
            [row["x"], row["y"], row["x"] + row["w"], row["y"] + row["h"]]
            for row in gt_rows
        ], dtype=float)
        prediction_boxes = np.asarray([
            [row["x"], row["y"], row["x"] + row["w"], row["y"] + row["h"]]
            for row in prediction_rows
        ], dtype=float)
        similarities = common.iou_matrix(gt_boxes, prediction_boxes)
        gt_indices, prediction_indices = linear_sum_assignment(-similarities)
        for gt_index, prediction_index in zip(gt_indices, prediction_indices):
            if similarities[gt_index, prediction_index] >= 0.9:
                matched[int(prediction_rows[prediction_index]["id"])][int(gt_rows[gt_index]["id"])] += 1
    output = {}
    for identity, counts in matched.items():
        maximum = max(counts.values())
        tied = sorted(label for label, count in counts.items() if count == maximum)
        total = sum(counts.values())
        output[identity] = {
            "majority_gt_identity": tied[0],
            "majority_count": maximum,
            "matched_observations": total,
            "tracklet_observations": tracklet_observations[identity],
            "purity": maximum / total,
            "distinct_gt_identities": len(counts),
            "majority_tie_count": len(tied),
            "majority_tied": len(tied) > 1,
        }
    return output


def relation(edge: dict, labels: dict[int, dict], exclude_ties: bool = False) -> str:
    left = labels.get(int(edge["earlier"]))
    right = labels.get(int(edge["later"]))
    if left is None or right is None:
        return "unknown"
    if exclude_ties and (left["majority_tied"] or right["majority_tied"]):
        return "ambiguous_tie"
    return (
        "correct"
        if left["majority_gt_identity"] == right["majority_gt_identity"]
        else "false"
    )


def extended_metrics(common, data: dict) -> dict:
    output = common.evaluate(data)
    clear = common.CLEAR({"PRINT_CONFIG": False}).eval_sequence(data)
    output.update({
        "FP": int(clear["CLR_FP"]),
        "FN": int(clear["CLR_FN"]),
        "TP": int(clear["CLR_TP"]),
        "Frag": int(clear["Frag"]),
    })
    return output


def invariant_signature(predictions: dict) -> Counter:
    return Counter(
        (
            int(frame), round(float(row["x"]), 7), round(float(row["y"]), 7),
            round(float(row["w"]), 7), round(float(row["h"]), 7),
            round(float(row.get("conf", 1.0)), 7), int(row.get("class_id", -1)),
        )
        for frame, rows in predictions.items() for row in rows
    )


def duplicate_count(predictions: dict) -> int:
    return sum(
        sum(count - 1 for count in Counter(int(row["id"]) for row in rows).values() if count > 1)
        for rows in predictions.values()
    )


def method_result(
    diagnostic,
    ace,
    common,
    predictions: dict,
    labels: dict,
    name: str,
    selected: list[dict],
    started: float,
    tau_a: float | None = None,
    tau_m: float | None = None,
) -> tuple[dict, list[dict], list[dict], dict]:
    output, accepted, rejected = diagnostic.apply_edges(predictions, selected, ace.edge_key)
    ace.assert_path_constraints(accepted) if name.startswith(("cost_h", "path_g")) else None
    data = common.metric_data(labels["__gt__"], output)
    counts = Counter(relation(edge, labels) for edge in accepted)
    tie_counts = Counter(relation(edge, labels, exclude_ties=True) for edge in accepted)
    row = {
        "method": name,
        "tau_a": tau_a if tau_a is not None else "N/A",
        "tau_m": tau_m if tau_m is not None else "N/A",
        **extended_metrics(common, data),
        "accepted_links": len(accepted),
        "accepted_correct": counts["correct"],
        "accepted_false": counts["false"],
        "accepted_unknown": counts["unknown"],
        "tie_excluded_correct": tie_counts["correct"],
        "tie_excluded_false": tie_counts["false"],
        "tie_ambiguous": tie_counts["ambiguous_tie"],
        "component_rejections": len(rejected),
        "box_multiset_preserved": invariant_signature(predictions) == invariant_signature(output),
        "duplicate_frame_identity_count": duplicate_count(output),
        "solver_seconds": time.perf_counter() - started,
    }
    return output, accepted, rejected, row


def evaluate_instance(diagnostic, ace, common, predictions, descriptors, labels, full_grid: bool, selected_config=None):
    all_edges = diagnostic.complete_temporal_edges(predictions, descriptors)
    gated = diagnostic.fixed_gated(all_edges)
    feature_started = time.perf_counter()
    features = ace.add_verification_features(gated, predictions)
    feature_seconds = time.perf_counter() - feature_started
    geometry_key = lambda edge: (
        edge["endpoint_center_distance_pixels"], edge["cosine_distance"], edge["gap"],
        edge["earlier"], edge["later"],
    )
    baseline_selections = {
        "ace_v1": diagnostic.reciprocal(gated, geometry_key),
        "cost_r": diagnostic.reciprocal(gated, ace.edge_key),
        "cost_g_legacy": gated,
        "cost_h": ace.partial_hungarian(features),
        "path_g": ace.path_constrained_greedy(features),
    }
    rows = []
    accepted_by_method = {}
    labels_with_gt = dict(labels)
    labels_with_gt["__gt__"] = labels["__gt__"]

    no_refinement = {
        "method": "no_refinement", "tau_a": "N/A", "tau_m": "N/A",
        **extended_metrics(common, common.metric_data(labels["__gt__"], predictions)),
        "accepted_links": 0, "accepted_correct": 0, "accepted_false": 0,
        "accepted_unknown": 0, "tie_excluded_correct": 0,
        "tie_excluded_false": 0, "tie_ambiguous": 0, "component_rejections": 0,
        "box_multiset_preserved": True,
        "duplicate_frame_identity_count": duplicate_count(predictions),
        "solver_seconds": 0.0,
    }
    rows.append(no_refinement)
    for name, selection in baseline_selections.items():
        started = time.perf_counter()
        _, accepted, _, row = method_result(
            diagnostic, ace, common, predictions, labels_with_gt, name, selection, started
        )
        rows.append(row)
        accepted_by_method[name] = accepted

    configurations = (
        [(tau_a, tau_m) for tau_a in TAU_A for tau_m in TAU_M]
        if full_grid else [selected_config]
    )
    for tau_a, tau_m in configurations:
        family_selections = {
            "cost_h_margin_reassign": ace.partial_hungarian(
                ace.filter_edges(features, "V_margin", tau_a, tau_m)
            ),
            "cost_h_motion_reassign": ace.partial_hungarian(
                ace.filter_edges(features, "V_motion", tau_a, tau_m)
            ),
            "cost_h_full_postfilter": ace.filter_edges(
                baseline_selections["cost_h"], "V_full", tau_a, tau_m
            ),
            "cost_h_full_reassign": ace.partial_hungarian(
                ace.filter_edges(features, "V_full", tau_a, tau_m)
            ),
            "path_g_full_reassign": ace.path_constrained_greedy(
                ace.filter_edges(features, "V_full", tau_a, tau_m)
            ),
        }
        for name, selection in family_selections.items():
            started = time.perf_counter()
            _, accepted, _, row = method_result(
                diagnostic, ace, common, predictions, labels_with_gt, name,
                selection, started, tau_a, tau_m,
            )
            rows.append(row)
            accepted_by_method[f"{name}:{tau_a}:{tau_m}"] = accepted
    if full_grid or selected_config is not None:
        started = time.perf_counter()
        soft = ace.partial_hungarian(features, cost=ace.soft_information_cost)
        _, accepted, _, row = method_result(
            diagnostic, ace, common, predictions, labels_with_gt,
            "cost_h_soft_information", soft, started,
        )
        rows.append(row)
        accepted_by_method["cost_h_soft_information"] = accepted
    return rows, features, accepted_by_method, all_edges, feature_seconds


def aggregate(rows: list[dict], split: str) -> list[dict]:
    groups: dict[tuple, list[dict]] = defaultdict(list)
    for row in rows:
        groups[(row["method"], row["tau_a"], row["tau_m"])].append(row)
    output = []
    for (method, tau_a, tau_m), values in sorted(groups.items(), key=lambda item: str(item[0])):
        output.append({
            "split": split,
            "method": method,
            "tau_a": tau_a,
            "tau_m": tau_m,
            "sequence_tracker_units": len(values),
            **{
                key: float(np.mean([float(row[key]) for row in values]))
                for key in ("HOTA", "AssA", "DetA", "IDF1", "MOTA")
            },
            **{
                key: int(sum(int(row[key]) for row in values))
                for key in (
                    "IDSW", "FP", "FN", "TP", "Frag", "accepted_links",
                    "accepted_correct", "accepted_false", "accepted_unknown",
                    "tie_excluded_correct", "tie_excluded_false", "tie_ambiguous",
                    "component_rejections", "duplicate_frame_identity_count",
                )
            },
            "all_box_multisets_preserved": all(row["box_multiset_preserved"] for row in values),
            "solver_seconds": sum(float(row["solver_seconds"]) for row in values),
        })
    return output


def correct_opportunities(diagnostic, predictions, descriptors, labels, all_edges, split, sequence, tracker):
    frames, rows = diagnostic.tracklets(predictions)
    edge_lookup = {(int(edge["earlier"]), int(edge["later"])): edge for edge in all_edges}
    output = []
    for source in sorted(frames):
        for destination in sorted(frames):
            if source == destination or source not in labels or destination not in labels:
                continue
            if labels[source]["majority_gt_identity"] != labels[destination]["majority_gt_identity"]:
                continue
            if frames[source] & frames[destination] or max(frames[source]) >= min(frames[destination]):
                continue
            gap = min(frames[destination]) - max(frames[source])
            if gap > 30:
                continue
            edge = edge_lookup.get((source, destination))
            first = rows[source][-1][1]
            second = rows[destination][0][1]
            distance = float(np.linalg.norm(np.asarray([
                first["x"] + first["w"] / 2, first["y"] + first["h"] / 2,
            ]) - np.asarray([
                second["x"] + second["w"] / 2, second["y"] + second["h"] / 2,
            ])))
            appearance = edge["cosine_distance"] if edge else None
            if source not in descriptors or destination not in descriptors:
                reason = "missing_descriptor"
            elif appearance is None or appearance > 0.30:
                reason = "appearance_gate"
            elif distance > 55.0:
                reason = "geometry_gate"
            else:
                reason = "entered_fixed_candidate_graph"
            output.append({
                "split": split, "sequence": sequence, "tracker": tracker,
                "source_id": source, "destination_id": destination,
                "gt_identity": labels[source]["majority_gt_identity"],
                "source_label_tied": labels[source]["majority_tied"],
                "destination_label_tied": labels[destination]["majority_tied"],
                "gap": gap, "geometry_pixels": distance,
                "appearance_distance": appearance if appearance is not None else "N/A",
                "candidate_status": reason,
                "enters_fixed_candidate_graph": reason == "entered_fixed_candidate_graph",
            })
    return output


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workspace", type=Path, required=True)
    parser.add_argument("--diagnostic-script", type=Path, required=True)
    parser.add_argument("--ace-core", type=Path, required=True)
    parser.add_argument("--development-manifest", type=Path, required=True)
    parser.add_argument("--held-out-manifest", type=Path, required=True)
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--threads", type=int, default=8)
    args = parser.parse_args()
    if args.output_dir.exists() and any(args.output_dir.iterdir()):
        raise SystemExit(f"refusing to overwrite non-empty output directory: {args.output_dir}")
    args.output_dir.mkdir(parents=True, exist_ok=True)
    torch.set_num_threads(args.threads)
    sys.path.insert(0, str(args.workspace / "third_party/trackeval_official"))
    sys.path.insert(0, str(args.workspace / "third_party/boxmot_official"))
    module = load_module("ace_v_m3ot_module", args.workspace / "scripts/run_m3ot_ambiguity_aware.py")
    diagnostic = load_module("ace_v_m3ot_diagnostic", args.diagnostic_script)
    ace = load_module("ace_v_m3ot_core", args.ace_core)
    device = torch.device(args.device)
    model, checkpoint_manifest = module.REID.load_reid(args.checkpoint, device)
    model.eval()

    sequence_rows = []
    feature_rows = []
    link_rows = []
    crop_rows = []
    candidate_rows = []
    runtime_rows = []
    selected_config = None
    aggregate_rows = []
    started_all = time.perf_counter()

    # The held-out manifest is deliberately not loaded until development selection is frozen.
    for split, manifest_path in (("development", args.development_manifest), ("held_out", args.held_out_manifest)):
        if split == "held_out" and selected_config is None:
            raise RuntimeError("held-out evaluation attempted before development selection")
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        root = Path(manifest["data_root"])
        split_rows = []
        for sequence_spec in manifest["sequences"]:
            sequence = sequence_spec["sequence_relative_path"]
            modality = sequence_spec["tags"][0]
            print(f"{split} {sequence}", flush=True)
            gt = module.COMMON.parse_gt(root / sequence_spec["gt_relative_path"])
            image_dir = root / sequence_spec["img_relative_path"]
            shape = module.COMMON.image_shape(image_dir)
            images = module.BASE.frame_images(image_dir)
            for tracker in TRACKERS:
                tracker_started = time.perf_counter()
                predictions = module.COMMON.run_sequence(tracker, gt, shape)
                tracker_seconds = time.perf_counter() - tracker_started
                prediction_path = args.output_dir / "tracker_outputs" / split / sequence.replace("/", "__") / f"{tracker}.jsonl.gz"
                save_predictions(prediction_path, predictions)
                observations, crop_counts = direct_tracker_observations(predictions, images)
                descriptor_started = time.perf_counter()
                descriptors = module.BASE.extract_tracklet_descriptors(observations, model, device)
                descriptor_seconds = time.perf_counter() - descriptor_started
                descriptor_path = args.output_dir / "descriptors" / split / sequence.replace("/", "__") / f"{tracker}.npz"
                descriptor_path.parent.mkdir(parents=True, exist_ok=True)
                np.savez_compressed(descriptor_path, **{str(key): value for key, value in descriptors.items()})
                labels = audit_labels(module.COMMON, gt, predictions)
                labels["__gt__"] = gt
                rows, features, accepted, all_edges, feature_seconds = evaluate_instance(
                    diagnostic, ace, module.COMMON, predictions, descriptors, labels,
                    full_grid=split == "development", selected_config=selected_config,
                )
                for row in rows:
                    contextual = {
                        "split": split, "sequence": sequence, "modality": modality,
                        "tracker": tracker, **row,
                    }
                    split_rows.append(contextual)
                    sequence_rows.append(contextual)
                for feature in features:
                    feature_rows.append({
                        "split": split, "sequence": sequence, "modality": modality,
                        "tracker": tracker, **feature,
                        "posthoc_gt_relation": relation(feature, labels),
                        "posthoc_gt_relation_ties_excluded": relation(feature, labels, True),
                        "source_matched_observations": labels.get(int(feature["earlier"]), {}).get("matched_observations", "N/A"),
                        "destination_matched_observations": labels.get(int(feature["later"]), {}).get("matched_observations", "N/A"),
                        "source_label_purity": labels.get(int(feature["earlier"]), {}).get("purity", "N/A"),
                        "destination_label_purity": labels.get(int(feature["later"]), {}).get("purity", "N/A"),
                        "source_majority_tied": labels.get(int(feature["earlier"]), {}).get("majority_tied", "N/A"),
                        "destination_majority_tied": labels.get(int(feature["later"]), {}).get("majority_tied", "N/A"),
                    })
                for method, edges in accepted.items():
                    for edge in edges:
                        link_rows.append({
                            "split": split, "sequence": sequence, "modality": modality,
                            "tracker": tracker, "method": method, **edge,
                            "posthoc_gt_relation": relation(edge, labels),
                            "posthoc_gt_relation_ties_excluded": relation(edge, labels, True),
                        })
                crop_rows.append({
                    "split": split, "sequence": sequence, "modality": modality,
                    "tracker": tracker, **crop_counts,
                    "descriptor_count": len(descriptors),
                    "prediction_path": str(prediction_path),
                    "prediction_sha256": sha256(prediction_path),
                    "descriptor_path": str(descriptor_path),
                    "descriptor_sha256": sha256(descriptor_path),
                    "crop_admission_uses_gt": False,
                })
                candidate_rows.extend(correct_opportunities(
                    diagnostic, predictions, descriptors, labels, all_edges,
                    split, sequence, tracker,
                ))
                runtime_rows.append({
                    "split": split, "sequence": sequence, "modality": modality,
                    "tracker": tracker, "tracker_seconds": tracker_seconds,
                    "descriptor_seconds": descriptor_seconds,
                    "verification_feature_seconds": feature_seconds,
                    "device": str(device), "threads": args.threads,
                })

        split_aggregate = aggregate(split_rows, split)
        aggregate_rows.extend(split_aggregate)
        if split == "development":
            full_rows = [row for row in split_aggregate if row["method"] == "cost_h_full_reassign"]
            baseline_h = next(row for row in split_aggregate if row["method"] == "cost_h")
            baseline_g = next(row for row in split_aggregate if row["method"] == "path_g")
            selection_rows = []
            for row in full_rows:
                path = next(
                    item for item in split_aggregate
                    if item["method"] == "path_g_full_reassign"
                    and float(item["tau_a"]) == float(row["tau_a"])
                    and float(item["tau_m"]) == float(row["tau_m"])
                )
                selection_rows.append({
                    **row,
                    "delta_h_idf1_pp": row["IDF1"] - baseline_h["IDF1"],
                    "path_g_idf1": path["IDF1"],
                    "delta_path_g_idf1_pp": path["IDF1"] - baseline_g["IDF1"],
                    "selection_dataset": "M3OT val direct tracker-box crops",
                })
            selection_rows.sort(key=lambda row: (
                -float(row["IDF1"]), int(row["accepted_false"]),
                float(row["solver_seconds"]), float(row["tau_a"]), float(row["tau_m"]),
            ))
            for index, row in enumerate(selection_rows, start=1):
                row["selection_rank"] = index
                row["selected"] = index == 1
            selected_config = (
                float(selection_rows[0]["tau_a"]), float(selection_rows[0]["tau_m"])
            )
            write_csv(args.output_dir / "development_selection.csv", selection_rows)
            write_json(args.output_dir / "selected_config.json", {
                "selected_before_held_out_manifest_load": True,
                "tau_a": selected_config[0], "tau_m": selected_config[1],
                "selection_rule": "max equal-sequence/tracker mean IDF1, then fewer false links, lower runtime, lower thresholds",
                "development_manifest_sha256": sha256(args.development_manifest),
            })

    write_csv(args.output_dir / "hybrid_results_per_sequence.csv", sequence_rows)
    write_csv(args.output_dir / "hybrid_results_aggregate.csv", aggregate_rows)
    write_csv(args.output_dir / "verification_features.csv", feature_rows)
    write_csv(args.output_dir / "accepted_link_audit.csv", link_rows)
    write_csv(args.output_dir / "m3ot_direct_crop_diagnostic.csv", crop_rows)
    write_csv(args.output_dir / "candidate_recall.csv", candidate_rows)
    write_csv(args.output_dir / "runtime_breakdown.csv", runtime_rows)
    manifest = {
        "status": "COMPLETE",
        "selected_config": {"tau_a": selected_config[0], "tau_m": selected_config[1]},
        "claim_scope": "M3OT oracle-box tracker input with direct tracker-box ReID crops; held-out is exposed exploratory retest",
        "ground_truth_use": "oracle tracker inputs, trajectory metrics, and post-hoc link labels only; never crop admission or verifier",
        "development_grid": {"tau_a": list(TAU_A), "tau_m": list(TAU_M)},
        "checkpoint": checkpoint_manifest,
        "inputs": {
            str(path): sha256(path) for path in (
                args.development_manifest, args.held_out_manifest, args.checkpoint,
                args.diagnostic_script, args.ace_core,
                args.workspace / "scripts/run_m3ot_ambiguity_aware.py",
            )
        },
        "runtime_seconds": time.perf_counter() - started_all,
        "environment": {
            "python": sys.version, "torch": torch.__version__,
            "device": str(device), "threads": args.threads,
            "cuda_available": torch.cuda.is_available(),
        },
        "outputs": {},
    }
    for path in sorted(args.output_dir.iterdir()):
        if path.is_file() and path.name != "manifest.json":
            manifest["outputs"][path.name] = {
                "bytes": path.stat().st_size, "sha256": sha256(path),
            }
    write_json(args.output_dir / "manifest.json", manifest)
    print(json.dumps({
        "status": manifest["status"], "selected_config": manifest["selected_config"],
        "runtime_seconds": manifest["runtime_seconds"],
        "sequence_rows": len(sequence_rows), "feature_rows": len(feature_rows),
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
