#!/usr/bin/env python3
"""Explain fixed-policy M3OT transfer with cached protocol and fresh diagnostics.

The historical tracker inputs, descriptor construction, and thresholds are
replayed unchanged. Ground truth is used for the oracle-box tracker protocol,
evaluation, and post-hoc link labels. No threshold is tuned on held-out data.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import json
import math
import platform
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import numpy as np
import torch
from scipy.optimize import linear_sum_assignment


MAX_GAP = 30
GEOMETRY_RADIUS = 55.0
APPEARANCE_DISTANCE = 0.30
UNMATCHED_COST = 1.0
METHODS = (
    "no_refinement",
    "historical_geometry_first_reciprocal",
    "controlled_cost_greedy",
    "controlled_cost_reciprocal",
    "controlled_cost_partial_hungarian",
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
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )


def write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = sorted({key for row in rows for key in row})
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def tracklets(predictions: dict[int, list[dict]]):
    frames: dict[int, set[int]] = defaultdict(set)
    rows: dict[int, list[tuple[int, dict]]] = defaultdict(list)
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


def complete_temporal_edges(predictions: dict, descriptors: dict) -> list[dict]:
    frames, rows = tracklets(predictions)
    identities = sorted(frames)
    output = []
    for index, left in enumerate(identities):
        for right in identities[index + 1:]:
            if frames[left] & frames[right]:
                continue
            if max(frames[left]) < min(frames[right]):
                earlier, later = left, right
            elif max(frames[right]) < min(frames[left]):
                earlier, later = right, left
            else:
                continue
            gap = min(frames[later]) - max(frames[earlier])
            if gap > MAX_GAP:
                continue
            first = rows[earlier][-1][1]
            second = rows[later][0][1]
            first_center = np.asarray(
                [first["x"] + first["w"] / 2, first["y"] + first["h"] / 2],
                dtype=float,
            )
            second_center = np.asarray(
                [second["x"] + second["w"] / 2, second["y"] + second["h"] / 2],
                dtype=float,
            )
            appearance = None
            if earlier in descriptors and later in descriptors:
                appearance = float(1.0 - np.dot(descriptors[earlier], descriptors[later]))
            geometry = float(np.linalg.norm(first_center - second_center))
            output.append({
                "earlier": earlier,
                "later": later,
                "gap": int(gap),
                "endpoint_center_distance_pixels": geometry,
                "cosine_distance": appearance,
                "controlled_cost": (
                    (geometry / GEOMETRY_RADIUS + appearance / APPEARANCE_DISTANCE + gap / MAX_GAP) / 3
                    if appearance is not None else None
                ),
            })
    return output


def fixed_gated(edges: list[dict]) -> list[dict]:
    return [
        edge for edge in edges
        if edge["cosine_distance"] is not None
        and edge["cosine_distance"] <= APPEARANCE_DISTANCE
        and edge["endpoint_center_distance_pixels"] <= GEOMETRY_RADIUS
        and edge["controlled_cost"] < UNMATCHED_COST
    ]


def reciprocal(edges: list[dict], key) -> list[dict]:
    outgoing = defaultdict(list)
    incoming = defaultdict(list)
    for edge in edges:
        outgoing[edge["earlier"]].append(edge)
        incoming[edge["later"]].append(edge)
    best_out = {identity: min(values, key=key) for identity, values in outgoing.items()}
    best_in = {identity: min(values, key=key) for identity, values in incoming.items()}
    return [
        edge for edge in edges
        if best_out[edge["earlier"]] is edge and best_in[edge["later"]] is edge
    ]


def partial_hungarian(edges: list[dict]) -> list[dict]:
    if not edges:
        return []
    sources = sorted({edge["earlier"] for edge in edges})
    destinations = sorted({edge["later"] for edge in edges})
    source_index = {identity: index for index, identity in enumerate(sources)}
    destination_index = {identity: index for index, identity in enumerate(destinations)}
    matrix = np.full((len(sources), len(destinations) + len(sources)), 1e6, dtype=float)
    lookup = {}
    for edge in edges:
        row = source_index[edge["earlier"]]
        column = destination_index[edge["later"]]
        if edge["controlled_cost"] < matrix[row, column]:
            matrix[row, column] = edge["controlled_cost"]
            lookup[(row, column)] = edge
    for row in range(len(sources)):
        matrix[row, len(destinations) + row] = UNMATCHED_COST
    rr, cc = linear_sum_assignment(matrix)
    return [
        lookup[(row, column)]
        for row, column in zip(rr, cc)
        if column < len(destinations) and matrix[row, column] < UNMATCHED_COST
    ]


def apply_edges(predictions: dict, proposed: list[dict], key):
    frames, _ = tracklets(predictions)
    parent = {identity: identity for identity in frames}
    support = {identity: set(values) for identity, values in frames.items()}

    def find(identity: int) -> int:
        while parent[identity] != identity:
            parent[identity] = parent[parent[identity]]
            identity = parent[identity]
        return identity

    accepted = []
    rejected = []
    for edge in sorted(proposed, key=key):
        source = find(edge["earlier"])
        destination = find(edge["later"])
        if source == destination:
            continue
        overlap = support[source] & support[destination]
        if overlap:
            rejected.append({**edge, "rejection": "component_frame_overlap"})
            continue
        parent[destination] = source
        support[source] |= support[destination]
        accepted.append(edge)
    remapped = defaultdict(list)
    for frame, rows in predictions.items():
        remapped[frame] = [{**row, "id": find(int(row["id"]))} for row in rows]
    return dict(remapped), accepted, rejected


def choose_method(module, method: str, predictions: dict, descriptors: dict, edges: list[dict]):
    if method == "no_refinement":
        return predictions, [], []
    gated = fixed_gated(edges)
    cost_key = lambda edge: (
        edge["controlled_cost"], edge["gap"], edge["earlier"], edge["later"]
    )
    if method == "controlled_cost_greedy":
        proposed = gated
    elif method == "controlled_cost_reciprocal":
        proposed = reciprocal(gated, cost_key)
    elif method == "controlled_cost_partial_hungarian":
        proposed = partial_hungarian(gated)
    else:
        raise ValueError(method)
    return apply_edges(predictions, proposed, cost_key)


def edge_relation(edge: dict, labels: dict[int, dict]) -> str:
    left = labels.get(edge["earlier"])
    right = labels.get(edge["later"])
    if left is None or right is None:
        return "unknown"
    return (
        "same_identity"
        if left["majority_gt_identity"] == right["majority_gt_identity"]
        else "different_identity"
    )


def summarize_split(rows: list[dict]) -> list[dict]:
    grouped = defaultdict(list)
    for row in rows:
        grouped[(row["split"], row["tracker"], row["method"])].append(row)
    output = []
    for (split, tracker, method), selected in sorted(grouped.items()):
        output.append({
            "split": split,
            "tracker": tracker,
            "method": method,
            "sequence_count": len(selected),
            "aggregation": "equal_sequence_mean_metrics_total_IDSW",
            **{
                key: float(np.mean([row[key] for row in selected]))
                for key in ("HOTA", "AssA", "DetA", "IDF1", "MOTA")
            },
            "IDSW": int(sum(row["IDSW"] for row in selected)),
            "accepted_correct": int(sum(row["accepted_correct"] for row in selected)),
            "accepted_false": int(sum(row["accepted_false"] for row in selected)),
            "accepted_unknown": int(sum(row["accepted_unknown"] for row in selected)),
        })
    return output


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workspace", type=Path, required=True)
    parser.add_argument("--val-manifest", type=Path, required=True)
    parser.add_argument("--val-results", type=Path, required=True)
    parser.add_argument("--test-manifest", type=Path, required=True)
    parser.add_argument("--test-results", type=Path, required=True)
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--threads", type=int, default=8)
    args = parser.parse_args()
    if args.output_dir.exists() and any(args.output_dir.iterdir()):
        raise SystemExit(f"refusing to overwrite non-empty output directory: {args.output_dir}")
    args.output_dir.mkdir(parents=True, exist_ok=True)

    torch.set_num_threads(args.threads)
    module = load_module(
        "professor_review_m3ot", args.workspace / "scripts/run_m3ot_ambiguity_aware.py"
    )
    device = torch.device(args.device)
    model, checkpoint_manifest = module.REID.load_reid(args.checkpoint, device)
    model.eval()
    inputs = (
        ("development", args.val_manifest, args.val_results),
        ("held_out", args.test_manifest, args.test_results),
    )
    sequence_rows = []
    casebook_rows = []
    reproduction_rows = []
    descriptor_rows = []
    started_all = time.perf_counter()

    for split, manifest_path, result_path in inputs:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        stored = json.loads(result_path.read_text(encoding="utf-8"))
        stored_sequences = {row["sequence"]: row["methods"] for row in stored["sequence_results"]}
        root = Path(manifest["data_root"])
        for sequence in manifest["sequences"]:
            name = sequence["sequence_relative_path"]
            modality = sequence["tags"][0]
            print(f"{split} {name}", flush=True)
            gt = module.COMMON.parse_gt(root / sequence["gt_relative_path"])
            image_dir = root / sequence["img_relative_path"]
            shape = module.COMMON.image_shape(image_dir)
            diagonal = math.hypot(shape[1], shape[0])
            images = module.BASE.frame_images(image_dir)
            for tracker in ("bytetrack", "ocsort"):
                predictions = module.COMMON.run_sequence(tracker, gt, shape)
                observations = module.BASE.attach_observations(gt, predictions, images)
                descriptor_started = time.perf_counter()
                descriptors = module.BASE.extract_tracklet_descriptors(
                    observations, model, device
                )
                descriptor_seconds = time.perf_counter() - descriptor_started
                descriptor_path = (
                    args.output_dir / "descriptors" / split /
                    name.replace("/", "__") / f"{tracker}.npz"
                )
                descriptor_path.parent.mkdir(parents=True, exist_ok=True)
                np.savez_compressed(
                    descriptor_path,
                    **{str(identity): value for identity, value in descriptors.items()},
                )
                descriptor_rows.append({
                    "split": split,
                    "sequence": name,
                    "modality": modality,
                    "tracker": tracker,
                    "descriptor_count": len(descriptors),
                    "descriptor_seconds_cpu": descriptor_seconds,
                    "descriptor_path": str(descriptor_path),
                    "descriptor_sha256": sha256(descriptor_path),
                })
                labels = module.tracklet_gt_labels(gt, predictions)
                frames, tracklet_rows = tracklets(predictions)
                edges = complete_temporal_edges(predictions, descriptors)
                gated = fixed_gated(edges)
                geo_key = lambda edge: (
                    edge["endpoint_center_distance_pixels"], edge["cosine_distance"],
                    edge["gap"], edge["earlier"], edge["later"],
                )
                cost_key = lambda edge: (
                    edge["controlled_cost"], edge["gap"],
                    edge["earlier"], edge["later"],
                )
                historical_proposed = reciprocal(gated, geo_key)
                historical_output, historical_accepted, historical_rejected = apply_edges(
                    predictions, historical_proposed, lambda edge: (
                        edge["cosine_distance"], edge["gap"],
                        edge["earlier"], edge["later"],
                    )
                )
                method_outputs = {
                    "no_refinement": (predictions, [], []),
                    "historical_geometry_first_reciprocal": (
                        historical_output, historical_accepted, historical_rejected
                    ),
                }
                for method in METHODS[2:]:
                    method_outputs[method] = choose_method(
                        module, method, predictions, descriptors, edges
                    )

                accepted_by_method = {
                    method: {(edge["earlier"], edge["later"]) for edge in values[1]}
                    for method, values in method_outputs.items()
                }
                outgoing = defaultdict(list)
                incoming = defaultdict(list)
                for edge in gated:
                    outgoing[edge["earlier"]].append(edge)
                    incoming[edge["later"]].append(edge)
                best_out = {
                    identity: min(values, key=geo_key) for identity, values in outgoing.items()
                }
                best_in = {
                    identity: min(values, key=geo_key) for identity, values in incoming.items()
                }
                edge_lookup = {(edge["earlier"], edge["later"]): edge for edge in edges}

                for source in sorted(frames):
                    for destination in sorted(frames):
                        if source == destination or source not in labels or destination not in labels:
                            continue
                        if labels[source]["majority_gt_identity"] != labels[destination]["majority_gt_identity"]:
                            continue
                        if frames[source] & frames[destination] or max(frames[source]) >= min(frames[destination]):
                            continue
                        gap = min(frames[destination]) - max(frames[source])
                        if gap > MAX_GAP:
                            continue
                        pair = (source, destination)
                        edge = edge_lookup.get(pair)
                        source_last = tracklet_rows[source][-1][1]
                        destination_first = tracklet_rows[destination][0][1]
                        if edge is None:
                            geometry = float(np.linalg.norm(np.asarray([
                                source_last["x"] + source_last["w"] / 2,
                                source_last["y"] + source_last["h"] / 2,
                            ]) - np.asarray([
                                destination_first["x"] + destination_first["w"] / 2,
                                destination_first["y"] + destination_first["h"] / 2,
                            ])))
                            appearance = None
                        else:
                            geometry = edge["endpoint_center_distance_pixels"]
                            appearance = edge["cosine_distance"]
                        enters = edge in gated if edge is not None else False
                        out_competitor = best_out.get(source)
                        in_competitor = best_in.get(destination)
                        if source not in descriptors or destination not in descriptors:
                            reason = "missing_descriptor"
                        elif appearance is None or appearance > APPEARANCE_DISTANCE:
                            reason = "appearance_gate"
                        elif geometry > GEOMETRY_RADIUS:
                            reason = "geometry_gate"
                        elif out_competitor is not edge:
                            reason = "lost_outgoing_rank"
                        elif in_competitor is not edge:
                            reason = "lost_incoming_rank"
                        elif pair in accepted_by_method["historical_geometry_first_reciprocal"]:
                            reason = "accepted"
                        else:
                            reason = "post_selection_rejection"
                        casebook_rows.append({
                            "row_type": "correct_fragment_opportunity",
                            "split": split,
                            "sequence": name,
                            "modality": modality,
                            "tracker": tracker,
                            "source_id": source,
                            "destination_id": destination,
                            "posthoc_gt_identity": labels[source]["majority_gt_identity"],
                            "source_majority_gt_identity": labels[source]["majority_gt_identity"],
                            "destination_majority_gt_identity": labels[destination]["majority_gt_identity"],
                            "source_gt_purity": labels[source]["purity"],
                            "destination_gt_purity": labels[destination]["purity"],
                            "gap": gap,
                            "geometry_pixels": geometry,
                            "geometry_normalized_by_gate": geometry / GEOMETRY_RADIUS,
                            "geometry_normalized_by_diagonal": geometry / diagonal,
                            "appearance_distance": appearance,
                            "controlled_cost": edge["controlled_cost"] if edge else None,
                            "source_crop_area_median_px2": median_area(tracklet_rows[source]),
                            "destination_crop_area_median_px2": median_area(tracklet_rows[destination]),
                            "enters_fixed_candidate_graph": enters,
                            "historical_decision": reason,
                            "outgoing_competitor_source": (
                                out_competitor["earlier"] if out_competitor else None
                            ),
                            "outgoing_competitor_destination": (
                                out_competitor["later"] if out_competitor else None
                            ),
                            "outgoing_competitor_gt_relation": (
                                edge_relation(out_competitor, labels) if out_competitor else None
                            ),
                            "outgoing_competitor_geometry_pixels": (
                                out_competitor["endpoint_center_distance_pixels"] if out_competitor else None
                            ),
                            "outgoing_competitor_appearance_distance": (
                                out_competitor["cosine_distance"] if out_competitor else None
                            ),
                            "incoming_competitor_source": (
                                in_competitor["earlier"] if in_competitor else None
                            ),
                            "incoming_competitor_destination": (
                                in_competitor["later"] if in_competitor else None
                            ),
                            "incoming_competitor_gt_relation": (
                                edge_relation(in_competitor, labels) if in_competitor else None
                            ),
                            **{
                                f"accepted_by_{method}": pair in accepted_by_method[method]
                                for method in METHODS[1:]
                            },
                        })

                for method, (output, accepted, rejected) in method_outputs.items():
                    counts = Counter(edge_relation(edge, labels) for edge in accepted)
                    metrics = module.COMMON.evaluate(module.COMMON.metric_data(gt, output))
                    sequence_rows.append({
                        "split": split,
                        "sequence": name,
                        "modality": modality,
                        "tracker": tracker,
                        "method": method,
                        **metrics,
                        "accepted_correct": counts["same_identity"],
                        "accepted_false": counts["different_identity"],
                        "accepted_unknown": counts["unknown"],
                        "component_rejections": len(rejected),
                    })
                    for edge in accepted:
                        if edge_relation(edge, labels) != "different_identity":
                            continue
                        source = edge["earlier"]
                        destination = edge["later"]
                        casebook_rows.append({
                            "row_type": "accepted_false_link",
                            "split": split,
                            "sequence": name,
                            "modality": modality,
                            "tracker": tracker,
                            "method": method,
                            "source_id": source,
                            "destination_id": destination,
                            "source_majority_gt_identity": labels.get(source, {}).get("majority_gt_identity"),
                            "destination_majority_gt_identity": labels.get(destination, {}).get("majority_gt_identity"),
                            "source_gt_purity": labels.get(source, {}).get("purity"),
                            "destination_gt_purity": labels.get(destination, {}).get("purity"),
                            "gap": edge["gap"],
                            "geometry_pixels": edge["endpoint_center_distance_pixels"],
                            "geometry_normalized_by_gate": (
                                edge["endpoint_center_distance_pixels"] / GEOMETRY_RADIUS
                            ),
                            "geometry_normalized_by_diagonal": edge["endpoint_center_distance_pixels"] / diagonal,
                            "appearance_distance": edge["cosine_distance"],
                            "controlled_cost": edge["controlled_cost"],
                            "source_crop_area_median_px2": median_area(tracklet_rows[source]),
                            "destination_crop_area_median_px2": median_area(tracklet_rows[destination]),
                        })

                stored_methods = stored_sequences[name]
                stored_baseline = stored_methods[tracker]
                stored_historical = stored_methods[f"{tracker}__geometry_reid_reciprocal"]
                observed_baseline = next(
                    row for row in sequence_rows
                    if row["split"] == split and row["sequence"] == name
                    and row["tracker"] == tracker and row["method"] == "no_refinement"
                )
                observed_historical = next(
                    row for row in sequence_rows
                    if row["split"] == split and row["sequence"] == name
                    and row["tracker"] == tracker
                    and row["method"] == "historical_geometry_first_reciprocal"
                )
                stored_pairs = {
                    (edge["earlier"], edge["later"])
                    for edge in stored_historical["graph"]["accepted_edges"]
                }
                observed_pairs = accepted_by_method["historical_geometry_first_reciprocal"]
                reproduction_rows.append({
                    "split": split,
                    "sequence": name,
                    "tracker": tracker,
                    "baseline_max_metric_abs_diff": max(
                        abs(float(observed_baseline[key]) - float(stored_baseline[key]))
                        for key in ("HOTA", "AssA", "DetA", "IDF1", "MOTA", "IDSW")
                    ),
                    "historical_max_metric_abs_diff": max(
                        abs(float(observed_historical[key]) - float(stored_historical[key]))
                        for key in ("HOTA", "AssA", "DetA", "IDF1", "MOTA", "IDSW")
                    ),
                    "accepted_edges_exact_match": stored_pairs == observed_pairs,
                    "stored_accepted_edges": len(stored_pairs),
                    "observed_accepted_edges": len(observed_pairs),
                })

    aggregate_rows = summarize_split(sequence_rows)
    write_csv(args.output_dir / "m3ot_linker_per_sequence.csv", sequence_rows)
    write_csv(args.output_dir / "m3ot_linker_comparison.csv", aggregate_rows)
    write_csv(args.output_dir / "m3ot_edge_casebook.csv", casebook_rows)
    write_csv(args.output_dir / "descriptor_runtime.csv", descriptor_rows)
    write_csv(args.output_dir / "reproduction_check.csv", reproduction_rows)

    reproduction_passed = all(
        row["baseline_max_metric_abs_diff"] <= 1e-10
        and row["historical_max_metric_abs_diff"] <= 1e-8
        and row["accepted_edges_exact_match"]
        for row in reproduction_rows
    )
    manifest = {
        "status": "COMPLETE" if reproduction_passed else "FAILED_REPRODUCTION_CHECK",
        "claim_scope": "Fixed M3OT development/held-out diagnostic; no retuning or dataset-specific exception",
        "methods": list(METHODS),
        "fixed_thresholds": {
            "maximum_gap_frames": MAX_GAP,
            "geometry_radius_pixels": GEOMETRY_RADIUS,
            "appearance_cosine_distance": APPEARANCE_DISTANCE,
            "partial_hungarian_unmatched_cost": UNMATCHED_COST,
        },
        "historical_descriptor_admission": (
            "Tracker observations with IoU >= 0.9 to oracle GT are attached to image "
            "crops before fixed BaseReID encoding; this reproduces the historical "
            "oracle-box diagnostic and is not a detector-input protocol."
        ),
        "configuration_selection": {
            "development": True,
            "held_out": False,
            "held_out_threshold_tuning": False,
        },
        "ground_truth_use": "oracle-box tracker input, descriptor crop admission, metrics, and post-hoc diagnostics",
        "inputs": {
            str(path): sha256(path)
            for path in (
                args.val_manifest, args.val_results,
                args.test_manifest, args.test_results, args.checkpoint,
                args.workspace / "scripts/run_m3ot_ambiguity_aware.py",
                args.workspace / "scripts/run_m3ot_temporal_evidence.py",
            )
        },
        "reproduction_passed": reproduction_passed,
        "reproduction_instances": len(reproduction_rows),
        "environment": {
            "python": sys.version,
            "executable": sys.executable,
            "platform": platform.platform(),
            "torch": torch.__version__,
            "device": str(device),
            "threads": args.threads,
        },
        "checkpoint": checkpoint_manifest,
        "runtime_seconds": time.perf_counter() - started_all,
        "command": " ".join(sys.argv),
        "script_sha256": sha256(Path(__file__)),
        "outputs": {},
    }
    for path in sorted(args.output_dir.iterdir()):
        if path.is_file() and path.name != "manifest.json":
            manifest["outputs"][path.name] = {
                "bytes": path.stat().st_size,
                "sha256": sha256(path),
            }
    write_json(args.output_dir / "manifest.json", manifest)
    print(json.dumps({
        "status": manifest["status"],
        "reproduction_passed": reproduction_passed,
        "sequence_rows": len(sequence_rows),
        "casebook_rows": len(casebook_rows),
        "runtime_seconds": manifest["runtime_seconds"],
    }, indent=2))
    return 0 if reproduction_passed else 2


if __name__ == "__main__":
    raise SystemExit(main())
