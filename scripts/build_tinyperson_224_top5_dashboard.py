"""Build the TinyPerson224 auxiliary stress-test dashboard.

This dashboard is intentionally separate from the main detector dashboard.
TinyPerson224 is an internal domain-transfer stress check only, not a paper
comparison claim.
"""

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
    "ProposedSize-P2P4BalancedSelfAttnTinyFReLU-yolo11l-TinyPerson224": "Ours",
    "YOLOv11l-TinyPerson224": "YOLOv11l",
    "YOLOv8l-TinyPerson224": "YOLOv8l",
    "YOLOv9c-TinyPerson224": "YOLOv9c",
    "YOLOv9m-TinyPerson224": "YOLOv9m",
}

NOTE_MAP = {
    "Ours": "internal auxiliary only",
    "YOLOv11l": "large YOLO baseline",
    "YOLOv8l": "large YOLO baseline",
    "YOLOv9c": "strong YOLO baseline",
    "YOLOv9m": "medium YOLO baseline",
}


def as_float(value: str | None) -> float:
    if value in (None, ""):
        return 0.0
    return float(value)


def clean_name(method: str) -> str:
    if method in NAME_MAP:
        return NAME_MAP[method]
    name = method
    replacements = [
        ("-TinyPerson224Aux", ""),
        ("-TinyPerson224", ""),
        (" TinyPerson224Aux reimplementation", ""),
        (" TinyPerson224Aux high-resolution reproduction", ""),
        (" TinyPerson224Aux inspired reproduction", ""),
        (" TinyPerson224Aux module reproduction", ""),
        (" reimplementation", ""),
    ]
    for old, new in replacements:
        name = name.replace(old, new)
    return name


def read_summary(path: Path, max_rows: int) -> tuple[list[dict[str, str | float]], int]:
    if not path.exists():
        return [], 0
    rows: list[dict[str, str | float]] = []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            name = clean_name(row["method"])
            rows.append(
                {
                    "method": name,
                    "input": "224",
                    "seeds": row.get("seeds", ""),
                    "seed_count": row.get("seed_count", ""),
                    "ap": as_float(row.get("best_AP_mean")),
                    "ap_std": as_float(row.get("best_AP_std")),
                    "ap50": as_float(row.get("best_AP50_mean")),
                    "ap50_std": as_float(row.get("best_AP50_std")),
                    "precision": as_float(row.get("best_precision_mean")),
                    "recall": as_float(row.get("best_recall_mean")),
                    "f1": as_float(row.get("best_F1_mean")),
                    "roc_auc": as_float(row.get("ROC-AUC_mean")),
                    "note": NOTE_MAP.get(name, "auxiliary diagnostic"),
                }
            )
    rows = sorted(rows, key=lambda item: (float(item["ap"]), float(item["ap50"])), reverse=True)
    return rows[:max_rows], len(rows)


def metric(value: float, digits: int = 5) -> str:
    if value == 0:
        return "0"
    if abs(value) < 0.001:
        return f"{value:.2e}"
    return f"{value:.{digits}f}"


def draw_table(ax: plt.Axes, rows: list[dict[str, str | float]]) -> None:
    ax.axis("off")
    headers = ["Model", "Input", "Seeds", "AP", "AP50", "P", "R", "F1", "ROC-AUC", "Paper use"]
    widths = [0.15, 0.06, 0.12, 0.09, 0.09, 0.08, 0.08, 0.09, 0.09, 0.15]
    x0 = 0.015
    y = 0.91
    row_h = 0.105
    line = "#d8e1ec"
    header_face = "#e7eef8"

    ax.add_patch(Rectangle((x0, y), sum(widths), row_h, facecolor=header_face, edgecolor=line, linewidth=0.9))
    x = x0
    for header, width in zip(headers, widths):
        ax.text(x + 0.006, y + row_h * 0.56, header, ha="left", va="center", fontsize=9, weight="bold", color="#152033")
        x += width

    y -= row_h
    for row in rows:
        is_ours = row["method"] == "Ours"
        face = "#fff7d6" if is_ours else "#ffffff"
        ax.add_patch(Rectangle((x0, y), sum(widths), row_h, facecolor=face, edgecolor=line, linewidth=0.7))
        cells = [
            str(row["method"]),
            str(row["input"]),
            str(row["seeds"]),
            metric(float(row["ap"])),
            metric(float(row["ap50"])),
            metric(float(row["precision"])),
            f"{float(row['recall']):.4f}",
            metric(float(row["f1"])),
            f"{float(row['roc_auc']):.4f}",
            str(row["note"]),
        ]
        x = x0
        for cell, width in zip(cells, widths):
            ax.text(
                x + 0.006,
                y + row_h * 0.56,
                cell,
                ha="left",
                va="center",
                fontsize=8.5,
                weight="bold" if is_ours else "normal",
                color="#152033",
            )
            x += width
        y -= row_h


def write_markdown(rows: list[dict[str, str | float]], out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# TinyPerson224 Auxiliary Stress Test",
        "",
        "Policy: internal auxiliary only. Do not mix these rows with the VisDrone 1280 main detector table.",
        "",
        "| Model | Input | Seeds | AP | AP50 | Precision | Recall | F1 | ROC-AUC | Paper use |",
        "|---|---:|---|---:|---:|---:|---:|---:|---:|---|",
    ]
    for row in rows:
        lines.append(
            "| {method} | {input} | {seeds} | {ap} | {ap50} | {precision} | {recall:.4f} | {f1} | {roc_auc:.4f} | {note} |".format(
                method=row["method"],
                input=row["input"],
                seeds=row["seeds"],
                ap=metric(float(row["ap"])),
                ap50=metric(float(row["ap50"])),
                precision=metric(float(row["precision"])),
                recall=float(row["recall"]),
                f1=metric(float(row["f1"])),
                roc_auc=float(row["roc_auc"]),
                note=row["note"],
            )
        )
    lines.extend(
        [
            "",
            "Interpretation: AP/AP50 are near zero for every method, so this is a domain/protocol stress diagnostic rather than a publishable cross-dataset performance claim.",
        ]
    )
    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_dashboard(
    rows: list[dict[str, str | float]],
    out_path: Path,
    *,
    total_rows: int,
    title: str,
    subtitle: str,
    policy: str,
) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    plt.rcParams.update({"font.family": "DejaVu Sans"})
    fig = plt.figure(figsize=(14.5, 8.4), dpi=170)
    fig.patch.set_facecolor("#f6f8fb")
    gs = fig.add_gridspec(2, 2, height_ratios=[0.95, 1.2], hspace=0.28, wspace=0.22)

    fig.text(0.035, 0.965, title, ha="left", va="top", fontsize=19, weight="bold", color="#0f172a")
    fig.text(
        0.035,
        0.925,
        subtitle,
        ha="left",
        va="top",
        fontsize=10.5,
        color="#475569",
    )
    fig.text(
        0.72,
        0.955,
        "Internal-only stress diagnostic",
        ha="left",
        va="top",
        fontsize=10.5,
        color="#92400e",
        bbox={"boxstyle": "round,pad=0.35", "facecolor": "#fef3c7", "edgecolor": "#fbbf24"},
    )

    labels = [str(row["method"]) for row in rows]
    ypos = list(range(len(rows)))
    ap = [float(row["ap"]) * 10000.0 for row in rows]
    ap50 = [float(row["ap50"]) * 10000.0 for row in rows]
    recall = [float(row["recall"]) for row in rows]
    f1 = [float(row["f1"]) * 10000.0 for row in rows]

    ax1 = fig.add_subplot(gs[0, 0])
    ax1.set_facecolor("#ffffff")
    ax1.barh([y - 0.16 for y in ypos], ap, height=0.28, color="#2563eb", label="AP x1e4")
    ax1.barh([y + 0.16 for y in ypos], ap50, height=0.28, color="#f97316", label="AP50 x1e4")
    ax1.set_yticks(ypos)
    ax1.set_yticklabels(labels, fontsize=9)
    ax1.invert_yaxis()
    ax1.set_title("Near-zero detection AP", fontsize=11, weight="bold")
    ax1.grid(axis="x", color="#e5e7eb")
    ax1.legend(frameon=False, fontsize=8, loc="lower right")
    for y, value in zip(ypos, ap50):
        ax1.text(value + 0.02, y + 0.16, f"{value:.2f}", va="center", fontsize=8, color="#334155")

    ax2 = fig.add_subplot(gs[0, 1])
    ax2.set_facecolor("#ffffff")
    ax2.barh([y - 0.16 for y in ypos], recall, height=0.28, color="#16a34a", label="Recall")
    ax2.barh([y + 0.16 for y in ypos], f1, height=0.28, color="#dc2626", label="F1 x1e4")
    ax2.set_yticks(ypos)
    ax2.set_yticklabels(labels, fontsize=9)
    ax2.invert_yaxis()
    ax2.set_title("Recall exists but precision/F1 collapse", fontsize=11, weight="bold")
    ax2.grid(axis="x", color="#e5e7eb")
    ax2.legend(frameon=False, fontsize=8, loc="lower right")

    ax3 = fig.add_subplot(gs[1, :])
    ax3.set_facecolor("#ffffff")
    draw_table(ax3, rows)
    fig.text(
        0.035,
        0.025,
        f"{policy} Showing top {len(rows)} of {total_rows} rows by AP/AP50.",
        ha="left",
        va="bottom",
        fontsize=9.5,
        color="#475569",
    )
    fig.savefig(out_path, bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--summary", default="outputs/experiments/tinyperson_224_top5/summary.csv")
    parser.add_argument("--out", default="outputs/reports/live/tinyperson_224_top5_dashboard.png")
    parser.add_argument("--markdown", default="outputs/reports/live/tinyperson_224_top5_dashboard.md")
    parser.add_argument("--title", default="TinyPerson224 Auxiliary Stress Test")
    parser.add_argument(
        "--subtitle",
        default="Separate from the VisDrone 1280 paper comparison. Protocol: input=224, epochs=50, patience=5, batch=64, seeds=42/123/2026.",
    )
    parser.add_argument(
        "--policy",
        default="Conclusion: retain as an internal stress-test artifact only. Legacy TinyPerson 640/1280 diagnostics are archived and excluded from main/supplementary paper tables.",
    )
    parser.add_argument("--max-rows", type=int, default=12)
    args = parser.parse_args()

    rows, total_rows = read_summary(Path(args.summary), args.max_rows)
    build_dashboard(rows, Path(args.out), total_rows=total_rows, title=args.title, subtitle=args.subtitle, policy=args.policy)
    write_markdown(rows, Path(args.markdown))
    print(args.out)
    print(args.markdown)


if __name__ == "__main__":
    main()
