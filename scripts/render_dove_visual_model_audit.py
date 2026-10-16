#!/usr/bin/env python3
"""Render paper-editable figures from the DOVE visual-model audit outputs."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
from PIL import Image, ImageDraw


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _box(ax, xy, width, height, text, face, edge="#263238") -> None:
    patch = FancyBboxPatch(
        xy,
        width,
        height,
        boxstyle="round,pad=0.02,rounding_size=0.03",
        linewidth=1.4,
        edgecolor=edge,
        facecolor=face,
    )
    ax.add_patch(patch)
    ax.text(
        xy[0] + width / 2,
        xy[1] + height / 2,
        text,
        ha="center",
        va="center",
        fontsize=9,
    )


def _arrow(ax, start, end, label=None) -> None:
    ax.annotate(
        "",
        xy=end,
        xytext=start,
        arrowprops={"arrowstyle": "->", "linewidth": 1.3, "color": "#37474f"},
    )
    if label:
        ax.text(
            (start[0] + end[0]) / 2,
            (start[1] + end[1]) / 2 + 0.025,
            label,
            ha="center",
            va="bottom",
            fontsize=7.5,
            color="#455a64",
        )


def render_system_diagram(output_dir: Path) -> None:
    fig, ax = plt.subplots(figsize=(12, 5.6))
    ax.set_xlim(0, 12)
    ax.set_ylim(0, 6)
    ax.axis("off")
    _box(ax, (0.3, 3.9), 1.8, 1.0, "Current RGB\n(uav_01 only)", "#e3f2fd")
    _box(ax, (0.3, 1.2), 1.8, 1.0, "Candidate action\n(camera pose)", "#e8f5e9")
    _box(ax, (2.8, 3.9), 2.0, 1.0, "Shared frozen\nvisual encoder", "#bbdefb")
    _box(ax, (2.8, 1.2), 2.0, 1.0, "Geometry/action\nfeatures", "#c8e6c9")
    _box(ax, (5.5, 4.4), 2.2, 1.0, "Visual Direct Ridge\nvisual x action", "#fff3e0")
    _box(ax, (5.5, 2.6), 2.2, 1.0, "Geometry Ridge\nbase prediction", "#f1f8e9")
    _box(ax, (5.5, 0.8), 2.2, 1.0, "Visual Residual Ridge\ncorrect base score", "#fce4ec")
    _box(ax, (8.4, 3.3), 1.7, 1.0, "Predicted\nRecall@0.5", "#ede7f6")
    _box(ax, (10.6, 3.3), 1.1, 1.0, "Argmax\naction", "#d1c4e9")
    _box(ax, (8.4, 0.7), 3.3, 1.0, "GT next-view boxes\ntraining/evaluation only", "#eeeeee", edge="#616161")
    _arrow(ax, (2.1, 4.4), (2.8, 4.4))
    _arrow(ax, (2.1, 1.7), (2.8, 1.7))
    _arrow(ax, (4.8, 4.4), (5.5, 4.9), "same encoder")
    _arrow(ax, (4.8, 4.4), (5.5, 1.3), "same encoder")
    _arrow(ax, (4.8, 1.7), (5.5, 4.8))
    _arrow(ax, (4.8, 1.7), (5.5, 3.1))
    _arrow(ax, (7.7, 3.1), (8.4, 3.7))
    _arrow(ax, (7.7, 1.3), (8.4, 3.6), "base + residual")
    _arrow(ax, (7.7, 4.9), (8.4, 3.9))
    _arrow(ax, (10.1, 3.8), (10.6, 3.8))
    _arrow(ax, (9.5, 1.7), (9.5, 3.3), "labels only")
    ax.text(
        6.0,
        5.75,
        "DOVE GT-Supervised Visual Viewpoint Pilot",
        ha="center",
        va="center",
        fontsize=14,
        weight="bold",
    )
    ax.text(
        6.0,
        0.15,
        "Candidate outcome RGB is never an input. Memory, discovery, and closed-loop control are not implemented.",
        ha="center",
        va="center",
        fontsize=8.5,
        color="#b71c1c",
    )
    fig.tight_layout()
    for suffix in ("svg", "pdf"):
        fig.savefig(output_dir / f"dove_visual_pilot_system.{suffix}", bbox_inches="tight")
    plt.close(fig)


def render_metric_chart(summary_csv: Path, output_dir: Path) -> None:
    rows = {row["method"]: row for row in _read_csv(summary_csv)}
    methods = [
        "FIXED_CURRENT_VIEW",
        "UNIFORM_RANDOM_EXPECTATION",
        "GEOMETRY_RIDGE",
        "VISUAL_DIRECT_RIDGE",
        "GEOMETRY_VISUAL_RESIDUAL_RIDGE",
        "GT_RECALL_ORACLE",
    ]
    labels = ["Fixed", "Random\nexpected", "Geometry", "Visual\ndirect", "Geometry +\nvisual residual", "Oracle"]
    recalls = [float(rows[method]["mean_selected_recall_at_iou50"]) for method in methods]
    f1s = [float(rows[method]["mean_selected_f1_at_iou50"]) for method in methods]
    x = list(range(len(methods)))
    fig, ax = plt.subplots(figsize=(10, 4.8))
    ax.bar([value - 0.19 for value in x], recalls, width=0.38, label="Recall@0.5", color="#1976d2")
    ax.bar([value + 0.19 for value in x], f1s, width=0.38, label="F1@0.5", color="#ef6c00")
    ax.set_xticks(x, labels)
    ax.set_ylabel("Mean selected-view score")
    ax.set_title("Balanced synthetic proxy pilot (12 scene variants)")
    ax.grid(axis="y", color="#dddddd", linewidth=0.7)
    ax.legend(frameon=False)
    ax.text(
        0.99,
        0.96,
        "Visual modules not adopted",
        transform=ax.transAxes,
        ha="right",
        va="top",
        color="#b71c1c",
        weight="bold",
    )
    fig.tight_layout()
    for suffix in ("svg", "pdf"):
        fig.savefig(output_dir / f"dove_balanced_model_comparison.{suffix}", bbox_inches="tight")
    plt.close(fig)


def render_qualitative(eval_dir: Path, output_dir: Path) -> None:
    cases = [
        (2, "uav_01", "Geometry success / visual embedding failure"),
        (4, "uav_02", "Oracle view missed by both learned policies"),
        (7, "uav_01", "Shared successful selection"),
    ]
    panels = []
    for scene, uav_id, title in cases:
        path = eval_dir / "overlays" / f"frame_{scene:04d}_{uav_id}.png"
        image = Image.open(path).convert("RGB")
        image.thumbnail((720, 405))
        canvas = Image.new("RGB", (720, 455), "white")
        canvas.paste(image, ((720 - image.width) // 2, 50))
        draw = ImageDraw.Draw(canvas)
        draw.text((12, 10), f"Scene {scene} / {uav_id}", fill="black")
        draw.text((12, 28), title, fill=(150, 25, 25))
        panels.append(canvas)
    montage = Image.new("RGB", (720, 455 * len(panels)), "white")
    for index, panel in enumerate(panels):
        montage.paste(panel, (0, 455 * index))
    montage.save(output_dir / "dove_balanced_success_failure_cases.png")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--summary-csv", required=True)
    parser.add_argument("--evaluation-dir", required=True)
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()
    output_dir = Path(args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    render_system_diagram(output_dir)
    render_metric_chart(Path(args.summary_csv).resolve(), output_dir)
    render_qualitative(Path(args.evaluation_dir).resolve(), output_dir)
    print(output_dir)


if __name__ == "__main__":
    main()
