"""Build a live dashboard for the corrected TinyPerson corner-window queue."""

from __future__ import annotations

import argparse
import csv
import json
import os
import re
from pathlib import Path
from typing import Any

os.environ.setdefault("MPLBACKEND", "Agg")
os.environ.setdefault("MPLCONFIGDIR", "/tmp/matplotlib")

import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle


RUN_RE = re.compile(r"(?P<method>yolov9m|ours)_tinyperson_corner_original_img(?P<imgsz>\d+)_seed(?P<seed>\d+)")
LABELS = {"yolov9m": "YOLOv9m", "ours": "Ours"}
QUEUE_LOG = Path("outputs/logs/tinyperson_corner_original/queue.log")


def as_float(value: Any) -> float:
    if value in (None, ""):
        return 0.0
    return float(value)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def queue_job_finished(method_key: str, seed: int) -> bool:
    if not QUEUE_LOG.exists():
        return False
    marker = f"FINISH TinyPerson corner/original job={method_key} seed={seed}"
    try:
        return marker in QUEUE_LOG.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return False


def parse_run(run_dir: Path) -> dict[str, Any] | None:
    match = RUN_RE.search(run_dir.name)
    results_csv = run_dir / "ultralytics" / "results.csv"
    if not match or not results_csv.exists():
        return None
    rows = read_csv(results_csv)
    if not rows:
        return None
    parsed = []
    for row in rows:
        parsed.append(
            {
                "epoch": int(float(row.get("epoch", 0))),
                "precision": as_float(row.get("metrics/precision(B)")),
                "recall": as_float(row.get("metrics/recall(B)")),
                "AP50": as_float(row.get("metrics/mAP50(B)")),
                "AP": as_float(row.get("metrics/mAP50-95(B)")),
                "box_loss": as_float(row.get("train/box_loss")),
                "cls_loss": as_float(row.get("train/cls_loss")),
            }
        )
    latest = parsed[-1]
    best = max(parsed, key=lambda item: item["AP"])
    last_epoch = latest["epoch"]
    method_key = match.group("method")
    seed = int(match.group("seed"))
    status = "running"
    if queue_job_finished(method_key, seed) or ((run_dir / "ultralytics" / "weights" / "last.pt").exists() and last_epoch >= 100):
        status = "complete"
    return {
        "method": LABELS.get(method_key, method_key),
        "seed": seed,
        "imgsz": int(match.group("imgsz")),
        "latest": latest,
        "best": best,
        "run_dir": run_dir.as_posix(),
        "status": status,
    }


def collect(root: Path) -> list[dict[str, Any]]:
    rows = []
    for run_dir in sorted(root.glob("*_tinyperson_corner_original_img*_seed*")):
        row = parse_run(run_dir)
        if row:
            rows.append(row)
    return sorted(rows, key=lambda row: (row["method"] != "Ours", row["method"], row["seed"]))


def draw(rows: list[dict[str, Any]], out: Path) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    fig = plt.figure(figsize=(14, 7.2), dpi=170)
    fig.patch.set_facecolor("#f5f7fb")
    fig.suptitle("TinyPerson Corrected Original-Window 1280 Diagnostic", x=0.04, ha="left", fontsize=17, weight="bold")
    fig.text(
        0.04,
        0.925,
        "Crop windows are materialized, all categories collapse to person, and training/eval use 1280 input. Legacy 640 rows are archived and should not be mixed into paper-facing comparisons.",
        fontsize=9.5,
        color="#475569",
    )
    ax = fig.add_axes([0.04, 0.10, 0.92, 0.74])
    ax.axis("off")

    headers = ["Method", "Seed", "Latest", "Best", "P", "R", "AP50", "AP", "Status"]
    widths = [0.18, 0.07, 0.12, 0.12, 0.09, 0.09, 0.10, 0.10, 0.13]
    x0, y, row_h = 0.01, 0.90, 0.105
    ax.add_patch(Rectangle((x0, y), sum(widths), row_h, facecolor="#e8eef6", edgecolor="#d7e0ea"))
    x = x0
    for header, width in zip(headers, widths):
        ax.text(x + 0.008, y + row_h * 0.55, header, va="center", fontsize=9, weight="bold", color="#172033")
        x += width
    y -= row_h

    if not rows:
        ax.text(x0 + 0.02, y + row_h * 0.6, "No corrected TinyPerson runs found yet.", fontsize=11, color="#64748b")
    for row in rows:
        latest = row["latest"]
        best = row["best"]
        is_ours = row["method"] == "Ours"
        face = "#fff7ed" if is_ours else "#ffffff"
        ax.add_patch(Rectangle((x0, y), sum(widths), row_h, facecolor=face, edgecolor="#d7e0ea"))
        cells = [
            row["method"],
            str(row["seed"]),
            f"e{latest['epoch']}",
            f"e{best['epoch']}",
            f"{latest['precision']:.4f}",
            f"{latest['recall']:.4f}",
            f"{latest['AP50']:.4f}",
            f"{latest['AP']:.4f}",
            row["status"],
        ]
        x = x0
        for cell, width in zip(cells, widths):
            ax.text(
                x + 0.008,
                y + row_h * 0.55,
                cell,
                va="center",
                fontsize=9,
                weight="bold" if is_ours else "normal",
                color="#172033",
            )
            x += width
        y -= row_h

    out_md = out.with_suffix(".md")
    lines = ["# TinyPerson Corrected Original-Window 1280 Diagnostic", ""]
    for row in rows:
        latest = row["latest"]
        best = row["best"]
        lines.append(
            f"- {row['method']} seed {row['seed']}: latest e{latest['epoch']} "
            f"AP={latest['AP']:.4f}, AP50={latest['AP50']:.4f}, P={latest['precision']:.4f}, R={latest['recall']:.4f}; "
            f"best e{best['epoch']} AP={best['AP']:.4f}, AP50={best['AP50']:.4f}"
        )
    out_md.write_text("\n".join(lines) + "\n", encoding="utf-8")
    fig.savefig(out, bbox_inches="tight")
    plt.close(fig)


def write_summary_csv(rows: list[dict[str, Any]], out: Path) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "method",
        "seed",
        "imgsz",
        "latest_epoch",
        "best_epoch",
        "best_ap",
        "best_ap50",
        "best_precision",
        "best_recall",
        "latest_ap",
        "latest_ap50",
        "status",
        "run_dir",
    ]
    with out.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            latest = row["latest"]
            best = row["best"]
            writer.writerow(
                {
                    "method": row["method"],
                    "seed": row["seed"],
                    "imgsz": row["imgsz"],
                    "latest_epoch": latest["epoch"],
                    "best_epoch": best["epoch"],
                    "best_ap": f"{best['AP']:.6f}",
                    "best_ap50": f"{best['AP50']:.6f}",
                    "best_precision": f"{best['precision']:.6f}",
                    "best_recall": f"{best['recall']:.6f}",
                    "latest_ap": f"{latest['AP']:.6f}",
                    "latest_ap50": f"{latest['AP50']:.6f}",
                    "status": row["status"],
                    "run_dir": row["run_dir"],
                }
            )


def write_latex_rows(rows: list[dict[str, Any]], out: Path) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "% Auto-generated by scripts/build_tinyperson_corner_original_dashboard.py",
        "% Corrected TinyPerson corner/original-window protocol; do not mix with legacy 640 diagnostic rows.",
        r"\begin{tabular}{lrrrrrrl}",
        r"\toprule",
        r"Method & Seed & Img & Best Ep. & AP & AP50 & R & Status \\",
        r"\midrule",
    ]
    for row in rows:
        best = row["best"]
        lines.append(
            f"{row['method']} & {row['seed']} & {row['imgsz']} & {best['epoch']} & "
            f"{best['AP']:.4f} & {best['AP50']:.4f} & {best['recall']:.4f} & {row['status']} \\\\"
        )
    if not rows:
        lines.append(r"\multicolumn{8}{c}{Corrected TinyPerson run pending.} \\")
    lines += [r"\bottomrule", r"\end{tabular}", ""]
    out.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default="outputs/detectors/tinyperson_corner_original")
    parser.add_argument("--out", default="outputs/reports/live/tinyperson_corner_original_dashboard.png")
    parser.add_argument("--summary-csv", default="outputs/experiments/tinyperson_corner_original/live_summary.csv")
    parser.add_argument("--tex", default="paper/tables/tinyperson_corner_original_live_table.tex")
    args = parser.parse_args()
    rows = collect(Path(args.root))
    draw(rows, Path(args.out))
    write_summary_csv(rows, Path(args.summary_csv))
    write_latex_rows(rows, Path(args.tex))
    print(json.dumps({"rows": len(rows), "out": args.out, "summary_csv": args.summary_csv, "tex": args.tex}, indent=2))


if __name__ == "__main__":
    main()
