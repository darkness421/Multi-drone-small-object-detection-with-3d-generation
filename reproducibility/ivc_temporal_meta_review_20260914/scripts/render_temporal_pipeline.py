#!/usr/bin/env python3
"""Render the executable temporal-refinement pipeline as a paper-ready figure."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def box(ax, x: float, y: float, width: float, height: float, title: str, lines: list[str], color: str) -> None:
    patch = FancyBboxPatch(
        (x, y), width, height,
        boxstyle="round,pad=0.012,rounding_size=0.018",
        linewidth=1.4, edgecolor=color, facecolor="white",
    )
    ax.add_patch(patch)
    ax.add_patch(FancyBboxPatch(
        (x, y + height - 0.18), width, 0.18,
        boxstyle="round,pad=0.012,rounding_size=0.018",
        linewidth=0, facecolor=color, alpha=0.14,
    ))
    ax.text(x + 0.025, y + height - 0.09, title, ha="left", va="center", fontsize=10.5, weight="bold", color="#172033")
    ax.text(x + width / 2, y + (height - 0.18) / 2, "\n".join(lines), ha="center", va="center", fontsize=7.8, color="#273449", linespacing=1.22)


def arrow(ax, start: tuple[float, float], end: tuple[float, float], color: str = "#46566d") -> None:
    ax.add_patch(FancyArrowPatch(start, end, arrowstyle="-|>", mutation_scale=12, linewidth=1.35, color=color))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    plt.rcParams.update({
        "font.family": "DejaVu Sans",
        "font.size": 9,
        "axes.unicode_minus": False,
    })
    fig, ax = plt.subplots(figsize=(14.2, 4.4))
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    colors = ("#365f8d", "#287271", "#8a5a44", "#675a8f", "#287271", "#365f8d")
    xs = (0.015, 0.18, 0.345, 0.51, 0.675, 0.84)
    titles = (
        "1  Saved tracklets", "2  Tracklet evidence", "3  Candidate graph",
        "4  Reciprocal gate", "5  Component guard", "6  Refined output",
    )
    body = (
        ["fixed boxes + classes", "local IDs + frame support", "ByteTrack / OC-SORT /", "Deep OC-SORT"],
        ["first / middle / last crops", "mean 128-D ReID", "descriptor + endpoints"],
        [r"$0 < \Delta t \leq 30$ frames", r"$d_{xy} \leq 55$ px", r"$d_{cos} \leq 0.30$"],
        ["mutual best successor", "deterministic tie breaking", "unmatched is allowed"],
        ["reject component merges", "with frame overlap", "preserve every input box"],
        ["accepted ID remaps", "unresolved stay unchanged", "no interpolation"],
    )
    width, height, y = 0.145, 0.55, 0.29
    for x, title, lines, color in zip(xs, titles, body, colors):
        box(ax, x, y, width, height, title, lines, color)
    for left, right in zip(xs[:-1], xs[1:]):
        arrow(ax, (left + width + 0.004, y + height / 2), (right - 0.004, y + height / 2))

    ax.text(0.015, 0.93, "Executable post-tracking refinement path", fontsize=13, weight="bold", color="#172033", ha="left")
    ax.text(0.015, 0.885, "All refiners receive the same frozen upstream tracklets", fontsize=9.5, color="#46566d", ha="left")
    audit = FancyBboxPatch(
        (0.18, 0.075), 0.66, 0.105,
        boxstyle="round,pad=0.012,rounding_size=0.018",
        linewidth=1.0, edgecolor="#9a4f4f", facecolor="#fffafa",
    )
    ax.add_patch(audit)
    ax.text(
        0.51, 0.127,
        "Evaluation-only audit: GT identities are read after links are frozen for HOTA / AssA / IDF1 / IDSW and link TP / FP",
        ha="center", va="center", fontsize=8.8, color="#7b3838",
    )
    arrow(ax, (0.88, y), (0.82, 0.18), color="#9a4f4f")

    png = args.output_dir / "temporal_refinement_pipeline.png"
    pdf = args.output_dir / "temporal_refinement_pipeline.pdf"
    fig.savefig(png, dpi=300, bbox_inches="tight", facecolor="white")
    fig.savefig(pdf, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    manifest = {
        "status": "COMPLETE",
        "command": " ".join(sys.argv),
        "script_sha256": sha256(Path(__file__)),
        "content_scope": "Visualization of the frozen implementation; no learned or unimplemented module is shown.",
        "outputs": {png.name: sha256(png), pdf.name: sha256(pdf)},
    }
    (args.output_dir / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": "COMPLETE", "png": str(png), "pdf": str(pdf)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
