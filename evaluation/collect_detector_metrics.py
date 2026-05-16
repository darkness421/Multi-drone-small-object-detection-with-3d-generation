"""Collect Ultralytics detector run metrics into one server baseline CSV."""

from __future__ import annotations

import argparse
import csv
import json
import re
from pathlib import Path
from typing import Any

from runtime.config import resolve_path


METRIC_COLUMNS = [
    "method",
    "model",
    "dataset",
    "seed",
    "status",
    "run_dir",
    "results_csv",
    "best_weight",
    "best_epoch",
    "best_AP",
    "best_AP50",
    "best_AP75",
    "best_APsmall",
    "best_precision",
    "best_recall",
    "best_F1",
    "final_epoch",
    "final_AP",
    "final_AP50",
    "final_AP75",
    "final_APsmall",
    "final_precision",
    "final_recall",
    "final_F1",
    "ROC-AUC",
    "latency_ms",
    "FPS",
    "Params",
    "GFLOPs",
]


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def as_float(value: Any) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def first_metric(row: dict[str, str], names: list[str]) -> float | None:
    stripped = {key.strip(): value for key, value in row.items()}
    for name in names:
        value = as_float(stripped.get(name))
        if value is not None:
            return value
    return None


def f1(precision: float | None, recall: float | None) -> float | None:
    if precision is None or recall is None or precision + recall == 0:
        return None
    return 2.0 * precision * recall / (precision + recall)


def metric_payload(row: dict[str, str], prefix: str) -> dict[str, float | None]:
    precision = first_metric(row, ["metrics/precision(B)", "metrics/precision"])
    recall = first_metric(row, ["metrics/recall(B)", "metrics/recall"])
    return {
        f"{prefix}_epoch": first_metric(row, ["epoch"]),
        f"{prefix}_AP": first_metric(row, ["metrics/mAP50-95(B)", "metrics/mAP50-95"]),
        f"{prefix}_AP50": first_metric(row, ["metrics/mAP50(B)", "metrics/mAP50"]),
        f"{prefix}_AP75": first_metric(row, ["metrics/mAP75(B)", "metrics/mAP75"]),
        f"{prefix}_APsmall": first_metric(row, ["metrics/mAP50-95(S)", "metrics/APsmall", "metrics/APs"]),
        f"{prefix}_precision": precision,
        f"{prefix}_recall": recall,
        f"{prefix}_F1": f1(precision, recall),
    }


def best_row(rows: list[dict[str, str]]) -> dict[str, str]:
    return max(rows, key=lambda row: first_metric(row, ["metrics/mAP50-95(B)", "metrics/mAP50-95"]) or -1.0)


def infer_seed(run_dir: Path, summary: dict[str, Any]) -> str:
    if summary.get("seed") is not None:
        return str(summary["seed"])
    match = re.search(r"seed(\d+)", run_dir.name)
    return match.group(1) if match else ""


def infer_method(model: str) -> str:
    stem = Path(model).stem
    aliases = {
        "yolov8n": "YOLOv8n",
        "yolov8s": "YOLOv8s",
        "yolo11n": "YOLOv11n",
        "yolo11s": "YOLOv11s",
        "yolo12n": "YOLOv12n",
        "yolo12s": "YOLOv12s",
        "rtdetr-l": "RT-DETR-L",
        "rtdetr-r18": "RT-DETR-R18",
    }
    return aliases.get(stem, stem)


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def collect_one(results_csv: Path) -> dict[str, Any]:
    run_dir = results_csv.parent.parent if results_csv.parent.name == "ultralytics" else results_csv.parent
    rows = read_csv_rows(results_csv)
    final = rows[-1] if rows else {}
    best = best_row(rows) if rows else {}
    train_summary = read_json(run_dir / "metrics" / "train_summary.json")
    eval_summary = read_json(run_dir / "metrics" / "eval_summary.json")
    model = str(train_summary.get("requested_model") or train_summary.get("model") or run_dir.name.split("_visdrone")[0])
    best_weight = results_csv.parent / "weights" / "best.pt"
    train_summary_path = run_dir / "metrics" / "train_summary.json"
    payload: dict[str, Any] = {
        "method": train_summary.get("method") or infer_method(model),
        "model": model,
        "dataset": "VisDrone2019-DET",
        "seed": infer_seed(run_dir, train_summary),
        "status": "completed" if train_summary_path.exists() and best_weight.exists() else "incomplete",
        "run_dir": str(run_dir),
        "results_csv": str(results_csv),
        "best_weight": str(best_weight) if best_weight.exists() else "",
        "ROC-AUC": (eval_summary.get("metrics") or {}).get("ROC-AUC", (eval_summary.get("roc_auc") or {}).get("macro")),
    }
    payload.update(metric_payload(best, "best"))
    payload.update(metric_payload(final, "final"))
    return payload


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(METRIC_COLUMNS)
    for row in rows:
        for key in row:
            if key not in fieldnames:
                fieldnames.append(key)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def collect(detector_root: str | Path) -> list[dict[str, Any]]:
    root = resolve_path(detector_root)
    return [collect_one(path) for path in sorted(root.rglob("results.csv"))]


def main() -> None:
    parser = argparse.ArgumentParser(description="Collect server detector baseline metrics.")
    parser.add_argument("--detector-root", default="outputs/detectors/server_baselines")
    parser.add_argument("--out", default="outputs/experiments/server_baseline_results.csv")
    args = parser.parse_args()

    rows = collect(args.detector_root)
    out_path = resolve_path(args.out)
    write_csv(out_path, rows)
    print(f"Wrote {out_path} ({len(rows)} rows)")


if __name__ == "__main__":
    main()
