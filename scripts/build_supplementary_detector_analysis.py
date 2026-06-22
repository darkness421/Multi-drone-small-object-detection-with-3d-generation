"""Build supplementary detector analysis figures.

This script is intentionally lightweight: it turns already-collected detector
CSV files into reviewer-facing supplementary artifacts. It does not train or
evaluate models. Use it after result collection for ablation heat maps and
input-size sweep plots.
"""

from __future__ import annotations

import argparse
import csv
import os
from collections import defaultdict
from pathlib import Path
from typing import Any

from runtime.config import resolve_path


DEFAULT_SUMMARY_CSVS = [
    Path("outputs/experiments/server_with_proposed_summary.csv"),
    Path("outputs/experiments/server_fresh/large_20260524_140922/server_baseline_summary.csv"),
    Path("outputs/experiments/server_fresh/large_20260524_140922/live/server_baseline_summary.csv"),
]

DEFAULT_RESULTS_CSVS = [
    Path("outputs/experiments/server_with_proposed_results.csv"),
    Path("outputs/experiments/server_fresh/large_20260524_140922/server_baseline_results.csv"),
    Path("outputs/experiments/server_fresh/large_20260524_140922/live/server_baseline_results.csv"),
]

ABLATION_METRICS = [
    ("AP", "best_AP_mean"),
    ("AP50", "best_AP50_mean"),
    ("Recall", "best_recall_mean"),
    ("F1", "best_F1_mean"),
]


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def read_many(paths: list[str | Path]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for path in paths:
        rows.extend(read_csv(resolve_path(path)))
    return rows


def as_float(value: Any) -> float | None:
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def mean(values: list[float]) -> float | None:
    values = [value for value in values if value is not None]
    if not values:
        return None
    return sum(values) / len(values)


def setup_matplotlib() -> Any:
    os.environ.setdefault("MPLCONFIGDIR", str(resolve_path(".cache/matplotlib")))
    os.environ.setdefault("XDG_CACHE_HOME", str(resolve_path(".cache")))
    import matplotlib.pyplot as plt

    plt.rcParams.update(
        {
            "axes.grid": False,
            "font.size": 10,
            "axes.titlesize": 13,
            "axes.labelsize": 10,
            "figure.facecolor": "white",
            "axes.facecolor": "white",
        }
    )
    return plt


def save_empty(out: Path, title: str, message: str) -> Path:
    plt = setup_matplotlib()
    out.parent.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(9.0, 4.8), constrained_layout=True)
    ax.axis("off")
    ax.set_title(title)
    ax.text(0.5, 0.5, message, ha="center", va="center", transform=ax.transAxes)
    fig.savefig(out, dpi=180)
    plt.close(fig)
    return out


def method_name(row: dict[str, str]) -> str:
    return row.get("method") or Path(row.get("model", "")).stem or "unknown"


def ablation_name(row: dict[str, str]) -> str:
    return row.get("ablation") or row.get("proposed_module") or "baseline"


def base_name(row: dict[str, str]) -> str:
    return row.get("base_model") or row.get("model") or method_name(row)


def row_score(row: dict[str, str]) -> float:
    value = as_float(row.get("best_AP_mean"))
    return value if value is not None else -1.0


def dedupe_summary(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    best: dict[tuple[str, str, str, str], dict[str, str]] = {}
    for row in rows:
        key = (
            row.get("dataset", ""),
            base_name(row),
            method_name(row),
            ablation_name(row),
        )
        old = best.get(key)
        if old is None or row_score(row) > row_score(old):
            best[key] = row
    return list(best.values())


def is_proposed_or_ablation(row: dict[str, str]) -> bool:
    return (
        row.get("is_proposed") == "true"
        or bool(row.get("ablation"))
        or (row.get("method") or "").startswith("Proposed")
        or (row.get("proposed_module") or "") not in {"", "baseline"}
    )


def control_rows(rows: list[dict[str, str]]) -> dict[str, dict[str, str]]:
    controls: dict[str, dict[str, str]] = {}
    for row in rows:
        name = ablation_name(row).lower()
        if name in {"control", "baseline", "resolution_control"}:
            old = controls.get(base_name(row))
            if old is None or row_score(row) > row_score(old):
                controls[base_name(row)] = row
    return controls


def build_ablation_heatmap(summary_rows: list[dict[str, str]], out_dir: Path) -> list[Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    rows = [row for row in dedupe_summary(summary_rows) if is_proposed_or_ablation(row)]
    controls = control_rows(rows)
    rows = [
        row
        for row in rows
        if ablation_name(row).lower() not in {"control", "baseline", "resolution_control"}
        and as_float(row.get("best_AP_mean")) is not None
    ]
    rows = sorted(rows, key=lambda row: (base_name(row), -row_score(row), ablation_name(row)))[:18]
    csv_path = out_dir / "ablation_delta_heatmap.csv"
    png_path = out_dir / "figures" / "ablation_delta_heatmap.png"

    if not rows:
        csv_path.write_text("label,baseline_reference,AP,AP50,Recall,F1\n", encoding="utf-8")
        return [csv_path, save_empty(png_path, "Ablation Delta Heatmap", "No ablation rows yet")]

    matrix: list[list[float]] = []
    labels: list[str] = []
    table_rows: list[list[str]] = []
    for row in rows:
        base = base_name(row)
        reference = controls.get(base)
        labels.append(f"{Path(base).stem}\n{ablation_name(row)}")
        values: list[float] = []
        table_row = [labels[-1].replace("\n", " / "), method_name(reference) if reference else "absolute"]
        for _, metric in ABLATION_METRICS:
            current = as_float(row.get(metric)) or 0.0
            ref_value = as_float(reference.get(metric)) if reference else None
            value = current - ref_value if ref_value is not None else current
            values.append(value)
            table_row.append(f"{value:.5f}")
        matrix.append(values)
        table_rows.append(table_row)

    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(["label", "baseline_reference", *[name for name, _ in ABLATION_METRICS]])
        writer.writerows(table_rows)

    plt = setup_matplotlib()
    import numpy as np

    data = np.array(matrix, dtype=float)
    limit = max(abs(float(data.min())), abs(float(data.max())), 1e-4)
    fig_h = max(5.2, 0.36 * len(labels) + 2.6)
    fig, ax = plt.subplots(figsize=(8.6, fig_h), constrained_layout=True)
    image = ax.imshow(data, cmap="RdYlGn", vmin=-limit, vmax=limit, aspect="auto")
    ax.set_title("Ablation Delta Heatmap vs Control")
    ax.set_xticks(range(len(ABLATION_METRICS)))
    ax.set_xticklabels([name for name, _ in ABLATION_METRICS])
    ax.set_yticks(range(len(labels)))
    ax.set_yticklabels(labels)
    for y_idx, row_values in enumerate(data):
        for x_idx, value in enumerate(row_values):
            ax.text(x_idx, y_idx, f"{value:+.3f}", ha="center", va="center", fontsize=8)
    colorbar = fig.colorbar(image, ax=ax, shrink=0.78)
    colorbar.set_label("metric delta")
    png_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(png_path, dpi=220)
    plt.close(fig)
    return [csv_path, png_path]


def completed_result_rows(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    return [row for row in rows if row.get("status", "completed") == "completed"]


def group_resolution_rows(rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, int], dict[str, list[float]]] = defaultdict(lambda: defaultdict(list))
    meta: dict[tuple[str, int], dict[str, str]] = {}
    for row in completed_result_rows(rows):
        imgsz_value = as_float(row.get("protocol_imgsz"))
        if imgsz_value is None:
            continue
        imgsz = int(imgsz_value)
        key = (method_name(row), imgsz)
        meta[key] = {"method": method_name(row), "imgsz": str(imgsz)}
        for metric in ["best_AP", "best_AP50", "best_recall", "best_F1", "FPS", "latency_ms"]:
            value = as_float(row.get(metric))
            if value is not None:
                grouped[key][metric].append(value)
    out: list[dict[str, Any]] = []
    for key, values in grouped.items():
        item = dict(meta[key])
        for metric, metric_values in values.items():
            item[metric] = mean(metric_values)
            item[f"{metric}_n"] = len(metric_values)
        out.append(item)
    return sorted(out, key=lambda row: (row["method"], int(row["imgsz"])))


def write_resolution_note(out_dir: Path, message: str) -> Path:
    path = out_dir / "input_size_sweep_status.md"
    path.write_text(message.rstrip() + "\n", encoding="utf-8")
    return path


def plot_resolution_scores(rows: list[dict[str, Any]], out: Path) -> Path | None:
    methods = sorted({row["method"] for row in rows})
    sizes = sorted({int(row["imgsz"]) for row in rows})
    if len(sizes) < 2:
        return None
    plt = setup_matplotlib()
    fig, ax = plt.subplots(figsize=(9.2, 5.6), constrained_layout=True)
    for method in methods:
        method_rows = [row for row in rows if row["method"] == method]
        method_rows.sort(key=lambda row: int(row["imgsz"]))
        x_values = [int(row["imgsz"]) for row in method_rows]
        ap = [row.get("best_AP") or 0.0 for row in method_rows]
        ap50 = [row.get("best_AP50") or 0.0 for row in method_rows]
        ax.plot(x_values, ap, marker="o", linewidth=2.0, label=f"{method} AP")
        ax.plot(x_values, ap50, marker="s", linewidth=1.6, linestyle="--", label=f"{method} AP50")
    ax.set_title("Input Pixel Size vs Detection Performance")
    ax.set_xlabel("input size (square pixels)")
    ax.set_ylabel("score")
    ax.set_xticks(sizes)
    ax.grid(axis="y", alpha=0.24)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.legend(ncol=2, fontsize=8)
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, dpi=220)
    plt.close(fig)
    return out


def plot_resolution_efficiency(rows: list[dict[str, Any]], out: Path) -> Path | None:
    methods = sorted({row["method"] for row in rows})
    sizes = sorted({int(row["imgsz"]) for row in rows})
    if len(sizes) < 2:
        return None
    plt = setup_matplotlib()
    fig, ax1 = plt.subplots(figsize=(9.2, 5.6), constrained_layout=True)
    ax2 = ax1.twinx()
    for method in methods:
        method_rows = [row for row in rows if row["method"] == method]
        method_rows.sort(key=lambda row: int(row["imgsz"]))
        x_values = [int(row["imgsz"]) for row in method_rows]
        fps = [row.get("FPS") or 0.0 for row in method_rows]
        latency = [row.get("latency_ms") or 0.0 for row in method_rows]
        if any(fps):
            ax1.plot(x_values, fps, marker="o", linewidth=2.0, label=f"{method} FPS")
        if any(latency):
            ax2.plot(x_values, latency, marker="s", linewidth=1.6, linestyle="--", label=f"{method} latency")
    ax1.set_title("Input Pixel Size vs Runtime")
    ax1.set_xlabel("input size (square pixels)")
    ax1.set_ylabel("FPS")
    ax2.set_ylabel("latency (ms)")
    ax1.set_xticks(sizes)
    ax1.grid(axis="y", alpha=0.24)
    for ax in (ax1, ax2):
        ax.spines["top"].set_visible(False)
    handles1, labels1 = ax1.get_legend_handles_labels()
    handles2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(handles1 + handles2, labels1 + labels2, ncol=2, fontsize=8, loc="upper center", bbox_to_anchor=(0.5, -0.12))
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, dpi=220, bbox_inches="tight")
    plt.close(fig)
    return out


def build_resolution_sweep(results_rows: list[dict[str, str]], out_dir: Path) -> list[Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    rows = group_resolution_rows(results_rows)
    csv_path = out_dir / "input_size_sweep.csv"
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        fieldnames = ["method", "imgsz", "best_AP", "best_AP50", "best_recall", "best_F1", "FPS", "latency_ms"]
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in fieldnames})
    written = [csv_path]
    score_plot = plot_resolution_scores(rows, out_dir / "figures" / "input_size_ap_ap50.png")
    efficiency_plot = plot_resolution_efficiency(rows, out_dir / "figures" / "input_size_efficiency.png")
    if score_plot and efficiency_plot:
        written.extend([score_plot, efficiency_plot])
    else:
        for stale in [
            out_dir / "figures" / "input_size_ap_ap50.png",
            out_dir / "figures" / "input_size_efficiency.png",
        ]:
            if stale.exists():
                stale.unlink()
        written.append(
            write_resolution_note(
                out_dir,
                "Input-size figures are intentionally withheld until at least two "
                "high-resolution settings have completed.",
            )
        )
    return written


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--summary-csv", action="append", default=[str(path) for path in DEFAULT_SUMMARY_CSVS])
    parser.add_argument("--results-csv", action="append", default=[str(path) for path in DEFAULT_RESULTS_CSVS])
    parser.add_argument("--out-dir", default="outputs/reports/supplementary_detector")
    args = parser.parse_args()

    out_dir = resolve_path(args.out_dir)
    summary_rows = read_many(args.summary_csv)
    results_rows = read_many(args.results_csv)
    written = build_ablation_heatmap(summary_rows, out_dir)
    written.extend(build_resolution_sweep(results_rows, out_dir))
    for path in written:
        print(path)


if __name__ == "__main__":
    main()
