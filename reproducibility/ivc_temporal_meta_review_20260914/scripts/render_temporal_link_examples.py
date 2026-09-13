#!/usr/bin/env python3
"""Render auditable success and failure examples from frozen MMOT tracklets.

The script reads only saved tracker outputs and the post-hoc link audit CSV.
Ground-truth identity labels are never used to construct or alter a link.
"""

from __future__ import annotations

import argparse
import csv
import gzip
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Rectangle


CORRECT_COLOR = "#16865a"
FAILURE_COLOR = "#c34f32"
SOURCE_COLOR = "#2468d8"
DESTINATION_COLOR = "#e87522"
TEXT_COLOR = "#162033"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--accepted-links", type=Path, required=True)
    parser.add_argument("--tracker-cache-dir", type=Path, required=True)
    parser.add_argument(
        "--family-root", nargs=2, metavar=("NAME", "PATH"), action="append", required=True
    )
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--method", default="com3d_reciprocal_guard")
    parser.add_argument("--preferred-family", default="confirmation38")
    parser.add_argument("--min-purity", type=float, default=0.8)
    return parser.parse_args()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def load_tracklets(path: Path) -> dict[int, list[dict]]:
    tracklets: dict[int, list[dict]] = {}
    with gzip.open(path, "rt", encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            tracklets.setdefault(int(row["id"]), []).append(row)
    for rows in tracklets.values():
        rows.sort(key=lambda row: int(row["frame"]))
    return tracklets


def endpoint_record(row: dict, cache_dir: Path) -> dict | None:
    family = row["family"]
    sequence = row["sequence"]
    class_name = row["class_name"]
    tracker = row["tracker"]
    path = cache_dir / "tracker_outputs" / family / sequence / class_name / f"{tracker}.jsonl.gz"
    if not path.exists():
        return None
    tracklets = load_tracklets(path)
    earlier = int(row["earlier"])
    later = int(row["later"])
    if earlier not in tracklets or later not in tracklets:
        return None
    source = tracklets[earlier][-1]
    destination = tracklets[later][0]
    if int(source["frame"]) >= int(destination["frame"]):
        return None
    source_area = float(source["w"]) * float(source["h"])
    destination_area = float(destination["w"]) * float(destination["h"])
    return {
        **row,
        "source": source,
        "destination": destination,
        "visual_score": min(source_area, destination_area),
    }


def choose_examples(rows: list[dict], cache_dir: Path, preferred_family: str, min_purity: float) -> list[dict]:
    candidates: list[dict] = []
    for row in rows:
        if row.get("posthoc_gt_correctness") not in {"correct", "false"}:
            continue
        try:
            source_purity = float(row.get("source_gt_purity", "nan"))
            destination_purity = float(row.get("destination_gt_purity", "nan"))
        except ValueError:
            continue
        if min(source_purity, destination_purity) < min_purity:
            continue
        record = endpoint_record(row, cache_dir)
        if record is not None:
            candidates.append(record)

    chosen = []
    for correctness in ("correct", "false"):
        subset = [row for row in candidates if row["posthoc_gt_correctness"] == correctness]
        preferred = [row for row in subset if row["family"] == preferred_family]
        pool = preferred or subset
        if not pool:
            raise RuntimeError(f"No auditable {correctness} link satisfies the fixed selection rule")
        pool.sort(
            key=lambda row: (
                float(row["visual_score"]),
                -int(row["gap"]),
                row["sequence"],
                row["tracker"],
                row["class_name"],
                int(row["earlier"]),
                int(row["later"]),
            ),
            reverse=True,
        )
        chosen.append(pool[0])
    return chosen


def load_rgb(path: Path) -> np.ndarray:
    array = np.load(path, mmap_mode="r")
    if array.ndim != 3 or array.shape[2] < 5:
        raise ValueError(f"Expected HWC MMOT array with at least five bands: {path}")
    return np.ascontiguousarray(array[:, :, [4, 2, 1]])


def context_crop(image: np.ndarray, box: dict) -> tuple[np.ndarray, tuple[float, float, float, float]]:
    x, y, w, h = (float(box[key]) for key in ("x", "y", "w", "h"))
    image_h, image_w = image.shape[:2]
    crop_w = min(image_w, max(280.0, 7.0 * w, 5.0 * h))
    crop_h = min(image_h, max(220.0, crop_w / 1.35, 7.0 * h, 4.0 * w))
    center_x, center_y = x + w / 2.0, y + h / 2.0
    left = int(round(max(0.0, min(center_x - crop_w / 2.0, image_w - crop_w))))
    top = int(round(max(0.0, min(center_y - crop_h / 2.0, image_h - crop_h))))
    right = int(round(min(image_w, left + crop_w)))
    bottom = int(round(min(image_h, top + crop_h)))
    return image[top:bottom, left:right], (x - left, y - top, w, h)


def draw_endpoint(ax, family_root: Path, sequence: str, endpoint: dict, color: str, role: str) -> None:
    frame = int(endpoint["frame"])
    image_path = family_root / sequence / f"{frame:06d}.npy"
    image = load_rgb(image_path)
    crop, box = context_crop(image, endpoint)
    ax.imshow(crop)
    ax.add_patch(Rectangle((box[0], box[1]), box[2], box[3], fill=False, edgecolor=color, linewidth=2.5))
    ax.text(
        box[0], max(2.0, box[1] - 5.0), f"ID {int(endpoint['id'])}", color="white",
        fontsize=9, fontweight="bold", bbox={"facecolor": color, "edgecolor": "none", "pad": 2.5}
    )
    ax.set_title(f"{role}: frame {frame}", color=color, fontsize=11, fontweight="bold", pad=6)
    ax.set_xticks([])
    ax.set_yticks([])
    for spine in ax.spines.values():
        spine.set_color(color)
        spine.set_linewidth(1.7)


def draw_decision(ax, row: dict) -> None:
    correct = row["posthoc_gt_correctness"] == "correct"
    result_color = CORRECT_COLOR if correct else FAILURE_COLOR
    result_text = "same actor" if correct else "different actors"
    source_id = int(row["earlier"])
    destination_id = int(row["later"])
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    ax.text(0.5, 0.90, "Frozen evidence decision", ha="center", va="center", fontsize=11,
            fontweight="bold", color=TEXT_COLOR)
    ax.text(0.17, 0.65, f"ID {source_id}", ha="center", va="center", color="white", fontsize=10,
            fontweight="bold", bbox={"facecolor": SOURCE_COLOR, "edgecolor": "none", "pad": 5})
    ax.text(0.83, 0.65, f"ID {destination_id}", ha="center", va="center", color="white", fontsize=10,
            fontweight="bold", bbox={"facecolor": DESTINATION_COLOR, "edgecolor": "none", "pad": 5})
    ax.annotate("", xy=(0.70, 0.65), xytext=(0.30, 0.65),
                arrowprops={"arrowstyle": "->", "lw": 2.4, "color": result_color})
    ax.text(0.5, 0.51, "accepted", ha="center", color=result_color, fontsize=10, fontweight="bold")
    ax.text(0.5, 0.34, f"gap {int(row['gap'])} frames  |  center {float(row['endpoint_center_distance_pixels']):.1f} px",
            ha="center", fontsize=9, color=TEXT_COLOR)
    ax.text(0.5, 0.23, f"ReID cosine distance {float(row['cosine_distance']):.3f}",
            ha="center", fontsize=9, color=TEXT_COLOR)
    ax.text(0.5, 0.08, f"Post-hoc GT audit: {result_text}", ha="center", fontsize=10,
            fontweight="bold", color=result_color)


def serializable_selection(row: dict) -> dict:
    return {
        key: value for key, value in row.items()
        if key not in {"source", "destination"}
    } | {
        "source_endpoint": row["source"],
        "destination_endpoint": row["destination"],
    }


def main() -> int:
    args = parse_args()
    family_roots = {name: Path(path) for name, path in args.family_root}
    rows = [row for row in read_csv(args.accepted_links) if row.get("method") == args.method]
    selected = choose_examples(rows, args.tracker_cache_dir, args.preferred_family, args.min_purity)
    args.output_dir.mkdir(parents=True, exist_ok=True)

    figure = plt.figure(figsize=(12.0, 6.4), constrained_layout=True, facecolor="white")
    grid = figure.add_gridspec(2, 3, width_ratios=(1.0, 1.0, 0.92), hspace=0.22, wspace=0.08)
    labels = ("(a) Correct accepted link", "(b) Accepted link failure")
    for row_index, (row, label) in enumerate(zip(selected, labels)):
        family_root = family_roots[row["family"]]
        left = figure.add_subplot(grid[row_index, 0])
        right = figure.add_subplot(grid[row_index, 1])
        decision = figure.add_subplot(grid[row_index, 2])
        draw_endpoint(left, family_root, row["sequence"], row["source"], SOURCE_COLOR, "Source endpoint")
        draw_endpoint(right, family_root, row["sequence"], row["destination"], DESTINATION_COLOR, "Destination endpoint")
        draw_decision(decision, row)
        left.text(
            0.0, 1.17,
            f"{label}: {row['sequence']} / {row['class_name']} / {row['tracker']}",
            transform=left.transAxes, ha="left", va="bottom", fontsize=11.5,
            fontweight="bold", color=TEXT_COLOR,
        )

    figure.suptitle(
        "Frozen-tracklet evidence links with post-hoc identity audit",
        fontsize=15, fontweight="bold", color=TEXT_COLOR,
    )
    png = args.output_dir / "temporal_link_success_failure.png"
    pdf = args.output_dir / "temporal_link_success_failure.pdf"
    figure.savefig(png, dpi=300, bbox_inches="tight", facecolor="white")
    figure.savefig(pdf, bbox_inches="tight", facecolor="white")
    plt.close(figure)

    manifest = {
        "accepted_links": str(args.accepted_links.resolve()),
        "method": args.method,
        "preferred_family": args.preferred_family,
        "selection_rule": (
            "For each post-hoc correctness class, prefer the prespecified confirmation family, "
            "require endpoint majority-GT purity >= min_purity, then maximize the smaller endpoint box area; "
            "ties use shorter gap and stable lexical/ID ordering."
        ),
        "min_purity": args.min_purity,
        "ground_truth_use": "Post-hoc correctness audit and figure annotation only; never link construction.",
        "channel_policy": "Raw HWC bands [4,2,1] (zero-based) displayed as RGB.",
        "selected": [serializable_selection(row) for row in selected],
        "outputs": [str(png.resolve()), str(pdf.resolve())],
    }
    (args.output_dir / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(manifest, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
