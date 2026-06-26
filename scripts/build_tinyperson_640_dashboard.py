"""Build a readable TinyPerson 640 supplementary stress-test dashboard."""

from __future__ import annotations

import argparse
import csv
import os
from pathlib import Path

os.environ.setdefault("MPLBACKEND", "Agg")
os.environ.setdefault("MPLCONFIGDIR", "/tmp/matplotlib")

import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle


NAME_MAP = {
    "ProposedSize-P2P4BalancedSelfAttnTinyFReLU-yolo11l-TinyPerson640": "SAFR-YOLO",
    "ProposedSize-P2P4HeadOnly-yolo11l-TinyPerson640": "P2P4 head only",
    "YOLOv11l-TinyPerson640": "YOLOv11l",
    "YOLOv8l-TinyPerson640": "YOLOv8l",
    "YOLOv9c-TinyPerson640": "YOLOv9c",
    "YOLOv9m-TinyPerson640": "YOLOv9m",
}

INTERPRETATION = {
    "SAFR-YOLO": "domain-shift limitation",
    "P2P4 head only": "core ablation",
    "YOLOv11l": "near-zero transfer",
    "YOLOv8l": "near-zero transfer",
    "YOLOv9c": "unstable sparse split",
    "YOLOv9m": "strongest, still near zero",
}


def as_float(value: str | None) -> float:
    if value is None or value == "":
        return 0.0
    return float(value)


def read_rows(path: Path) -> list[dict[str, float | str]]:
    rows: list[dict[str, float | str]] = []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            name = NAME_MAP.get(row["method"], row["method"].replace("-TinyPerson640", ""))
            rows.append(
                {
                    "method": name,
                    "ap": as_float(row.get("best_AP_mean")),
                    "ap_std": as_float(row.get("best_AP_std")),
                    "ap50": as_float(row.get("best_AP50_mean")),
                    "ap50_std": as_float(row.get("best_AP50_std")),
                    "recall": as_float(row.get("best_recall_mean")),
                    "f1": as_float(row.get("best_F1_mean")),
                    "f1_std": as_float(row.get("best_F1_std")),
                    "seeds": row.get("seeds", ""),
                    "note": INTERPRETATION.get(name, "diagnostic"),
                }
            )
    return sorted(rows, key=lambda item: float(item["ap"]), reverse=True)


def metric_text(mean: float, std: float, scale: float = 1.0) -> str:
    return f"{mean * scale:.3f} +/- {std * scale:.3f}"


def latex_escape(value: str) -> str:
    return (
        value.replace("\\", "\\textbackslash{}")
        .replace("&", "\\&")
        .replace("%", "\\%")
        .replace("_", "\\_")
        .replace("#", "\\#")
    )


def latex_metric(mean: float, std: float, scale: float = 1.0, *, bold: bool = False) -> str:
    text = f"{mean * scale:.3f} $\\pm$ {std * scale:.3f}"
    return f"\\textbf{{{text}}}" if bold else text


def write_tex(rows: list[dict[str, float | str]], out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    best_ap = max(float(row["ap"]) for row in rows) if rows else 0.0
    best_ap50 = max(float(row["ap50"]) for row in rows) if rows else 0.0
    lines = [
        "\\begin{tabular}{lrrrrl}",
        "\\toprule",
        "Method & AP $\\times 10^{-3}$ & AP50 $\\times 10^{-3}$ & Recall & F1 $\\times 10^{-3}$ & Interpretation \\\\",
        "\\midrule",
    ]
    for row in rows:
        method = str(row["method"])
        ap = float(row["ap"])
        ap50 = float(row["ap50"])
        line = (
            f"{latex_escape(method)} & "
            f"{latex_metric(ap, float(row['ap_std']), 1000.0, bold=ap == best_ap)} & "
            f"{latex_metric(ap50, float(row['ap50_std']), 1000.0, bold=ap50 == best_ap50)} & "
            f"{float(row['recall']):.4f} & "
            f"{latex_metric(float(row['f1']), float(row['f1_std']), 1000.0)} & "
            f"{latex_escape(str(row['note']))} \\\\"
        )
        lines.append(line)
    lines.extend(["\\bottomrule", "\\end{tabular}", ""])
    out_path.write_text("\n".join(lines), encoding="utf-8")


def draw_table(ax: plt.Axes, rows: list[dict[str, float | str]]) -> None:
    ax.axis("off")
    headers = ["Method", "AP x1e-3", "AP50 x1e-3", "Recall", "F1 x1e-3", "Interpretation"]
    widths = [0.22, 0.14, 0.14, 0.10, 0.13, 0.27]
    x0 = 0.02
    y = 0.92
    row_h = 0.115
    header_color = "#e8eef6"
    line_color = "#d7e0ea"
    ax.add_patch(Rectangle((x0, y), sum(widths), row_h, facecolor=header_color, edgecolor=line_color))
    x = x0
    for header, width in zip(headers, widths):
        ax.text(x + 0.008, y + row_h * 0.55, header, va="center", ha="left", fontsize=9, weight="bold", color="#172033")
        x += width

    y -= row_h
    for idx, row in enumerate(rows):
        method = str(row["method"])
        face = "#fff5c7" if method == "SAFR-YOLO" else ("#eef7ee" if idx == 0 else "#ffffff")
        ax.add_patch(Rectangle((x0, y), sum(widths), row_h, facecolor=face, edgecolor=line_color))
        cells = [
            method,
            metric_text(float(row["ap"]), float(row["ap_std"]), 1000.0),
            metric_text(float(row["ap50"]), float(row["ap50_std"]), 1000.0),
            f"{float(row['recall']):.4f}",
            metric_text(float(row["f1"]), float(row["f1_std"]), 1000.0),
            str(row["note"]),
        ]
        x = x0
        for cell, width in zip(cells, widths):
            weight = "bold" if method == "SAFR-YOLO" else "normal"
            ax.text(x + 0.008, y + row_h * 0.55, cell, va="center", ha="left", fontsize=8.5, color="#172033", weight=weight)
            x += width
        y -= row_h


def build_dashboard(rows: list[dict[str, float | str]], out_path: Path, *, paper_style: bool = False) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    labels = [str(row["method"]) for row in rows]
    ap = [float(row["ap"]) * 1000.0 for row in rows]
    ap50 = [float(row["ap50"]) * 1000.0 for row in rows]
    recall = [float(row["recall"]) for row in rows]
    f1 = [float(row["f1"]) * 1000.0 for row in rows]
    ypos = list(range(len(rows)))

    plt.rcParams.update({"font.family": "DejaVu Sans", "axes.titleweight": "bold"})
    fig = plt.figure(figsize=(14, 8.4 if paper_style else 9), dpi=170)
    gs = fig.add_gridspec(2, 2, height_ratios=[1.0, 1.25], hspace=0.35, wspace=0.22)
    fig.patch.set_facecolor("#f5f7fb")
    if paper_style:
        fig.text(
            0.04,
            0.965,
            "Six detector variants, seeds 42/123/2026. Values are diagnostic only because the converted TinyPerson split is sparse.",
            fontsize=10,
            color="#475569",
        )
    else:
        fig.suptitle("TinyPerson 640 Supplementary Stress Test", x=0.04, ha="left", fontsize=18, weight="bold", color="#111827")
        fig.text(
            0.04,
            0.925,
            "Six detector variants, seeds 42/123/2026. Values are diagnostic only because the converted TinyPerson split is sparse.",
            fontsize=10,
            color="#475569",
        )

    ax1 = fig.add_subplot(gs[0, 0])
    ax1.set_facecolor("#ffffff")
    ax1.barh([y - 0.17 for y in ypos], ap, height=0.28, color="#2563eb", label="AP")
    ax1.barh([y + 0.17 for y in ypos], ap50, height=0.28, color="#f97316", label="AP50")
    ax1.set_yticks(ypos)
    ax1.set_yticklabels(labels, fontsize=9)
    ax1.invert_yaxis()
    ax1.set_xlabel("score x 1e-3")
    ax1.set_title("Detection Accuracy")
    ax1.grid(axis="x", color="#e5e7eb")
    ax1.legend(frameon=False, loc="lower right")
    for y, value in zip(ypos, ap50):
        ax1.text(value + 0.02, y + 0.17, f"{value:.3f}", va="center", fontsize=8, color="#334155")

    ax2 = fig.add_subplot(gs[0, 1])
    ax2.set_facecolor("#ffffff")
    ax2.barh([y - 0.17 for y in ypos], recall, height=0.28, color="#16a34a", label="Recall")
    ax2.barh([y + 0.17 for y in ypos], f1, height=0.28, color="#dc2626", label="F1 x1e-3")
    ax2.set_yticks(ypos)
    ax2.set_yticklabels(labels, fontsize=9)
    ax2.invert_yaxis()
    ax2.set_xlabel("score")
    ax2.set_title("Recall and F1")
    ax2.grid(axis="x", color="#e5e7eb")
    ax2.legend(frameon=False, loc="lower right")

    ax3 = fig.add_subplot(gs[1, :])
    ax3.set_facecolor("#ffffff")
    draw_table(ax3, rows)
    fig.text(
        0.04,
        0.04,
        "Use in supplementary as a domain-shift and dataset-conversion limitation check, not as the main VisDrone detector claim.",
        fontsize=9,
        color="#64748b",
    )
    fig.savefig(out_path, bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--summary", default="outputs/experiments/tinyperson_640/summary.csv")
    parser.add_argument("--out", default="outputs/reports/live/tinyperson_640_dashboard.png")
    parser.add_argument("--paper-out", default="paper/figures/results/paper_fig12_tinyperson_640_stress.png")
    parser.add_argument("--tex-out", default="paper/tables/tinyperson_640_stress_table.tex")
    args = parser.parse_args()

    rows = read_rows(Path(args.summary))
    for output in [Path(args.out), Path(args.paper_out)]:
        build_dashboard(rows, output, paper_style=output.name.startswith("paper_fig"))
        print(output)
    write_tex(rows, Path(args.tex_out))
    print(args.tex_out)


if __name__ == "__main__":
    main()
