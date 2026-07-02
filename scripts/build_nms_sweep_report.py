"""Build CSV/Markdown/PNG summaries for detector NMS sweep results."""

from __future__ import annotations

import argparse
import csv
import os
from pathlib import Path
from typing import Any

from runtime.config import resolve_path
from scripts.watch_nms_sweep_scoreboard import (
    BASELINE_AP,
    BASELINE_AP50,
    BASELINE_F1,
    BASELINE_PARAMS_M,
    BASELINE_PRECISION,
    BASELINE_RECALL,
    TARGET_AP,
    TARGET_AP50,
    collect_rows,
    signed,
)


def setup_matplotlib() -> Any:
    os.environ.setdefault("MPLCONFIGDIR", str(resolve_path(".cache/matplotlib")))
    os.environ.setdefault("XDG_CACHE_HOME", str(resolve_path(".cache")))
    import matplotlib.pyplot as plt

    plt.rcParams.update(
        {
            "axes.grid": True,
            "axes.axisbelow": True,
            "grid.alpha": 0.25,
            "font.size": 10,
            "axes.titlesize": 13,
            "axes.labelsize": 10,
            "legend.fontsize": 9,
            "figure.facecolor": "white",
            "axes.facecolor": "white",
        }
    )
    return plt


def write_csv(rows: list[dict[str, Any]], out: Path, limit: int) -> Path:
    out.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "rank",
        "method",
        "conf",
        "iou",
        "nms",
        "AP",
        "AP50",
        "precision",
        "recall",
        "F1",
        "params_m",
        "delta_AP",
        "delta_AP50",
        "delta_F1",
        "delta_params_m",
        "strict_pass",
        "path",
    ]
    with out.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for rank, row in enumerate(rows[:limit], 1):
            params = row.get("params")
            writer.writerow(
                {
                    "rank": rank,
                    "method": row["method"],
                    "conf": row["conf"],
                    "iou": row["iou"],
                    "nms": row["nms"],
                    "AP": f"{row['ap']:.6f}",
                    "AP50": f"{row['ap50']:.6f}",
                    "precision": f"{row['precision']:.6f}",
                    "recall": f"{row['recall']:.6f}",
                    "F1": f"{row['f1']:.6f}",
                    "params_m": "" if params is None else f"{params:.4f}",
                    "delta_AP": f"{row['ap'] - BASELINE_AP:.6f}",
                    "delta_AP50": f"{row['ap50'] - BASELINE_AP50:.6f}",
                    "delta_F1": f"{row['f1'] - BASELINE_F1:.6f}",
                    "delta_params_m": "" if params is None else f"{params - BASELINE_PARAMS_M:.4f}",
                    "strict_pass": "true" if row["pass"] else "false",
                    "path": row["path"],
                }
            )
    return out


def write_markdown(rows: list[dict[str, Any]], out: Path, limit: int) -> Path:
    out.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# NMS Sweep Snapshot",
        "",
        f"Reference YOLOv11l mean: AP {BASELINE_AP:.4f}, AP50 {BASELINE_AP50:.4f}, "
        f"P {BASELINE_PRECISION:.4f}, R {BASELINE_RECALL:.4f}, F1 {BASELINE_F1:.4f}, "
        f"Params {BASELINE_PARAMS_M:.2f}M.",
        f"Strict pass threshold: AP >= {TARGET_AP:.4f} and AP50 >= {TARGET_AP50:.4f}.",
        "",
        "| Rank | Method | NMS | AP | AP50 | P | R | F1 | Params | Delta AP | Strict pass |",
        "| ---: | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for rank, row in enumerate(rows[:limit], 1):
        params = row.get("params")
        nms = f"conf={row['conf']}, iou={row['iou']}, {row['nms']}"
        lines.append(
            "| "
            f"{rank} | {row['method']} | {nms} | {row['ap']:.4f} | {row['ap50']:.4f} | "
            f"{row['precision']:.4f} | {row['recall']:.4f} | {row['f1']:.4f} | "
            f"{'-' if params is None else f'{params:.2f}M'} | "
            f"{signed(row['ap'] - BASELINE_AP)} | {'yes' if row['pass'] else 'no'} |"
        )
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return out


def plot_top(rows: list[dict[str, Any]], out: Path, limit: int) -> Path:
    out.parent.mkdir(parents=True, exist_ok=True)
    plt = setup_matplotlib()
    top = list(reversed(rows[:limit]))
    fig, ax = plt.subplots(figsize=(9.4, max(4.8, 0.52 * len(top) + 2.5)), constrained_layout=True)
    labels = [f"{row['method']}\nconf={row['conf']}, iou={row['iou']}, {row['nms']}" for row in top]
    aps = [row["ap"] for row in top]
    colors = ["#16A34A" if row["pass"] else "#2563EB" for row in top]
    bars = ax.barh(labels, aps, color=colors, alpha=0.88)
    ax.axvline(BASELINE_AP, color="#111827", linestyle="--", linewidth=1.2, label="YOLOv11l mean AP")
    ax.axvline(TARGET_AP, color="#DC2626", linestyle=":", linewidth=1.4, label="+1.5% AP target")
    ax.set_title("Top NMS Sweep Results")
    ax.set_xlabel("AP (mAP50-95)")
    ax.set_xlim(max(0.34, min(aps + [BASELINE_AP]) - 0.01), max(aps + [TARGET_AP]) + 0.006)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.legend(loc="lower right")
    for bar, row in zip(bars, top):
        ax.annotate(
            f"AP {row['ap']:.4f} / AP50 {row['ap50']:.4f}",
            xy=(bar.get_width(), bar.get_y() + bar.get_height() / 2),
            xytext=(5, 0),
            textcoords="offset points",
            va="center",
            fontsize=8,
        )
    fig.savefig(out, dpi=180)
    plt.close(fig)
    return out


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=8)
    parser.add_argument(
        "--roots",
        nargs="+",
        type=Path,
        default=[Path("outputs/detectors/nms_sweep_efficient"), Path("outputs/detectors/nms_sweep_accuracy")],
    )
    parser.add_argument("--csv-out", type=Path, default=Path("outputs/experiments/nms_sweep_summary.csv"))
    parser.add_argument("--md-out", type=Path, default=Path("outputs/reports/nms_sweep_snapshot.md"))
    parser.add_argument(
        "--fig-out",
        type=Path,
        default=Path("outputs/reports/paper_experiment_figures/detector/nms_sweep_top_results.png"),
    )
    args = parser.parse_args()
    rows = collect_rows(args.roots)
    csv_path = write_csv(rows, args.csv_out, args.limit)
    md_path = write_markdown(rows, args.md_out, args.limit)
    fig_path = plot_top(rows, args.fig_out, args.limit)
    print(csv_path)
    print(md_path)
    print(fig_path)


if __name__ == "__main__":
    main()
