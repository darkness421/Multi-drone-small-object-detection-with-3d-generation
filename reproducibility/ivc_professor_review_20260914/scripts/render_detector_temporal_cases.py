#!/usr/bin/env python3
"""Render verified detector-input MMOT tracklet-link success and failure cases.

The selected links and all displayed IDs come from frozen tracker outputs and
the accepted-link trace. Ground truth is used only for the post-hoc audit and
for dashed annotations in the figure; it never changes a link or prediction.
"""

from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import json
from collections import defaultdict
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Patch, Rectangle
from scipy.optimize import linear_sum_assignment


CLASS_IDS = {"car": 0}
METHODS = ("com3d_reciprocal_guard", "geometry_reid_hungarian")
METHOD_LABELS = {
    "no_refinement": "No refinement",
    "com3d_reciprocal_guard": "CoM3D-ACE",
    "geometry_reid_hungarian": "Partial-H",
}
TRACKER_LABELS = {
    "bytetrack": "ByteTrack",
    "ocsort": "OC-SORT",
    "deepocsort": "Deep OC-SORT",
}
PREDICTION_COLOR = "#2468D8"
GT_COLOR = "#E87522"
SUCCESS_COLOR = "#087F5B"
FAILURE_COLOR = "#C2413B"
COMPARATOR_COLOR = "#596579"
TEXT_COLOR = "#172033"


CASE_SPECS = (
    {
        "key": "correct_link",
        "panel": "(a) Correct accepted edge",
        "family": "confirmation38",
        "sequence": "data49-2",
        "tracker": "ocsort",
        "class_name": "car",
        "observations": (
            {"frame": 10, "track_id": 3, "gt_id": 2},
            {"frame": 22, "track_id": 1, "gt_id": 2},
            {"frame": 35, "track_id": 28, "gt_id": 2},
        ),
        "com3d_edge": (3, 28),
        "partial_edge": (1, 28),
        "expected_com3d_correctness": "correct",
        "expected_partial_correctness": "correct",
        "interpretation": (
            "CoM3D-ACE correctly joins tracker fragments 3 and 28 for actor 2; "
            "the intervening fragment 1 remains a separate component. Partial-H "
            "instead joins fragments 1 and 28."
        ),
    },
    {
        "key": "false_merge",
        "panel": "(b) Failure case",
        "family": "confirmation38",
        "sequence": "data37-10",
        "tracker": "bytetrack",
        "class_name": "car",
        "observations": (
            {"frame": 90, "track_id": 99, "gt_id": 16},
            {"frame": 102, "track_id": 49, "gt_id": 14},
            {"frame": 136, "track_id": 123, "gt_id": 14},
        ),
        "com3d_edge": (99, 123),
        "partial_edge": (49, 123),
        "expected_com3d_correctness": "false",
        "expected_partial_correctness": "correct",
        "interpretation": (
            "CoM3D-ACE assigns fragment 123 to the wrong predecessor 99; "
            "Partial-H assigns fragment 123 to same-actor predecessor 49."
        ),
    },
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--accepted-links", type=Path, required=True)
    parser.add_argument("--per-sequence-csv", type=Path, required=True)
    parser.add_argument("--tracker-cache-dir", type=Path, required=True)
    parser.add_argument(
        "--family-root", nargs=2, metavar=("NAME", "PATH"), action="append", required=True
    )
    parser.add_argument("--output-dir", type=Path, required=True)
    return parser.parse_args()


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def load_tracklets(path: Path) -> tuple[dict[int, list[dict]], list[dict]]:
    tracklets: dict[int, list[dict]] = defaultdict(list)
    all_rows = []
    with gzip.open(path, "rt", encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            tracklets[int(row["id"])].append(row)
            all_rows.append(row)
    for rows in tracklets.values():
        rows.sort(key=lambda row: int(row["frame"]))
    return dict(tracklets), all_rows


def parse_gt(path: Path, class_id: int) -> list[dict]:
    output = []
    with path.open(encoding="utf-8-sig", errors="replace") as handle:
        for raw in handle:
            values = next(csv.reader([raw.strip()]))
            if len(values) < 12 or int(float(values[11])) != class_id:
                continue
            polygon = np.asarray([float(value) for value in values[2:10]], dtype=float).reshape(4, 2)
            lower = polygon.min(axis=0)
            upper = polygon.max(axis=0)
            output.append(
                {
                    "frame": int(float(values[0])),
                    "id": int(float(values[1])),
                    "x": float(lower[0]),
                    "y": float(lower[1]),
                    "w": float(upper[0] - lower[0]),
                    "h": float(upper[1] - lower[1]),
                }
            )
    return output


def box_array(rows: list[dict]) -> np.ndarray:
    return np.asarray(
        [[row["x"], row["y"], row["x"] + row["w"], row["y"] + row["h"]] for row in rows],
        dtype=float,
    )


def iou_matrix(left: np.ndarray, right: np.ndarray) -> np.ndarray:
    if len(left) == 0 or len(right) == 0:
        return np.zeros((len(left), len(right)), dtype=float)
    top_left = np.maximum(left[:, None, :2], right[None, :, :2])
    bottom_right = np.minimum(left[:, None, 2:], right[None, :, 2:])
    intersection_wh = np.maximum(0.0, bottom_right - top_left)
    intersection = intersection_wh[:, :, 0] * intersection_wh[:, :, 1]
    left_area = (left[:, 2] - left[:, 0]) * (left[:, 3] - left[:, 1])
    right_area = (right[:, 2] - right[:, 0]) * (right[:, 3] - right[:, 1])
    union = left_area[:, None] + right_area[None, :] - intersection
    return np.divide(intersection, union, out=np.zeros_like(intersection), where=union > 0)


def posthoc_match(predictions: list[dict], gt_rows: list[dict], selected_track_id: int, expected_gt_id: int) -> tuple[dict, dict, float]:
    if not predictions or not gt_rows:
        raise RuntimeError("selected frame has no prediction or GT rows")
    similarity = iou_matrix(box_array(gt_rows), box_array(predictions))
    gt_indices, pred_indices = linear_sum_assignment(-similarity)
    matches = {
        int(predictions[pred_index]["id"]): (gt_rows[gt_index], float(similarity[gt_index, pred_index]))
        for gt_index, pred_index in zip(gt_indices, pred_indices)
        if similarity[gt_index, pred_index] >= 0.9
    }
    if selected_track_id not in matches:
        raise RuntimeError(f"track {selected_track_id} has no one-to-one IoU>=0.9 match")
    gt_row, score = matches[selected_track_id]
    if int(gt_row["id"]) != expected_gt_id:
        raise RuntimeError(
            f"track {selected_track_id} matched GT {gt_row['id']}, expected {expected_gt_id}"
        )
    prediction = next(row for row in predictions if int(row["id"]) == selected_track_id)
    return prediction, gt_row, score


def find_edge(rows: list[dict[str, str]], spec: dict, method: str, edge_ids: tuple[int, int], correctness: str) -> dict[str, str]:
    matches = [
        row
        for row in rows
        if row.get("family") == spec["family"]
        and row.get("sequence") == spec["sequence"]
        and row.get("tracker") == spec["tracker"]
        and row.get("class_name") == spec["class_name"]
        and row.get("method") == method
        and int(row["earlier"]) == edge_ids[0]
        and int(row["later"]) == edge_ids[1]
    ]
    if len(matches) != 1:
        raise RuntimeError(f"expected one accepted edge for {spec['key']}/{method}/{edge_ids}, found {len(matches)}")
    if matches[0].get("posthoc_gt_correctness") != correctness:
        raise RuntimeError(f"unexpected edge audit for {spec['key']}/{method}: {matches[0]}")
    return matches[0]


def final_id_map(all_track_ids: set[int], rows: list[dict[str, str]], spec: dict, method: str) -> dict[int, int]:
    edges = [
        row
        for row in rows
        if row.get("family") == spec["family"]
        and row.get("sequence") == spec["sequence"]
        and row.get("tracker") == spec["tracker"]
        and row.get("class_name") == spec["class_name"]
        and row.get("method") == method
    ]
    parent = {identity: identity for identity in all_track_ids}

    def find(identity: int) -> int:
        while parent[identity] != identity:
            parent[identity] = parent[parent[identity]]
            identity = parent[identity]
        return identity

    if method == "geometry_reid_hungarian":
        key = lambda row: (float(row["controlled_cost"]), int(row["gap"]), int(row["earlier"]), int(row["later"]))
    else:
        key = lambda row: (float(row["cosine_distance"]), int(row["gap"]), int(row["earlier"]), int(row["later"]))
    for edge in sorted(edges, key=key):
        earlier_root = find(int(edge["earlier"]))
        later_root = find(int(edge["later"]))
        if earlier_root != later_root:
            parent[later_root] = earlier_root
    return {identity: find(identity) for identity in all_track_ids}


def load_rgb(path: Path) -> np.ndarray:
    array = np.load(path, mmap_mode="r")
    if array.ndim != 3 or array.shape[2] < 5:
        raise RuntimeError(f"expected HWC MMOT array with at least five bands: {path}")
    return np.ascontiguousarray(array[:, :, [4, 2, 1]])


def crop_context(image: np.ndarray, prediction: dict, gt: dict) -> tuple[np.ndarray, tuple[float, float, float, float], tuple[float, float, float, float]]:
    image_height, image_width = image.shape[:2]
    boxes = (prediction, gt)
    left_union = min(float(row["x"]) for row in boxes)
    top_union = min(float(row["y"]) for row in boxes)
    right_union = max(float(row["x"]) + float(row["w"]) for row in boxes)
    bottom_union = max(float(row["y"]) + float(row["h"]) for row in boxes)
    object_width = right_union - left_union
    object_height = bottom_union - top_union
    crop_width = min(float(image_width), max(260.0, 4.0 * object_width, 3.2 * object_height))
    crop_height = min(float(image_height), max(190.0, crop_width / 1.45, 3.4 * object_height))
    center_x = (left_union + right_union) / 2.0
    center_y = (top_union + bottom_union) / 2.0
    left = int(round(max(0.0, min(center_x - crop_width / 2.0, image_width - crop_width))))
    top = int(round(max(0.0, min(center_y - crop_height / 2.0, image_height - crop_height))))
    right = int(round(min(float(image_width), left + crop_width)))
    bottom = int(round(min(float(image_height), top + crop_height)))

    def relative(row: dict) -> tuple[float, float, float, float]:
        return (
            float(row["x"]) - left,
            float(row["y"]) - top,
            float(row["w"]),
            float(row["h"]),
        )

    return image[top:bottom, left:right], relative(prediction), relative(gt)


def draw_observation(axis, record: dict) -> None:
    axis.imshow(record["crop"])
    pred_box = record["prediction_box_in_crop"]
    gt_box = record["gt_box_in_crop"]
    axis.add_patch(Rectangle(pred_box[:2], pred_box[2], pred_box[3], fill=False, edgecolor=PREDICTION_COLOR, linewidth=1.8))
    axis.add_patch(Rectangle(gt_box[:2], gt_box[2], gt_box[3], fill=False, edgecolor=GT_COLOR, linewidth=1.5, linestyle=(0, (3, 2))))
    axis.text(
        pred_box[0],
        max(2.0, pred_box[1] - 4.0),
        f"Pred {record['track_id']}",
        color="white",
        fontsize=6.3,
        fontweight="bold",
        bbox={"facecolor": PREDICTION_COLOR, "edgecolor": "none", "pad": 1.6},
    )
    axis.text(
        0.98,
        0.04,
        f"post-hoc GT {record['gt_id']} | IoU {record['iou']:.2f}",
        transform=axis.transAxes,
        ha="right",
        va="bottom",
        color="white",
        fontsize=5.8,
        fontweight="bold",
        bbox={"facecolor": "#333943", "edgecolor": "none", "alpha": 0.88, "pad": 1.7},
    )
    axis.set_title(f"frame {record['frame']}", fontsize=7.3, fontweight="bold", color=TEXT_COLOR, pad=3)
    axis.set_xticks([])
    axis.set_yticks([])
    for spine in axis.spines.values():
        spine.set_color("#AAB0B8")
        spine.set_linewidth(0.7)


def draw_id_rows(axis, case: dict) -> None:
    axis.set_xlim(0, 1)
    axis.set_ylim(0, 1)
    axis.axis("off")
    observations = case["observations"]
    x_positions = (0.34, 0.53, 0.72)
    axis.text(0.03, 0.89, "Output identity", fontsize=6.4, fontweight="bold", color=TEXT_COLOR, va="center")
    for x, observation in zip(x_positions, observations):
        axis.text(x, 0.89, f"f{observation['frame']}", fontsize=6.1, color="#5A6472", ha="center", va="center")

    rows = (
        ("no_refinement", 0.66),
        ("com3d_reciprocal_guard", 0.39),
        ("geometry_reid_hungarian", 0.12),
    )
    for method, y in rows:
        axis.text(
            0.03,
            y,
            METHOD_LABELS[method],
            fontsize=6.6,
            fontweight="bold" if method == "com3d_reciprocal_guard" else "normal",
            color=SUCCESS_COLOR if method == "com3d_reciprocal_guard" and case["key"] == "correct_link" else TEXT_COLOR,
            va="center",
        )
        ids = []
        for observation in observations:
            local_id = observation["track_id"]
            ids.append(local_id if method == "no_refinement" else case["final_ids"][method][local_id])
        for x, identity in zip(x_positions, ids):
            face = "#F3F5F7"
            edge = "#AAB1BA"
            if method == "com3d_reciprocal_guard" and identity != observations[x_positions.index(x)]["track_id"]:
                face = "#E7F5EF" if case["key"] == "correct_link" else "#FBEAE7"
                edge = SUCCESS_COLOR if case["key"] == "correct_link" else FAILURE_COLOR
            elif method == "geometry_reid_hungarian" and identity != observations[x_positions.index(x)]["track_id"]:
                face = "#EDF1F6"
                edge = COMPARATOR_COLOR
            axis.text(
                x,
                y,
                f"ID {identity}",
                ha="center",
                va="center",
                fontsize=6.4,
                fontweight="bold",
                color=TEXT_COLOR,
                bbox={"boxstyle": "round,pad=0.22", "facecolor": face, "edgecolor": edge, "linewidth": 0.8},
            )
        if method == "com3d_reciprocal_guard":
            edge = case["com3d_edge"]
            correctness = case["com3d_edge_record"]["posthoc_gt_correctness"]
            color = SUCCESS_COLOR if correctness == "correct" else FAILURE_COLOR
            axis.text(0.82, y, f"{edge[0]} -> {edge[1]} ({correctness})", fontsize=6.2, color=color, fontweight="bold", va="center")
        elif method == "geometry_reid_hungarian":
            edge = case["partial_edge"]
            correctness = case["partial_edge_record"]["posthoc_gt_correctness"]
            axis.text(0.82, y, f"{edge[0]} -> {edge[1]} ({correctness})", fontsize=6.2, color=COMPARATOR_COLOR, va="center")
        else:
            axis.text(0.82, y, "no post-link", fontsize=6.2, color="#697382", va="center")


def metric_delta(metric_rows: list[dict[str, str]], spec: dict, method: str) -> float:
    values = [
        row
        for row in metric_rows
        if row.get("family") == spec["family"]
        and row.get("sequence") == spec["sequence"]
        and row.get("tracker") == spec["tracker"]
        and row.get("method") in {"no_refinement", method}
        and row.get("IDF1") not in {None, ""}
    ]
    lookup = {row["method"]: float(row["IDF1"]) for row in values}
    if set(lookup) != {"no_refinement", method}:
        raise RuntimeError(f"missing per-sequence metric for {spec['key']}/{method}")
    return lookup[method] - lookup["no_refinement"]


def build_case(spec: dict, accepted_rows: list[dict[str, str]], metric_rows: list[dict[str, str]], cache_root: Path, family_roots: dict[str, Path], output_dir: Path) -> dict:
    class_id = CLASS_IDS[spec["class_name"]]
    cache_path = (
        cache_root
        / "tracker_outputs"
        / spec["family"]
        / spec["sequence"]
        / spec["class_name"]
        / f"{spec['tracker']}.jsonl.gz"
    )
    tracklets, all_predictions = load_tracklets(cache_path)
    family_root = family_roots[spec["family"]]
    case_output = output_dir / spec["key"]
    case_output.mkdir(parents=True, exist_ok=True)
    observations = []

    for observation_spec in spec["observations"]:
        frame = int(observation_spec["frame"])
        track_id = int(observation_spec["track_id"])
        gt_id = int(observation_spec["gt_id"])
        frame_predictions = [row for row in all_predictions if int(row["frame"]) == frame]
        gt_rows = parse_gt(family_root / spec["sequence"] / f"{frame:06d}.txt", class_id)
        prediction, gt, score = posthoc_match(frame_predictions, gt_rows, track_id, gt_id)
        image_path = family_root / spec["sequence"] / f"{frame:06d}.npy"
        crop, pred_relative, gt_relative = crop_context(load_rgb(image_path), prediction, gt)
        plain_crop = case_output / f"frame_{frame:03d}_pred_{track_id}_gt_{gt_id}_crop.png"
        plt.imsave(plain_crop, crop)
        record = {
            **observation_spec,
            "iou": score,
            "prediction": prediction,
            "gt": gt,
            "image_path": str(image_path.resolve()),
            "image_sha256": sha256(image_path),
            "plain_crop": str(plain_crop.relative_to(output_dir)),
            "crop": crop,
            "prediction_box_in_crop": pred_relative,
            "gt_box_in_crop": gt_relative,
        }
        observations.append(record)

    com3d_edge_record = find_edge(
        accepted_rows,
        spec,
        "com3d_reciprocal_guard",
        spec["com3d_edge"],
        spec["expected_com3d_correctness"],
    )
    partial_edge_record = find_edge(
        accepted_rows,
        spec,
        "geometry_reid_hungarian",
        spec["partial_edge"],
        spec["expected_partial_correctness"],
    )
    all_track_ids = set(tracklets)
    final_ids = {
        method: final_id_map(all_track_ids, accepted_rows, spec, method) for method in METHODS
    }
    selected_ids = {int(observation["track_id"]) for observation in observations}
    final_ids = {
        method: {identity: mapping[identity] for identity in sorted(selected_ids)}
        for method, mapping in final_ids.items()
    }
    return {
        **spec,
        "cache_path": str(cache_path.resolve()),
        "cache_sha256": sha256(cache_path),
        "observations": observations,
        "com3d_edge_record": com3d_edge_record,
        "partial_edge_record": partial_edge_record,
        "final_ids": final_ids,
        "delta_idf1_pp": {
            method: metric_delta(metric_rows, spec, method) for method in METHODS
        },
    }


def serializable_case(case: dict) -> dict:
    output = {key: value for key, value in case.items() if key != "observations"}
    output["observations"] = []
    for observation in case["observations"]:
        output["observations"].append(
            {
                key: value
                for key, value in observation.items()
                if key not in {"crop", "prediction_box_in_crop", "gt_box_in_crop"}
            }
            | {
                "prediction_box_in_crop": list(observation["prediction_box_in_crop"]),
                "gt_box_in_crop": list(observation["gt_box_in_crop"]),
            }
        )
    return output


def write_case_csv(path: Path, cases: list[dict]) -> None:
    fields = (
        "case",
        "family",
        "sequence",
        "tracker",
        "class_name",
        "frame",
        "local_prediction_id",
        "posthoc_gt_id",
        "one_to_one_iou",
        "plain_crop",
    )
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for case in cases:
            for observation in case["observations"]:
                writer.writerow(
                    {
                        "case": case["key"],
                        "family": case["family"],
                        "sequence": case["sequence"],
                        "tracker": case["tracker"],
                        "class_name": case["class_name"],
                        "frame": observation["frame"],
                        "local_prediction_id": observation["track_id"],
                        "posthoc_gt_id": observation["gt_id"],
                        "one_to_one_iou": observation["iou"],
                        "plain_crop": observation["plain_crop"],
                    }
                )


def render(cases: list[dict], output_png: Path, output_pdf: Path) -> None:
    figure = plt.figure(figsize=(7.25, 7.35), facecolor="white")
    outer = figure.add_gridspec(2, 1, left=0.03, right=0.985, top=0.94, bottom=0.025, hspace=0.30)
    for case_index, case in enumerate(cases):
        grid = outer[case_index].subgridspec(2, 3, height_ratios=(1.0, 0.62), hspace=0.10, wspace=0.035)
        axes = [figure.add_subplot(grid[0, column]) for column in range(3)]
        for axis, observation in zip(axes, case["observations"]):
            draw_observation(axis, observation)
        axes[0].text(
            0.0,
            1.22,
            f"{case['panel']} ({case['sequence']} / {TRACKER_LABELS[case['tracker']]})",
            transform=axes[0].transAxes,
            ha="left",
            va="bottom",
            fontsize=7.9,
            fontweight="bold",
            color=TEXT_COLOR,
        )
        axes[2].text(
            1.0,
            1.20,
            f"sequence delta IDF1: CoM3D-ACE {case['delta_idf1_pp']['com3d_reciprocal_guard']:+.2f} pp; "
            f"Partial-H {case['delta_idf1_pp']['geometry_reid_hungarian']:+.2f} pp",
            transform=axes[2].transAxes,
            ha="right",
            va="bottom",
            fontsize=5.9,
            color="#566171",
        )
        id_axis = figure.add_subplot(grid[1, :])
        draw_id_rows(id_axis, case)

    figure.legend(
        handles=(
            Patch(facecolor="none", edgecolor=PREDICTION_COLOR, label="frozen prediction box / local ID"),
            Patch(facecolor="none", edgecolor=GT_COLOR, linestyle="--", label="post-hoc GT audit"),
        ),
        loc="upper center",
        bbox_to_anchor=(0.5, 1.015),
        ncol=2,
        frameon=False,
        fontsize=6.4,
    )
    figure.savefig(output_png, dpi=400, bbox_inches="tight", facecolor="white")
    figure.savefig(output_pdf, bbox_inches="tight", facecolor="white")
    plt.close(figure)


def main() -> int:
    args = parse_args()
    family_roots = {name: Path(path) for name, path in args.family_root}
    accepted_rows = read_csv(args.accepted_links)
    metric_rows = read_csv(args.per_sequence_csv)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    cases = [
        build_case(spec, accepted_rows, metric_rows, args.tracker_cache_dir, family_roots, args.output_dir)
        for spec in CASE_SPECS
    ]

    output_png = args.output_dir / "mmot_detector_temporal_cases.png"
    output_pdf = args.output_dir / "mmot_detector_temporal_cases.pdf"
    render(cases, output_png, output_pdf)
    write_case_csv(args.output_dir / "case_observations.csv", cases)

    manifest = {
        "accepted_links": str(args.accepted_links.resolve()),
        "accepted_links_sha256": sha256(args.accepted_links),
        "per_sequence_metrics": str(args.per_sequence_csv.resolve()),
        "per_sequence_metrics_sha256": sha256(args.per_sequence_csv),
        "channel_policy": "Raw HWC bands [4,2,1] (zero-based) displayed as RGB.",
        "gt_use": (
            "Post-hoc one-to-one same-class IoU>=0.9 audit and dashed figure labels only; "
            "GT is not used by either linker."
        ),
        "selection_note": (
            "The correct case exposes a verified CoM3D-ACE accepted edge across frozen tracker fragments. "
            "The failure case exposes a verified false CoM3D-ACE edge for which Partial-H chose a correct "
            "alternative predecessor. Representative displayed observations are high-IoU points within the "
            "linked tracklets; accepted-edge records retain the actual endpoint frames and gaps."
        ),
        "cases": [serializable_case(case) for case in cases],
        "outputs": [
            output_png.name,
            output_pdf.name,
            "case_observations.csv",
        ],
        "experiment_status": "rendered from frozen predictions and link traces; no new training or tracking",
    }
    (args.output_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps({case["key"]: case["delta_idf1_pp"] for case in cases}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
