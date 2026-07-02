"""Collect TinyPerson eval-only input-size sweep artifacts.

This script reads eval_summary.json files produced by
scripts/ubuntu/run_tinyperson_eval_imgsz_sweep.sh. The sweep intentionally uses
symlinked checkpoint names instead of original best.pt paths so it does not
overwrite the metrics stored next to the completed TinyPerson training runs.
"""

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

os.environ.setdefault("MPLBACKEND", "Agg")
os.environ.setdefault("MPLCONFIGDIR", "/tmp/matplotlib")

import matplotlib.pyplot as plt


RUN_RE = re.compile(r"(?P<method>.+)_img(?P<imgsz>\d+)_seed(?P<seed>\d+)$")
TIMESTAMP_PREFIX_RE = re.compile(r"^\d{8}_\d{6}_")

LABELS = {
    "tinyperson_safr": "Ours",
    "tinyperson_safr_transfer": "Ours transfer",
    "tinyperson_yolov9m": "YOLOv9m",
}

NOTES = {
    "Ours": "legacy TinyPerson scratch run",
    "Ours transfer": "VisDrone-init TinyPerson fine-tune",
    "YOLOv9m": "strongest TinyPerson stress-test baseline",
}


def as_float(value: Any) -> float:
    if value is None or value == "":
        return 0.0
    return float(value)


def f1(precision: float, recall: float) -> float:
    denom = precision + recall
    if denom <= 0:
        return 0.0
    return 2.0 * precision * recall / denom


def parse_run(summary_path: Path) -> dict[str, Any] | None:
    try:
        payload = json.loads(summary_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
    run_dir = Path(payload.get("run_dir", summary_path.parents[2]))
    match = RUN_RE.search(run_dir.name)
    if not match:
        return None
    metrics = payload.get("metrics", {})
    precision = as_float(metrics.get("precision"))
    recall = as_float(metrics.get("recall"))
    run_key = TIMESTAMP_PREFIX_RE.sub("", match.group("method"))
    method = LABELS.get(run_key, run_key)
    return {
        "method": method,
        "run_key": run_key,
        "imgsz": int(match.group("imgsz")),
        "seed": int(match.group("seed")),
        "AP": as_float(metrics.get("AP")),
        "AP50": as_float(metrics.get("AP50")),
        "precision": precision,
        "recall": recall,
        "F1": f1(precision, recall),
        "latency_ms": as_float(metrics.get("latency_ms")),
        "FPS": as_float(metrics.get("FPS")),
        "note": NOTES.get(method, "eval-only diagnostic"),
        "run_dir": str(run_dir),
    }


def collect_rows(root: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for summary_path in sorted(root.glob("*/metrics/eval_summary.json")):
        row = parse_run(summary_path)
        if row:
            rows.append(row)
    return sorted(rows, key=lambda row: (row["method"], row["imgsz"], row["seed"]))


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    fieldnames = list(rows[0].keys())
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def summarize(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[tuple[str, int], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        groups[(row["method"], row["imgsz"])].append(row)

    out: list[dict[str, Any]] = []
    for (method, imgsz), group in groups.items():
        item: dict[str, Any] = {
            "method": method,
            "imgsz": imgsz,
            "seed_count": len(group),
            "seeds": ",".join(str(row["seed"]) for row in sorted(group, key=lambda r: r["seed"])),
            "note": group[0]["note"],
        }
        for metric in ["AP", "AP50", "precision", "recall", "F1", "latency_ms", "FPS"]:
            values = [float(row[metric]) for row in group]
            item[f"{metric}_mean"] = mean(values)
            item[f"{metric}_std"] = stdev(values) if len(values) > 1 else 0.0
        out.append(item)
    return sorted(out, key=lambda row: (row["method"], int(row["imgsz"])))


def latex_escape(value: str) -> str:
    return (
        value.replace("\\", "\\textbackslash{}")
        .replace("&", "\\&")
        .replace("%", "\\%")
        .replace("_", "\\_")
        .replace("#", "\\#")
    )


def metric(mean_value: float, std_value: float) -> str:
    return f"{mean_value:.4f} $\\pm$ {std_value:.4f}"


def metric_scaled(mean_value: float, std_value: float, scale: float = 1000.0) -> str:
    return f"{mean_value * scale:.3f} $\\pm$ {std_value * scale:.3f}"


def write_tex(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "\\begin{tabular}{llrrrrrl}",
        "\\toprule",
        "Method & Eval size & AP $\\times 10^{-3}$ & AP50 $\\times 10^{-3}$ & Recall & F1 $\\times 10^{-3}$ & Seeds & Note \\\\",
        "\\midrule",
    ]
    for row in rows:
        lines.append(
            f"{latex_escape(str(row['method']))} & {int(row['imgsz'])} & "
            f"{metric_scaled(float(row['AP_mean']), float(row['AP_std']))} & "
            f"{metric_scaled(float(row['AP50_mean']), float(row['AP50_std']))} & "
            f"{metric(float(row['recall_mean']), float(row['recall_std']))} & "
            f"{metric_scaled(float(row['F1_mean']), float(row['F1_std']))} & "
            f"{latex_escape(str(row['seeds']))} & {latex_escape(str(row['note']))} \\\\"
        )
    lines.extend(["\\bottomrule", "\\end{tabular}", ""])
    path.write_text("\n".join(lines), encoding="utf-8")


def draw_dashboard(path: Path, rows: list[dict[str, Any]], *, paper_style: bool = False) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        return

    methods = sorted({str(row["method"]) for row in rows})
    sizes = sorted({int(row["imgsz"]) for row in rows})
    colors = {
        "Ours": "#2563eb",
        "Ours transfer": "#f97316",
        "YOLOv9m": "#16a34a",
    }
    fig, axes = plt.subplots(1, 2, figsize=(13, 5.5), dpi=170)
    fig.patch.set_facecolor("#f5f7fb")
    if not paper_style:
        fig.suptitle("TinyPerson Eval-Only Input-Size Sweep", x=0.04, ha="left", fontsize=16, weight="bold")
        fig.text(
            0.04,
            0.925,
            "Same completed checkpoints, evaluated at multiple image sizes. This is supplementary diagnostic evidence only.",
            fontsize=9,
            color="#475569",
        )
        fig.subplots_adjust(top=0.84)
    else:
        fig.subplots_adjust(top=0.95)

    row_map = {(str(row["method"]), int(row["imgsz"])): row for row in rows}
    for ax, metric_name, ylabel in [
        (axes[0], "AP50", "AP50"),
        (axes[1], "recall", "Recall"),
    ]:
        ax.set_facecolor("#ffffff")
        for method in methods:
            values = [float(row_map.get((method, size), {}).get(f"{metric_name}_mean", math.nan)) for size in sizes]
            ax.plot(sizes, values, marker="o", linewidth=2.2, label=method, color=colors.get(method))
        ax.set_xlabel("eval image size")
        ax.set_ylabel(ylabel)
        ax.grid(True, color="#e5e7eb", linewidth=0.8)
        ax.set_xticks(sizes)
    axes[0].legend(frameon=False, loc="best")
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default="outputs/detectors/tinyperson_eval_imgsz_sweep")
    parser.add_argument("--out-dir", default="outputs/experiments/tinyperson_eval_imgsz_sweep")
    parser.add_argument("--dashboard", default="outputs/reports/live/tinyperson_eval_imgsz_sweep_dashboard.png")
    parser.add_argument("--paper-figure", default="paper/figures/results/paper_fig13_tinyperson_eval_imgsz_sweep.png")
    parser.add_argument("--tex-out", default="paper/tables/tinyperson_eval_imgsz_sweep_table.tex")
    args = parser.parse_args()

    rows = collect_rows(Path(args.root))
    out_dir = Path(args.out_dir)
    write_csv(out_dir / "results.csv", rows)
    summary = summarize(rows)
    write_csv(out_dir / "summary.csv", summary)
    write_tex(Path(args.tex_out), summary)
    draw_dashboard(Path(args.dashboard), summary)
    draw_dashboard(Path(args.paper_figure), summary, paper_style=True)

    report = [
        "# TinyPerson Eval-Only Input-Size Sweep",
        "",
        f"- Results: `{out_dir / 'results.csv'}`",
        f"- Summary: `{out_dir / 'summary.csv'}`",
        f"- Dashboard: `{args.dashboard}`",
        f"- Paper figure: `{args.paper_figure}`",
        f"- Paper table: `{args.tex_out}`",
        f"- Completed eval rows: `{len(rows)}`",
        "",
        "This sweep reuses completed checkpoints and changes only eval-time image size.",
        "It is supplementary diagnostic evidence and should not replace the VisDrone 1280 main comparison.",
        "",
    ]
    (out_dir / "README.md").write_text("\n".join(report), encoding="utf-8")
    print(json.dumps({"rows": len(rows), "summary_rows": len(summary), "out_dir": str(out_dir)}, indent=2))


if __name__ == "__main__":
    main()
