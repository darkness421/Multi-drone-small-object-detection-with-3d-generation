"""Build a PNG/PDF preview for the current detector candidate figure."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch


OUT_DIR = Path("paper/figures")


def box(ax, xy, wh, text, fc="#ffffff", ec="#1f2937", fontsize=10):
    x, y = xy
    w, h = wh
    patch = FancyBboxPatch(
        (x, y),
        w,
        h,
        boxstyle="round,pad=0.02,rounding_size=0.05",
        linewidth=1.4,
        facecolor=fc,
        edgecolor=ec,
    )
    ax.add_patch(patch)
    lines = text.split("\n")
    for i, line in enumerate(lines):
        ax.text(
            x + w / 2,
            y + h / 2 + (len(lines) - 1) * 0.12 - i * 0.24,
            line,
            ha="center",
            va="center",
            fontsize=fontsize,
            color="#111827",
            fontweight="bold" if i == 0 else "normal",
        )


def arrow(ax, start, end, rad=0.0):
    ax.add_patch(
        FancyArrowPatch(
            start,
            end,
            arrowstyle="-|>",
            mutation_scale=12,
            linewidth=1.3,
            color="#1f2937",
            connectionstyle=f"arc3,rad={rad}",
        )
    )


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "figure.facecolor": "white",
            "axes.facecolor": "white",
            "savefig.facecolor": "white",
        }
    )
    fig, ax = plt.subplots(figsize=(12.8, 7.2), constrained_layout=True)
    ax.set_xlim(0, 12.8)
    ax.set_ylim(0, 7.2)
    ax.axis("off")

    ax.text(0.35, 6.85, "Current Detector Candidate Schematic: P2-CBAM-FR-s123", fontsize=17, fontweight="bold", color="#0f172a")
    ax.text(0.35, 6.55, "Working structure only; update if the compact final detector changes.", fontsize=10.5, color="#475569")

    box(ax, (0.45, 4.75), (1.25, 0.85), "UAV RGB\n1280 px", fontsize=9)
    box(ax, (2.1, 4.55), (1.8, 1.25), "YOLOv11l\nBackbone\nP2/P3/P4/P5", "#e0f2fe", "#0369a1", 9)
    box(ax, (4.45, 4.55), (2.0, 1.25), "FPN/PAN Neck\nupsample + concat\nDetect layers 19/22/25/28", "#e0f2fe", "#0369a1", 8.5)
    arrow(ax, (1.7, 5.18), (2.1, 5.18))
    arrow(ax, (3.9, 5.18), (4.45, 5.18))

    levels = [
        ("P2 / 4\nlayer 19\n128ch", 5.95),
        ("P3 / 8\nlayer 22\n256ch", 4.75),
        ("P4 / 16\nlayer 25\n512ch", 3.55),
        ("P5 / 32\nlayer 28\n512ch", 2.35),
    ]
    for label, y in levels:
        box(ax, (7.0, y), (1.45, 0.78), label, "#dcfce7", "#15803d", 8.5)
        arrow(ax, (6.45, 5.15), (7.0, y + 0.39), rad=0.05)

    box(
        ax,
        (9.1, 4.45),
        (2.15, 1.2),
        "Residual CBAM\nchannel gate + spatial gate\nstable residual gain",
        "#fef3c7",
        "#b45309",
        8.5,
    )
    box(
        ax,
        (9.1, 2.75),
        (2.15, 1.2),
        "TinySpatialFReLU\nh=F-AvgPool3x3(F)\nY=max(F,c(F))",
        "#fef3c7",
        "#b45309",
        8.5,
    )
    for _, y in levels:
        arrow(ax, (8.45, y + 0.39), (9.1, 5.05 if y > 4.0 else 3.35))

    box(ax, (11.75, 3.75), (0.75, 1.35), "Detect\nP2-P5\nbbox\nclass", "#fee2e2", "#b91c1c", 8)
    arrow(ax, (11.25, 4.35), (11.75, 4.35))

    box(
        ax,
        (0.45, 0.65),
        (11.8, 0.95),
        "Current experiment status\nAP 0.3848 / AP50 0.6079 / Params 26.22M. Accuracy lead so far, but compact confirmation is still required.",
        "#eef2ff",
        "#4338ca",
        9,
    )
    ax.text(0.45, 0.25, "Do not label this as the final proposed detector until the compact queue finishes.", fontsize=9.5, color="#475569")

    for suffix in ("png", "pdf"):
        fig.savefig(OUT_DIR / f"fig02_detector_module.{suffix}", dpi=240)
    plt.close(fig)


if __name__ == "__main__":
    main()
