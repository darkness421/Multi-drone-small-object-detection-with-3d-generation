"""Build paper-ready summaries for the final detector input-resolution sweep."""

from __future__ import annotations

import argparse
import csv
import json
import math
import os
import re
from collections import defaultdict
from pathlib import Path
from statistics import mean, stdev
from typing import Any


PARAMS_M = {
    "ours": 20.82,
    "yolov9c": 25.326958,
}

DISPLAY_NAME = {
    "ours": "Ours",
    "yolov9c": "YOLOv9c",
}


RUN_RE = re.compile(
    r"final_input_(?P<model>[^_]+)_seed(?P<seed>\d+)_imgsz(?P<imgsz>\d+)_conf(?P<conf>[^_]+)_iou(?P<iou>[^_]+)_(?P<nms>.+)$"
)


def setup_matplotlib() -> Any:
    os.environ.setdefault("MPLCONFIGDIR", ".cache/matplotlib")
    os.environ.setdefault("XDG_CACHE_HOME", ".cache")
    import matplotlib.pyplot as plt

    plt.rcParams.update(
        {
            "axes.grid": True,
            "axes.axisbelow": True,
            "grid.alpha": 0.25,
            "font.size": 10,
            "axes.labelsize": 10,
            "legend.fontsize": 9,
            "figure.facecolor": "white",
            "axes.facecolor": "white",
        }
    )
    return plt


def parse_float_token(value: str) -> float:
    return float(value.replace("p", "."))


def f1_score(precision: float, recall: float) -> float:
    denom = precision + recall
    if denom <= 0:
        return 0.0
    return 2.0 * precision * recall / denom


def collect_rows(root: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for summary_path in sorted(root.glob("*/metrics/eval_summary.json")):
        run_name = summary_path.parents[1].name
        bare_run_name = "_".join(run_name.split("_")[1:]) if run_name[:8].isdigit() else run_name
        match = RUN_RE.search(bare_run_name)
        if not match:
            continue
        data = json.loads(summary_path.read_text(encoding="utf-8"))
        metrics = data.get("metrics", {})
        model_key = match.group("model")
        precision = float(metrics.get("precision", 0.0))
        recall = float(metrics.get("recall", 0.0))
        row = {
            "model_key": model_key,
            "model": DISPLAY_NAME.get(model_key, model_key),
            "method_raw": data.get("method", ""),
            "seed": int(match.group("seed")),
            "imgsz": int(match.group("imgsz")),
            "conf": parse_float_token(match.group("conf")),
            "iou": parse_float_token(match.group("iou")),
            "nms_type": match.group("nms"),
            "AP": float(metrics.get("AP", 0.0)),
            "AP50": float(metrics.get("AP50", 0.0)),
            "AP75": float(metrics.get("AP75", 0.0)),
            "precision": precision,
            "recall": recall,
            "F1": f1_score(precision, recall),
            "latency_ms": float(metrics.get("latency_ms", 0.0)),
            "FPS": float(metrics.get("FPS", 0.0)),
            "params_m": PARAMS_M.get(model_key, math.nan),
            "run_dir": str(data.get("run_dir", summary_path.parents[1])),
            "summary_path": str(summary_path),
        }
        rows.append(row)
    rows.sort(key=lambda r: (r["model_key"], r["seed"], r["imgsz"]))
    return rows


def write_rows_csv(rows: list[dict[str, Any]], out: Path) -> Path:
    out.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "model",
        "model_key",
        "method_raw",
        "seed",
        "imgsz",
        "conf",
        "iou",
        "nms_type",
        "AP",
        "AP50",
        "AP75",
        "precision",
        "recall",
        "F1",
        "latency_ms",
        "FPS",
        "params_m",
        "run_dir",
    ]
    with out.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row[field] for field in fields})
    return out


def summarize(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, int], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[(row["model_key"], row["imgsz"])].append(row)

    summary: list[dict[str, Any]] = []
    for (model_key, imgsz), group in sorted(grouped.items()):
        metrics = ["AP", "AP50", "AP75", "precision", "recall", "F1", "latency_ms", "FPS"]
        out: dict[str, Any] = {
            "model": DISPLAY_NAME.get(model_key, model_key),
            "model_key": model_key,
            "imgsz": imgsz,
            "conf": group[0]["conf"],
            "iou": group[0]["iou"],
            "nms_type": group[0]["nms_type"],
            "seeds": " ".join(str(row["seed"]) for row in sorted(group, key=lambda r: r["seed"])),
            "n": len(group),
            "params_m": PARAMS_M.get(model_key, math.nan),
        }
        for metric in metrics:
            values = [float(row[metric]) for row in group]
            out[f"{metric}_mean"] = mean(values)
            out[f"{metric}_std"] = stdev(values) if len(values) > 1 else 0.0
        summary.append(out)
    summary.sort(key=lambda r: (r["model_key"], r["imgsz"]))
    return summary


def write_summary_csv(summary: list[dict[str, Any]], out: Path) -> Path:
    out.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "model",
        "model_key",
        "imgsz",
        "conf",
        "iou",
        "nms_type",
        "seeds",
        "n",
        "params_m",
        "AP_mean",
        "AP_std",
        "AP50_mean",
        "AP50_std",
        "precision_mean",
        "precision_std",
        "recall_mean",
        "recall_std",
        "F1_mean",
        "F1_std",
        "latency_ms_mean",
        "latency_ms_std",
        "FPS_mean",
        "FPS_std",
    ]
    with out.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in summary:
            writer.writerow({field: row.get(field, "") for field in fields})
    return out


def write_markdown(rows: list[dict[str, Any]], summary: list[dict[str, Any]], out: Path) -> Path:
    out.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Final Detector Input-Resolution Sweep",
        "",
        "Scope: eval-only sweep on VisDrone2019-DET using the 1280-trained final checkpoints.",
        "This is supplementary sensitivity evidence, not a low-resolution training protocol.",
        "",
        f"Completed eval summaries: {len(rows)} / 24.",
        "",
        "| Model | Img | Seeds | AP | AP50 | P | R | F1 | Params | FPS |",
        "| --- | ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in summary:
        lines.append(
            "| "
            f"{row['model']} | {row['imgsz']} | {row['seeds']} | "
            f"{row['AP_mean']:.4f} +/- {row['AP_std']:.4f} | "
            f"{row['AP50_mean']:.4f} +/- {row['AP50_std']:.4f} | "
            f"{row['precision_mean']:.4f} | {row['recall_mean']:.4f} | "
            f"{row['F1_mean']:.4f} | {row['params_m']:.2f}M | {row['FPS_mean']:.1f} |"
        )
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return out


def plot_summary(summary: list[dict[str, Any]], out: Path) -> Path:
    out.parent.mkdir(parents=True, exist_ok=True)
    plt = setup_matplotlib()
    fig, axes = plt.subplots(1, 2, figsize=(10.4, 4.3), constrained_layout=True)
    colors = {"ours": "#0F766E", "yolov9c": "#2563EB"}
    markers = {"ours": "o", "yolov9c": "s"}
    for model_key in sorted({row["model_key"] for row in summary}):
        group = [row for row in summary if row["model_key"] == model_key]
        group.sort(key=lambda r: r["imgsz"])
        label = DISPLAY_NAME.get(model_key, model_key)
        x = [row["imgsz"] for row in group]
        axes[0].errorbar(
            x,
            [row["AP_mean"] for row in group],
            yerr=[row["AP_std"] for row in group],
            label=label,
            color=colors.get(model_key),
            marker=markers.get(model_key, "o"),
            linewidth=2,
            capsize=3,
        )
        axes[1].errorbar(
            x,
            [row["AP50_mean"] for row in group],
            yerr=[row["AP50_std"] for row in group],
            label=label,
            color=colors.get(model_key),
            marker=markers.get(model_key, "o"),
            linewidth=2,
            capsize=3,
        )

    axes[0].set_xlabel("Evaluation image size")
    axes[0].set_ylabel("AP (mAP50-95)")
    axes[1].set_xlabel("Evaluation image size")
    axes[1].set_ylabel("AP50")
    for ax in axes:
        ax.set_xticks([640, 960, 1280, 1536])
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.legend(frameon=True)
    fig.savefig(out, dpi=220)
    plt.close(fig)
    return out


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path("outputs/detectors/final_input_resolution_sweep"))
    parser.add_argument(
        "--rows-out",
        type=Path,
        default=Path("outputs/experiments/final_input_resolution_sweep/results.csv"),
    )
    parser.add_argument(
        "--summary-out",
        type=Path,
        default=Path("outputs/experiments/final_input_resolution_sweep/summary.csv"),
    )
    parser.add_argument(
        "--md-out",
        type=Path,
        default=Path("outputs/reports/live/final_input_resolution_summary.md"),
    )
    parser.add_argument(
        "--fig-out",
        type=Path,
        default=Path("outputs/reports/live/paper_fig15_final_input_resolution_sweep.png"),
    )
    parser.add_argument(
        "--paper-fig-out",
        type=Path,
        default=Path("paper/figures/results/final_detector_input_resolution_sweep.png"),
    )
    args = parser.parse_args()

    rows = collect_rows(args.root)
    summary = summarize(rows)
    rows_path = write_rows_csv(rows, args.rows_out)
    summary_path = write_summary_csv(summary, args.summary_out)
    md_path = write_markdown(rows, summary, args.md_out)
    fig_path = plot_summary(summary, args.fig_out)
    paper_fig_path = plot_summary(summary, args.paper_fig_out)
    print(rows_path)
    print(summary_path)
    print(md_path)
    print(fig_path)
    print(paper_fig_path)


if __name__ == "__main__":
    main()
