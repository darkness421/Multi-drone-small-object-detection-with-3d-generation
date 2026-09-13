#!/usr/bin/env python3
"""Run corrected-channel temporal linker comparisons on an MMOT release root.

Upstream tracker outputs are generated once, saved immutably, and then shared by
all refiners. Ground-truth identities are read only after predictions and
candidate links have been frozen, for metrics and post-hoc link auditing.
"""

from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import importlib.util
import json
import os
import sys
import time
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

import numpy as np
import torch
from PIL import Image
from scipy.optimize import linear_sum_assignment


CLASS_NAMES = ("car", "bike", "pedestrian", "van", "truck", "bus", "tricycle", "awning-bike")
MAX_GAP = 30
GEOMETRY_RADIUS = 55.0
APPEARANCE_DISTANCE = 0.30
AF_THR_T = (0, 30)
AF_THR_S = 75.0
AF_THR_P = 0.05
METHODS = (
    "no_refinement",
    "geometry_greedy",
    "geometry_reid_hungarian",
    "aflink_official",
    "com3d_reciprocal_guard",
)
ABLATIONS = (
    "no_refinement",
    "geometry_greedy",
    "geometry_reciprocal_guard",
    "geometry_reid_greedy_guard",
    "geometry_reid_reciprocal_no_guard",
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
        writer.writerows([{key: json_ready(row.get(key)) for key in fields} for row in rows])


def cuda_sync(device: torch.device) -> None:
    if device.type == "cuda":
        torch.cuda.synchronize(device)


def load_predictions(path: Path) -> dict[int, list[dict]]:
    frames = defaultdict(list)
    with gzip.open(path, "rt", encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            frames[int(row.pop("frame"))].append({
                key: value
                for key, value in row.items()
                if key not in {"family", "sequence", "class_name", "tracker"}
            })
    return frames


def save_predictions(path: Path, context: dict, predictions: dict[int, list[dict]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(path, "wt", encoding="utf-8", newline="") as handle:
        for frame in sorted(predictions):
            for row in predictions[frame]:
                handle.write(json.dumps({**context, "frame": frame, **json_ready(row)}, sort_keys=True) + "\n")


def load_descriptors(path: Path) -> dict[int, np.ndarray]:
    with np.load(path) as payload:
        return {int(key): payload[key] for key in payload.files}


def duplicate_frame_identity_count(predictions: dict[int, list[dict]]) -> int:
    result = 0
    for rows in predictions.values():
        counts = Counter(int(row["id"]) for row in rows)
        result += sum(count - 1 for count in counts.values() if count > 1)
    return result


def geometry_multiset(predictions: dict[int, list[dict]]) -> Counter:
    result = Counter()
    for frame, rows in predictions.items():
        for row in rows:
            result[(
                int(frame), round(float(row["x"]), 7), round(float(row["y"]), 7),
                round(float(row["w"]), 7), round(float(row["h"]), 7),
                round(float(row.get("conf", 1.0)), 7), int(row.get("class_id", -1)),
            )] += 1
    return result


def extended_metrics(common, data: dict) -> dict:
    result = common.evaluate(data)
    clear = common.CLEAR({"PRINT_CONFIG": False}).eval_sequence(data)
    result.update({
        "FP": int(clear["CLR_FP"]),
        "FN": int(clear["CLR_FN"]),
        "TP": int(clear["CLR_TP"]),
        "Frag": int(clear["Frag"]),
    })
    return result


def prediction_tracklets(predictions: dict[int, list[dict]]) -> tuple[dict[int, set[int]], dict[int, list[tuple[int, dict]]]]:
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


def build_candidates(predictions: dict[int, list[dict]], descriptors: dict[int, np.ndarray]) -> tuple[list[dict], set[int]]:
    frames, rows = prediction_tracklets(predictions)
    identities = sorted(frames)
    candidates = []
    eligible_sources = set()
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
            eligible_sources.add(earlier)
            earlier_row = rows[earlier][-1][1]
            later_row = rows[later][0][1]
            earlier_center = np.asarray([
                earlier_row["x"] + earlier_row["w"] / 2.0,
                earlier_row["y"] + earlier_row["h"] / 2.0,
            ], dtype=float)
            later_center = np.asarray([
                later_row["x"] + later_row["w"] / 2.0,
                later_row["y"] + later_row["h"] / 2.0,
            ], dtype=float)
            top_left_distance = float(np.linalg.norm(
                np.asarray([earlier_row["x"], earlier_row["y"]], dtype=float)
                - np.asarray([later_row["x"], later_row["y"]], dtype=float)
            ))
            appearance = None
            if earlier in descriptors and later in descriptors:
                appearance = float(1.0 - np.dot(descriptors[earlier], descriptors[later]))
            geometry = float(np.linalg.norm(earlier_center - later_center))
            candidates.append({
                "earlier": earlier,
                "later": later,
                "gap": int(gap),
                "endpoint_center_distance_pixels": geometry,
                "endpoint_top_left_distance_pixels": top_left_distance,
                "cosine_distance": appearance,
                "controlled_cost": (
                    (geometry / GEOMETRY_RADIUS + appearance / APPEARANCE_DISTANCE + gap / MAX_GAP) / 3.0
                    if appearance is not None else None
                ),
            })
    return candidates, eligible_sources


def reciprocal(edges: list[dict], use_appearance: bool) -> list[dict]:
    outgoing = defaultdict(list)
    incoming = defaultdict(list)
    for edge in edges:
        outgoing[edge["earlier"]].append(edge)
        incoming[edge["later"]].append(edge)

    def key(edge):
        return (
            edge["endpoint_center_distance_pixels"],
            edge["cosine_distance"] if use_appearance else 0.0,
            edge["gap"], edge["earlier"], edge["later"],
        )

    best_out = {identity: min(values, key=key) for identity, values in outgoing.items()}
    best_in = {identity: min(values, key=key) for identity, values in incoming.items()}
    return [
        edge for edge in edges
        if best_out[edge["earlier"]] is edge and best_in[edge["later"]] is edge
    ]


def hungarian_with_unmatched(edges: list[dict], unmatched_cost: float = 1.0) -> list[dict]:
    valid = [
        edge for edge in edges
        if edge["cosine_distance"] is not None
        and edge["endpoint_center_distance_pixels"] <= GEOMETRY_RADIUS
        and edge["cosine_distance"] <= APPEARANCE_DISTANCE
        and edge["controlled_cost"] < unmatched_cost
    ]
    if not valid:
        return []
    sources = sorted({edge["earlier"] for edge in valid})
    destinations = sorted({edge["later"] for edge in valid})
    row_index = {value: index for index, value in enumerate(sources)}
    col_index = {value: index for index, value in enumerate(destinations)}
    matrix = np.full((len(sources), len(destinations) + len(sources)), 1e6, dtype=float)
    lookup = {}
    for edge in valid:
        row = row_index[edge["earlier"]]
        column = col_index[edge["later"]]
        key = (edge["controlled_cost"], edge["gap"], edge["earlier"], edge["later"])
        existing = lookup.get((row, column))
        if existing is None or key < existing[0]:
            matrix[row, column] = edge["controlled_cost"]
            lookup[(row, column)] = (key, edge)
    for row in range(len(sources)):
        matrix[row, len(destinations) + row] = unmatched_cost
    rr, cc = linear_sum_assignment(matrix)
    selected = []
    for row, column in zip(rr, cc):
        if column < len(destinations) and matrix[row, column] < unmatched_cost:
            selected.append(lookup[(row, column)][1])
    return selected


def apply_union_edges(predictions: dict[int, list[dict]], proposed: list[dict], component_guard: bool, sort_key) -> tuple[dict, list[dict], list[dict]]:
    frames, _ = prediction_tracklets(predictions)
    parent = {identity: identity for identity in frames}
    component_frames = {identity: set(values) for identity, values in frames.items()}

    def find(identity: int) -> int:
        while parent[identity] != identity:
            parent[identity] = parent[parent[identity]]
            identity = parent[identity]
        return identity

    accepted = []
    rejected = []
    for edge in sorted(proposed, key=sort_key):
        earlier_root = find(edge["earlier"])
        later_root = find(edge["later"])
        if earlier_root == later_root:
            continue
        overlap = component_frames[earlier_root] & component_frames[later_root]
        if overlap and component_guard:
            rejected.append({**edge, "rejection": "component_frame_overlap", "overlap_frames": sorted(overlap)})
            continue
        parent[later_root] = earlier_root
        component_frames[earlier_root] |= component_frames[later_root]
        accepted.append(dict(edge))
    remapped = defaultdict(list)
    for frame, rows in predictions.items():
        remapped[frame] = [{**row, "id": find(int(row["id"]))} for row in rows]
    return remapped, accepted, rejected


def apply_aflink_mapping(predictions: dict[int, list[dict]], selected: list[dict]) -> tuple[dict, list[dict], list[dict]]:
    # Preserve the official implementation's ordered ID2ID construction.
    temporary = {}
    final = {}
    for edge in sorted(selected, key=lambda item: (item["earlier"], item["later"])):
        temporary[edge["earlier"]] = edge["later"]
    for source, destination in temporary.items():
        final[destination] = final[source] if source in final else source
    remapped = defaultdict(list)
    for frame, rows in predictions.items():
        remapped[frame] = [{**row, "id": int(final.get(int(row["id"]), int(row["id"])))} for row in rows]
    return remapped, [dict(edge) for edge in selected], []


def edge_audit(edges: list[dict], labels: dict[int, dict]) -> tuple[list[dict], Counter]:
    rows = []
    counts = Counter()
    for edge in edges:
        left = labels.get(edge["earlier"])
        right = labels.get(edge["later"])
        row = dict(edge)
        if left is None or right is None:
            correctness = "unknown"
        else:
            correctness = "correct" if left["majority_gt_identity"] == right["majority_gt_identity"] else "false"
            row.update({
                "source_majority_gt_identity": left["majority_gt_identity"],
                "destination_majority_gt_identity": right["majority_gt_identity"],
                "source_gt_purity": left["purity"],
                "destination_gt_purity": right["purity"],
            })
        row["posthoc_gt_correctness"] = correctness
        counts[correctness] += 1
        rows.append(row)
    return rows, counts


def area_bin(area: float) -> str:
    if area < 32.0 ** 2:
        return "tiny_lt_32sq"
    if area < 96.0 ** 2:
        return "small_32sq_to_96sq"
    return "larger_ge_96sq"


def tracklet_areas(predictions: dict[int, list[dict]]) -> dict[int, float]:
    values = defaultdict(list)
    for rows in predictions.values():
        for row in rows:
            values[int(row["id"])].append(float(row["w"]) * float(row["h"]))
    return {identity: float(np.median(areas)) for identity, areas in values.items()}


def corrected_crop(image_path: Path, bbox: tuple[int, int, int, int]) -> torch.Tensor:
    array = np.load(image_path, mmap_mode="r")
    rgb = np.ascontiguousarray(array[:, :, [4, 2, 1]])
    height, width = rgb.shape[:2]
    x1, y1, x2, y2 = bbox
    x1, y1 = max(0, x1), max(0, y1)
    x2, y2 = min(width, x2 + 1), min(height, y2 + 1)
    if x2 <= x1 or y2 <= y1:
        raise RuntimeError(f"empty corrected MMOT crop: {image_path} {bbox}")
    crop = np.ascontiguousarray(rgb[y1:y2, x1:x2])
    image = Image.fromarray(crop, mode="RGB").resize((128, 256), Image.Resampling.BILINEAR)
    values = np.asarray(image, dtype=np.float32).copy()
    tensor = torch.from_numpy(values).permute(2, 0, 1)
    mean = torch.tensor([123.675, 116.28, 103.53])[:, None, None]
    std = torch.tensor([58.395, 57.12, 57.375])[:, None, None]
    return (tensor - mean) / std


def extract_descriptors(predictions: dict, image_map: dict[int, Path], model, device: torch.device, batch_size: int) -> tuple[dict[int, np.ndarray], dict]:
    _, tracklet_rows = prediction_tracklets(predictions)
    work = []
    for identity, rows in sorted(tracklet_rows.items()):
        selected = rows if len(rows) <= 3 else [rows[0], rows[len(rows) // 2], rows[-1]]
        for frame, row in selected:
            if frame not in image_map:
                continue
            work.append((identity, image_map[frame], (
                int(round(row["x"])), int(round(row["y"])),
                int(round(row["x"] + row["w"])), int(round(row["y"] + row["h"])),
            )))
    features = defaultdict(list)
    rejected_invalid_crops = 0
    started = time.perf_counter()
    cuda_sync(device)
    with torch.inference_mode():
        for begin in range(0, len(work), batch_size):
            batch_items = work[begin:begin + batch_size]
            tensors = []
            admitted = []
            for identity, image_path, bbox in batch_items:
                try:
                    tensors.append(corrected_crop(image_path, bbox))
                    admitted.append(identity)
                except RuntimeError:
                    rejected_invalid_crops += 1
            if not tensors:
                continue
            batch = torch.stack(tensors).to(device)
            output = model(batch).detach().float().cpu().numpy()
            norms = np.linalg.norm(output, axis=1, keepdims=True)
            if not np.isfinite(output).all() or np.any(norms <= 0):
                raise RuntimeError("non-finite corrected ReID feature")
            output = output / norms
            for identity, feature in zip(admitted, output):
                features[identity].append(feature)
            del batch, output
    cuda_sync(device)
    elapsed = time.perf_counter() - started
    descriptors = {}
    for identity, rows in features.items():
        mean = np.mean(rows, axis=0)
        norm = np.linalg.norm(mean)
        if np.isfinite(mean).all() and norm > 0:
            descriptors[identity] = (mean / norm).astype(np.float32)
    return descriptors, {
        "tracklets_with_eligible_observations": len(features),
        "sampled_crops": len(work) - rejected_invalid_crops,
        "rejected_invalid_crops": rejected_invalid_crops,
        "descriptors": len(descriptors),
        "runtime_seconds": elapsed,
        "device": str(device),
        "batch_size": batch_size,
        "channel_policy": "HWC zero-based [4,2,1] as RGB",
        "crop_admission": "Direct tracker output boxes; no GT matching or GT identity.",
    }


@dataclass
class AFLinkRuntime:
    model: Any
    dataset: Any
    device: torch.device

    def scores(self, pairs: list[tuple[np.ndarray, np.ndarray]], batch_size: int) -> np.ndarray:
        if not pairs:
            return np.empty((0,), dtype=np.float32)
        values = []
        with torch.inference_mode():
            for begin in range(0, len(pairs), batch_size):
                batch_pairs = pairs[begin:begin + batch_size]
                left = []
                right = []
                for first, second in batch_pairs:
                    transformed_left, transformed_right = self.dataset.transform(first, second)
                    left.append(transformed_left)
                    right.append(transformed_right)
                output = self.model(torch.stack(left).to(self.device), torch.stack(right).to(self.device))
                values.append(output[:, 1].detach().float().cpu().numpy())
        return np.concatenate(values)


def load_aflink(root: Path, checkpoint: Path, device: torch.device) -> tuple[AFLinkRuntime, dict]:
    sys.path.insert(0, str(root))
    from AFLink.dataset import LinkData
    from AFLink.model import PostLinker

    model = PostLinker()
    payload = torch.load(checkpoint, map_location="cpu", weights_only=False)
    model.load_state_dict(payload)
    model.eval().to(device)
    dataset = LinkData("", "")
    return AFLinkRuntime(model=model, dataset=dataset, device=device), {
        "repository": "https://github.com/dyhBUPT/StrongSORT",
        "repository_commit": os.popen(f"git -C {root} rev-parse HEAD").read().strip(),
        "checkpoint": str(checkpoint),
        "checkpoint_sha256": sha256(checkpoint),
        "checkpoint_source": "official StrongSORT Google Drive file AFLink_epoch20.pth",
        "gates": {"thrT": list(AF_THR_T), "thrS": AF_THR_S, "thrP": AF_THR_P},
        "target_adaptation": False,
    }


def aflink_select(runtime: AFLinkRuntime, predictions: dict[int, list[dict]], batch_size: int) -> tuple[list[dict], dict]:
    frames, rows = prediction_tracklets(predictions)
    identities = sorted(frames)
    candidates = []
    pairs = []
    for source in identities:
        source_track = np.asarray([
            [frame, row["x"], row["y"], row["w"], row["h"]]
            for frame, row in rows[source]
        ], dtype=np.float32)
        fi, xi, yi = source_track[-1, :3]
        for destination in identities:
            if source == destination:
                continue
            destination_track = np.asarray([
                [frame, row["x"], row["y"], row["w"], row["h"]]
                for frame, row in rows[destination]
            ], dtype=np.float32)
            fj, xj, yj = destination_track[0, :3]
            gap = float(fj - fi)
            spatial = float(np.hypot(xi - xj, yi - yj))
            if not (AF_THR_T[0] <= gap < AF_THR_T[1]) or spatial > AF_THR_S:
                continue
            candidates.append({
                "earlier": source,
                "later": destination,
                "gap": int(gap),
                "endpoint_top_left_distance_pixels": spatial,
            })
            pairs.append((source_track, destination_track))
    started = time.perf_counter()
    cuda_sync(runtime.device)
    probabilities = runtime.scores(pairs, batch_size=batch_size)
    cuda_sync(runtime.device)
    model_seconds = time.perf_counter() - started
    for edge, probability in zip(candidates, probabilities):
        edge["aflink_probability"] = float(probability)
        edge["aflink_cost"] = float(1.0 - probability)
    valid = [edge for edge in candidates if edge["aflink_cost"] <= AF_THR_P]
    if not valid:
        return [], {"candidate_edges": len(candidates), "gated_edges": 0, "model_runtime_seconds": model_seconds}
    sources = np.asarray(identities)
    index = {identity: idx for idx, identity in enumerate(identities)}
    matrix = np.full((len(identities), len(identities)), 1e5, dtype=float)
    lookup = {}
    for edge in valid:
        row = index[edge["earlier"]]
        column = index[edge["later"]]
        if edge["aflink_cost"] < matrix[row, column]:
            matrix[row, column] = edge["aflink_cost"]
            lookup[(row, column)] = edge
    mask_row = matrix.min(axis=1) < AF_THR_P
    mask_col = matrix.min(axis=0) < AF_THR_P
    compressed = matrix[mask_row][:, mask_col]
    row_ids = sources[mask_row]
    col_ids = sources[mask_col]
    rr, cc = linear_sum_assignment(compressed)
    selected = []
    for row, column in zip(rr, cc):
        if compressed[row, column] < AF_THR_P:
            selected.append(lookup[(index[int(row_ids[row])], index[int(col_ids[column])])])
    return selected, {
        "candidate_edges": len(candidates),
        "gated_edges": len(valid),
        "selected_edges": len(selected),
        "model_runtime_seconds": model_seconds,
    }


def method_output(method: str, predictions: dict, candidates: list[dict], af_runtime: AFLinkRuntime, af_batch_size: int) -> tuple[dict, list[dict], list[dict], dict]:
    if method == "no_refinement":
        return predictions, [], [], {"candidate_edges": 0}
    if method == "geometry_greedy":
        proposed = [edge for edge in candidates if edge["endpoint_center_distance_pixels"] <= GEOMETRY_RADIUS]
        output, accepted, rejected = apply_union_edges(
            predictions, proposed, True,
            lambda edge: (edge["endpoint_center_distance_pixels"], edge["gap"], edge["earlier"], edge["later"]),
        )
        return output, accepted, rejected, {"candidate_edges": len(proposed)}
    if method == "geometry_reciprocal_guard":
        gated = [edge for edge in candidates if edge["endpoint_center_distance_pixels"] <= GEOMETRY_RADIUS]
        proposed = reciprocal(gated, use_appearance=False)
        output, accepted, rejected = apply_union_edges(
            predictions, proposed, True,
            lambda edge: (edge["endpoint_center_distance_pixels"], edge["gap"], edge["earlier"], edge["later"]),
        )
        return output, accepted, rejected, {"candidate_edges": len(gated), "proposed_edges": len(proposed)}
    if method == "geometry_reid_greedy_guard":
        proposed = [
            edge for edge in candidates
            if edge["cosine_distance"] is not None
            and edge["endpoint_center_distance_pixels"] <= GEOMETRY_RADIUS
            and edge["cosine_distance"] <= APPEARANCE_DISTANCE
        ]
        output, accepted, rejected = apply_union_edges(
            predictions, proposed, True,
            lambda edge: (edge["cosine_distance"], edge["gap"], edge["earlier"], edge["later"]),
        )
        return output, accepted, rejected, {"candidate_edges": len(proposed)}
    if method == "geometry_reid_hungarian":
        proposed = hungarian_with_unmatched(candidates)
        output, accepted, rejected = apply_union_edges(
            predictions, proposed, True,
            lambda edge: (edge["controlled_cost"], edge["gap"], edge["earlier"], edge["later"]),
        )
        return output, accepted, rejected, {"candidate_edges": len([e for e in candidates if e["controlled_cost"] is not None]), "proposed_edges": len(proposed), "unmatched_cost": 1.0}
    if method == "geometry_reid_reciprocal_no_guard" or method == "com3d_reciprocal_guard":
        gated = [
            edge for edge in candidates
            if edge["cosine_distance"] is not None
            and edge["endpoint_center_distance_pixels"] <= GEOMETRY_RADIUS
            and edge["cosine_distance"] <= APPEARANCE_DISTANCE
        ]
        proposed = reciprocal(gated, use_appearance=True)
        output, accepted, rejected = apply_union_edges(
            predictions, proposed, method == "com3d_reciprocal_guard",
            lambda edge: (edge["cosine_distance"], edge["gap"], edge["earlier"], edge["later"]),
        )
        return output, accepted, rejected, {"candidate_edges": len(gated), "proposed_edges": len(proposed)}
    if method == "aflink_official":
        proposed, details = aflink_select(af_runtime, predictions, af_batch_size)
        output, accepted, rejected = apply_aflink_mapping(predictions, proposed)
        return output, accepted, rejected, details
    raise ValueError(method)


def corrected_deepocsort(mmot, gt: dict, image_map: dict[int, Path], model, device: torch.device, batch_size: int) -> dict[int, list[dict]]:
    from boxmot.trackers.registry import create_tracker, get_tracker_config

    tracker = create_tracker(
        "deepocsort",
        tracker_config=get_tracker_config("deepocsort"),
        precomputed_reid=True,
        device=str(device),
        half=False,
        per_class=False,
    )
    predictions = defaultdict(list)
    mean = torch.tensor([123.675, 116.28, 103.53])[:, None, None]
    std = torch.tensor([58.395, 57.12, 57.375])[:, None, None]
    for frame in range(1, max(gt, default=0) + 1):
        rows = gt.get(frame, [])
        array = np.load(image_map[frame], mmap_mode="r")
        image_rgb = np.ascontiguousarray(array[:, :, [4, 2, 1]])
        image_bgr = np.ascontiguousarray(array[:, :, [1, 2, 4]])
        tensors = []
        height, width = image_rgb.shape[:2]
        for row in rows:
            x1, y1 = max(0, int(row["x"])), max(0, int(row["y"]))
            x2 = min(width, int(round(row["x"] + row["w"])) + 1)
            y2 = min(height, int(round(row["y"] + row["h"])) + 1)
            crop = Image.fromarray(np.ascontiguousarray(image_rgb[y1:y2, x1:x2]), mode="RGB").resize((128, 256), Image.Resampling.BILINEAR)
            tensor = torch.from_numpy(np.asarray(crop, dtype=np.float32).copy()).permute(2, 0, 1)
            tensors.append((tensor - mean) / std)
        if tensors:
            embeddings_parts = []
            with torch.inference_mode():
                for begin in range(0, len(tensors), batch_size):
                    batch = torch.stack(tensors[begin:begin + batch_size]).to(device)
                    embeddings_parts.append(model(batch).detach().float().cpu().numpy())
            embeddings = np.concatenate(embeddings_parts)
            embeddings /= np.linalg.norm(embeddings, axis=1, keepdims=True)
        else:
            embeddings = np.empty((0, 128), dtype=np.float32)
        detections = np.asarray([
            [row["x"], row["y"], row["x"] + row["w"], row["y"] + row["h"], 1.0, row["class_id"]]
            for row in rows
        ], dtype=np.float32).reshape(-1, 6)
        outputs = tracker.update(detections, image_bgr, embeddings)
        for output in outputs:
            x1, y1, x2, y2, identity, confidence, class_id = output[:7]
            predictions[frame].append({
                "id": int(identity), "x": float(x1), "y": float(y1),
                "w": float(x2 - x1), "h": float(y2 - y1),
                "conf": float(confidence), "class_id": int(class_id), "visibility": 1.0,
            })
    return predictions


def summarize_records(common, records: list[dict], families: list[str], trackers: list[str], methods: Iterable[str], include_pooled: bool = True) -> tuple[list[dict], list[dict]]:
    sequence_rows = []
    by_sequence = defaultdict(list)
    for record in records:
        by_sequence[(record["family"], record["sequence"], record["tracker"], record["method"])].append(record)
    for (family, sequence, tracker, method), grouped_records in sorted(by_sequence.items()):
        invalid = [row for row in grouped_records if not row["valid_output"]]
        base = {
            "family": family, "sequence": sequence, "tracker": tracker, "method": method,
            "valid_output": not invalid, "invalid_class_instances": len(invalid),
        }
        if invalid:
            sequence_rows.append(base)
            continue
        metrics = extended_metrics(
            common,
            common_module_concatenate(common, [row["metric_data"] for row in grouped_records]),
        )
        sequence_rows.append({**base, **metrics})

    aggregate_rows = []
    for tracker in trackers:
        for method in methods:
            selected_all = [row for row in records if row["tracker"] == tracker and row["method"] == method]
            if not selected_all:
                continue
            groups = [("all_sequences", selected_all)]
            groups.extend((family, [row for row in selected_all if row["family"] == family]) for family in families)
            for scope, selected in groups:
                if not selected:
                    continue
                scope_sequences = [
                    row for row in sequence_rows
                    if row["tracker"] == tracker and row["method"] == method
                    and (scope == "all_sequences" or row["family"] == scope)
                ]
                invalid = [row for row in selected if not row["valid_output"]]
                base = {
                    "scope": scope, "tracker": tracker, "method": method,
                    "sequence_count": len(scope_sequences),
                    "valid_output": not invalid,
                    "invalid_class_instances": len(invalid),
                    "invalid_sequences": sum(not row["valid_output"] for row in scope_sequences),
                }
                if invalid:
                    aggregations = ["equal_sequence_mean_metrics_total_counts"]
                    if include_pooled:
                        aggregations.insert(0, "pooled_detections")
                    for aggregation in aggregations:
                        aggregate_rows.append({**base, "aggregation": aggregation})
                    continue
                if include_pooled:
                    pooled = extended_metrics(common, common_module_concatenate(common, [row["metric_data"] for row in selected]))
                    aggregate_rows.append({
                        **base, "aggregation": "pooled_detections", **pooled,
                    })
                equal = {
                    key: float(np.mean([row[key] for row in scope_sequences]))
                    for key in ("HOTA", "AssA", "DetA", "IDF1", "MOTA")
                }
                equal.update({key: int(sum(row[key] for row in scope_sequences)) for key in ("IDSW", "FP", "FN", "TP", "Frag", "valid_gt_boxes", "predicted_boxes")})
                aggregate_rows.append({
                    **base, "aggregation": "equal_sequence_mean_metrics_total_counts", **equal,
                })
    return sequence_rows, aggregate_rows


def common_module_concatenate(common, items: list[dict]) -> dict:
    # The historical helper lives one import level above COMMON.
    gt_offset = tracker_offset = 0
    output = {
        "num_timesteps": 0, "num_gt_ids": 0, "num_tracker_ids": 0,
        "num_gt_dets": 0, "num_tracker_dets": 0,
        "gt_ids": [], "tracker_ids": [], "similarity_scores": [],
    }
    for data in items:
        output["gt_ids"].extend([values + gt_offset for values in data["gt_ids"]])
        output["tracker_ids"].extend([values + tracker_offset for values in data["tracker_ids"]])
        output["similarity_scores"].extend(data["similarity_scores"])
        output["num_timesteps"] += data["num_timesteps"]
        output["num_gt_dets"] += data["num_gt_dets"]
        output["num_tracker_dets"] += data["num_tracker_dets"]
        gt_offset += data["num_gt_ids"]
        tracker_offset += data["num_tracker_ids"]
    output["num_gt_ids"] = gt_offset
    output["num_tracker_ids"] = tracker_offset
    return output


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workspace", type=Path, required=True)
    parser.add_argument("--data-cache", type=Path, required=True)
    parser.add_argument("--reid-checkpoint", type=Path, required=True)
    parser.add_argument("--aflink-root", type=Path, required=True)
    parser.add_argument("--aflink-checkpoint", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--device", default="cuda:0")
    parser.add_argument("--batch-size", type=int, default=128)
    parser.add_argument("--aflink-batch-size", type=int, default=512)
    parser.add_argument(
        "--family-root", nargs=2, action="append", metavar=("NAME", "PATH"), required=True,
        help="Repeat for frozen subsets such as legacy12 and confirmation38.",
    )
    parser.add_argument(
        "--tracker-cache-dir", type=Path, required=True,
        help="Immutable cache root shared by every refiner in this run.",
    )
    parser.add_argument(
        "--descriptor-cache-dir", type=Path,
        help="Optional immutable descriptor-cache root from a completed input pass.",
    )
    parser.add_argument(
        "--skip-pooled-aggregate", action="store_true",
        help="Report per-sequence metrics and equal-sequence means without a quadratic full-set identity matrix.",
    )
    parser.add_argument("--trackers", nargs="+", choices=("bytetrack", "ocsort", "deepocsort"), default=["bytetrack", "ocsort", "deepocsort"])
    parser.add_argument("--max-sequences-per-family", type=int)
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    sys.path.insert(0, str(args.workspace / "third_party/trackeval_official"))
    sys.path.insert(0, str(args.workspace / "third_party/boxmot_official"))
    mmot = load_module("corrected_linker_mmot", args.workspace / "scripts/run_mmot_locked_temporal.py")
    try:
        from loguru import logger

        logger.remove()
        logger.add(sys.stderr, level="WARNING")
    except ImportError:
        pass
    device = torch.device(args.device)
    if device.type == "cuda" and not torch.cuda.is_available():
        raise SystemExit("CUDA requested but unavailable")
    torch.manual_seed(0)
    np.random.seed(0)
    if device.type == "cuda":
        torch.cuda.manual_seed_all(0)
        torch.backends.cudnn.benchmark = False
    model, reid_manifest = mmot.REID.load_reid(args.reid_checkpoint, device)
    af_runtime, af_manifest = load_aflink(args.aflink_root, args.aflink_checkpoint, device)
    # Warm up both fixed models outside measured method runtimes.
    with torch.inference_mode():
        model(torch.zeros((2, 3, 256, 128), device=device))
        af_runtime.model(torch.zeros((2, 1, 30, 5), device=device), torch.zeros((2, 1, 30, 5), device=device))
    cuda_sync(device)

    family_roots = {name: Path(path) for name, path in args.family_root}
    families = list(family_roots)
    records = []
    runtime_rows = []
    descriptor_rows = []
    accepted_rows = []
    rejected_rows = []
    candidate_rows = []
    size_rows_raw = []
    invariant_failures = []
    processed_instances = 0
    started_all = time.perf_counter()

    for family in families:
        sequence_dirs = sorted(path for path in family_roots[family].iterdir() if path.is_dir())
        if args.max_sequences_per_family is not None:
            sequence_dirs = sequence_dirs[:args.max_sequences_per_family]
        for sequence_dir in sequence_dirs:
            frames, image_map, shape, _ = mmot.load_sequence(sequence_dir)
            for class_id, class_name in enumerate(CLASS_NAMES):
                gt = mmot.class_frames(frames, class_id)
                if not gt:
                    continue
                for tracker in args.trackers:
                    context = {"family": family, "sequence": sequence_dir.name, "class_name": class_name, "tracker": tracker}
                    relative_cache = Path("tracker_outputs") / family / sequence_dir.name / class_name / f"{tracker}.jsonl.gz"
                    cache = args.tracker_cache_dir / relative_cache
                    if cache.is_file():
                        predictions = load_predictions(cache)
                        runtime_rows.append({
                            **context, "method": f"upstream_{tracker}",
                            "runtime_seconds": None,
                            "tracklet_count": len(prediction_tracklets(predictions)[0]),
                            "runtime_status": "reused_immutable_cache",
                        })
                    else:
                        tracker_started = time.perf_counter()
                        if tracker in {"bytetrack", "ocsort"}:
                            predictions = mmot.COMMON.run_sequence(tracker, gt, shape)
                        else:
                            predictions = corrected_deepocsort(mmot, gt, image_map, model, device, args.batch_size)
                        cuda_sync(device)
                        tracker_seconds = time.perf_counter() - tracker_started
                        save_predictions(cache, context, predictions)
                        runtime_rows.append({
                            **context, "method": f"upstream_{tracker}",
                            "runtime_seconds": tracker_seconds,
                            "tracklet_count": len(prediction_tracklets(predictions)[0]),
                            "runtime_status": "measured_and_cached",
                        })
                    tracker_source = str(cache)
                    tracker_source_hash = sha256(cache)

                    descriptor_relative = Path("descriptors") / family / sequence_dir.name / class_name / f"{tracker}.npz"
                    cached_descriptor_path = (
                        args.descriptor_cache_dir / descriptor_relative
                        if args.descriptor_cache_dir is not None else None
                    )
                    if cached_descriptor_path is not None and cached_descriptor_path.is_file():
                        descriptors = load_descriptors(cached_descriptor_path)
                        descriptor_path = cached_descriptor_path
                        descriptor_info = {
                            "tracklets_with_eligible_observations": len(descriptors),
                            "sampled_crops": None,
                            "rejected_invalid_crops": None,
                            "descriptors": len(descriptors),
                            "runtime_seconds": 0.0,
                            "runtime_status": "reused_immutable_cache",
                            "device": str(device),
                            "batch_size": args.batch_size,
                            "channel_policy": "HWC zero-based [4,2,1] as RGB",
                            "crop_admission": "Direct tracker output boxes; no GT matching or GT identity.",
                        }
                    else:
                        descriptors, descriptor_info = extract_descriptors(
                            predictions, image_map, model, device, args.batch_size
                        )
                        descriptor_path = args.output_dir / descriptor_relative
                        descriptor_path.parent.mkdir(parents=True, exist_ok=True)
                        np.savez_compressed(descriptor_path, **{str(identity): feature for identity, feature in descriptors.items()})
                        descriptor_info["runtime_status"] = "measured_and_cached"
                    descriptor_rows.append({
                        **context, **descriptor_info,
                        "tracker_source": tracker_source,
                        "tracker_source_sha256": tracker_source_hash,
                        "descriptor_path": str(descriptor_path),
                        "descriptor_sha256": sha256(descriptor_path),
                    })
                    labels = mmot.M3OT_GRAPH.tracklet_gt_labels(gt, predictions)
                    candidates, eligible_sources = build_candidates(predictions, descriptors)
                    areas = tracklet_areas(predictions)
                    for edge in candidates:
                        candidate_rows.append({
                            **context, **edge,
                            "source_area_median_px2": areas[edge["earlier"]],
                            "destination_area_median_px2": areas[edge["later"]],
                            "pair_size_bin": area_bin(min(areas[edge["earlier"]], areas[edge["later"]])),
                        })

                    for method in sorted(set(METHODS) | set(ABLATIONS)):
                        cuda_sync(device)
                        method_started = time.perf_counter()
                        output, accepted, rejected, details = method_output(
                            method, predictions, candidates, af_runtime, args.aflink_batch_size
                        )
                        cuda_sync(device)
                        elapsed = time.perf_counter() - method_started
                        duplicates = duplicate_frame_identity_count(output)
                        geometry_preserved = geometry_multiset(predictions) == geometry_multiset(output)
                        valid_output = duplicates == 0 and geometry_preserved
                        if not valid_output:
                            invariant_failures.append({**context, "method": method, "duplicate_count": duplicates, "geometry_preserved": geometry_preserved})
                        audited, link_counts = edge_audit(accepted, labels)
                        for edge in audited:
                            source_area = areas[edge["earlier"]]
                            destination_area = areas[edge["later"]]
                            accepted_rows.append({
                                **context, "method": method, **edge,
                                "source_area_median_px2": source_area,
                                "destination_area_median_px2": destination_area,
                                "pair_size_bin": area_bin(min(source_area, destination_area)),
                            })
                            size_rows_raw.append({
                                **context, "method": method,
                                "pair_size_bin": area_bin(min(source_area, destination_area)),
                                "posthoc_gt_correctness": edge["posthoc_gt_correctness"],
                            })
                        for edge in rejected:
                            rejected_rows.append({**context, "method": method, **edge})
                        metric_data = mmot.COMMON.metric_data(gt, output)
                        records.append({
                            **context, "method": method, "metric_data": metric_data,
                            "valid_output": valid_output,
                            "accepted_correct": link_counts["correct"],
                            "accepted_false": link_counts["false"],
                            "accepted_unknown": link_counts["unknown"],
                            "eligible_source_tracklets": len(eligible_sources),
                        })
                        runtime_rows.append({
                            **context, "method": method, "runtime_seconds": elapsed,
                            "tracklet_count": len(prediction_tracklets(predictions)[0]),
                            "temporal_candidate_count": len(candidates),
                            "eligible_source_tracklets": len(eligible_sources),
                            "accepted_links": len(accepted),
                            "rejected_component_links": len(rejected),
                            "duplicate_frame_identity_count": duplicates,
                            "geometry_multiset_preserved": geometry_preserved,
                            **details,
                        })
                    processed_instances += 1

    all_methods = sorted(set(row["method"] for row in records))
    sequence_rows, aggregate_rows = summarize_records(
        mmot.COMMON,
        records,
        families,
        args.trackers,
        all_methods,
        include_pooled=not args.skip_pooled_aggregate,
    )
    link_summary = defaultdict(Counter)
    eligible_summary = defaultdict(int)
    for record in records:
        for scope in (record["family"], "all_sequences"):
            key = (scope, record["tracker"], record["method"])
            link_summary[key].update({
                "correct": record["accepted_correct"],
                "false": record["accepted_false"],
                "unknown": record["accepted_unknown"],
            })
            eligible_summary[key] += record["eligible_source_tracklets"]
    link_summary_rows = []
    for key, counts in sorted(link_summary.items()):
        scope, tracker, method = key
        known = counts["correct"] + counts["false"]
        link_summary_rows.append({
            "scope": scope, "tracker": tracker, "method": method,
            "accepted_correct": counts["correct"], "accepted_false": counts["false"], "accepted_unknown": counts["unknown"],
            "accepted_link_precision": counts["correct"] / known if known else None,
            "eligible_source_tracklets": eligible_summary[key],
            "accepted_link_coverage": known / eligible_summary[key] if eligible_summary[key] else None,
        })

    size_summary = defaultdict(Counter)
    for row in size_rows_raw:
        for scope in (row["family"], "all_sequences"):
            size_summary[(scope, row["tracker"], row["method"], row["pair_size_bin"])][row["posthoc_gt_correctness"]] += 1
    size_rows = []
    for key, counts in sorted(size_summary.items()):
        known = counts["correct"] + counts["false"]
        size_rows.append({
            "scope": key[0], "tracker": key[1], "method": key[2], "size_bin": key[3],
            "accepted_correct": counts["correct"], "accepted_false": counts["false"], "accepted_unknown": counts["unknown"],
            "accepted_link_precision": counts["correct"] / known if known else None,
        })

    results_dir = args.output_dir / "results"
    write_csv(results_dir / "linker_comparison_per_sequence.csv", [row for row in sequence_rows if row["method"] in METHODS])
    write_csv(results_dir / "linker_comparison_aggregate.csv", [row for row in aggregate_rows if row["method"] in METHODS])
    write_csv(results_dir / "temporal_ablation.csv", [row for row in aggregate_rows if row["method"] in ABLATIONS])
    write_csv(results_dir / "accepted_links.csv", accepted_rows)
    write_csv(results_dir / "rejected_links.csv", rejected_rows)
    write_csv(results_dir / "candidate_edges.csv", candidate_rows)
    write_csv(results_dir / "link_summary.csv", link_summary_rows)
    write_csv(results_dir / "refiner_runtime.csv", runtime_rows)
    write_csv(results_dir / "descriptor_runtime.csv", descriptor_rows)
    write_csv(results_dir / "size_stratified_analysis.csv", size_rows)

    manifest = {
        "status": "COMPLETE" if not invariant_failures else "COMPLETE_WITH_INVALID_OUTPUT_VARIANTS",
        "claim_scope": "MMOT oracle-AABB temporal association; corrected RGB proxy; no detector or cross-UAV claim",
        "command": " ".join(sys.argv),
        "script_sha256": sha256(Path(__file__)),
        "processed_class_tracker_instances": processed_instances,
        "families": families,
        "family_roots": {name: str(path) for name, path in family_roots.items()},
        "trackers": args.trackers,
        "methods": list(METHODS),
        "ablations": list(ABLATIONS),
        "fixed_thresholds": {
            "maximum_gap_frames": MAX_GAP,
            "geometry_radius_pixels": GEOMETRY_RADIUS,
            "appearance_cosine_distance": APPEARANCE_DISTANCE,
            "hungarian_unmatched_cost": 1.0,
            "hungarian_controlled_cost": "mean(geometry/55, appearance/0.30, gap/30)",
        },
        "channel_policy": {
            "raw": "HWC uint8, bands 1..8",
            "reid_rgb": "zero-based [4,2,1] -> RGB",
            "deepocsort_cmc_bgr": "zero-based [1,2,4] -> BGR",
        },
        "reid": reid_manifest,
        "aflink": af_manifest,
        "ground_truth_use": "Oracle AABB inputs; identities only for metrics and post-hoc link audit. Appearance crops come directly from tracker boxes without GT matching.",
        "invariant_failures": invariant_failures,
        "invalid_output_policy": "Sequence and aggregate tracking metrics are N/A when any class output violates MOT identity or geometry invariants.",
        "tracker_cache_dir": args.tracker_cache_dir,
        "descriptor_cache_dir": args.descriptor_cache_dir,
        "aggregate_protocol": (
            "per-sequence metrics and equal-sequence means"
            if args.skip_pooled_aggregate
            else "per-sequence, pooled-detection, and equal-sequence aggregates"
        ),
        "runtime_seconds": time.perf_counter() - started_all,
        "cuda": {
            "available": torch.cuda.is_available(),
            "device": str(device),
            "name": torch.cuda.get_device_name(device) if device.type == "cuda" else None,
            "torch": torch.__version__,
        },
        "outputs": {},
    }
    for path in sorted(results_dir.glob("*")):
        manifest["outputs"][path.name] = {"path": str(path), "sha256": sha256(path)}
    write_json(args.output_dir / "manifest.json", manifest)
    print(json.dumps({
        "status": manifest["status"],
        "runtime_seconds": manifest["runtime_seconds"],
        "processed_instances": processed_instances,
        "invariant_failures": len(invariant_failures),
        "aggregate_csv": str(results_dir / "linker_comparison_aggregate.csv"),
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
