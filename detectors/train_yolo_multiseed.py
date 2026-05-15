"""Run YOLO detector training across multiple seeds and aggregate metrics."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from statistics import mean, stdev
from typing import Any

from detectors.ultralytics_runner import eval_yolo, train_yolo
from runtime.config import resolve_path
from scripts.track_training_experiment import parse_ultralytics_metrics


DEFAULT_SEEDS = [42, 123, 2026]


def parse_seeds(value: str) -> list[int]:
    seeds = [int(part.strip()) for part in value.split(",") if part.strip()]
    if not seeds:
        raise argparse.ArgumentTypeError("At least one seed is required.")
    return seeds


def latest_results_csv(run_dir: str | Path) -> Path | None:
    candidates = sorted(Path(run_dir).rglob("results.csv"), key=lambda path: path.stat().st_mtime, reverse=True)
    return candidates[0] if candidates else None


def best_weight(run_dir: str | Path) -> Path | None:
    candidates = sorted(Path(run_dir).rglob("weights/best.pt"), key=lambda path: path.stat().st_mtime, reverse=True)
    return candidates[0] if candidates else None


def metric_value(row: dict[str, Any], key: str) -> float | None:
    value = row.get(key)
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def summarize_rows(rows: list[dict[str, Any]], metric_keys: list[str]) -> dict[str, dict[str, float]]:
    summary: dict[str, dict[str, float]] = {}
    for key in metric_keys:
        values = [value for row in rows if (value := metric_value(row, key)) is not None]
        if not values:
            continue
        summary[key] = {
            "mean": float(mean(values)),
            "std": float(stdev(values)) if len(values) > 1 else 0.0,
            "n": float(len(values)),
        }
    return summary


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames: list[str] = []
    for row in rows:
        for key in row:
            if key not in fieldnames:
                fieldnames.append(key)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def run_seed(args: argparse.Namespace, seed: int) -> dict[str, Any]:
    run_name = f"{Path(args.model).stem}_{args.dataset_slug}_scratch_seed{seed}" if args.from_scratch else f"{Path(args.model).stem}_{args.dataset_slug}_seed{seed}"
    train_summary = train_yolo(
        model=args.model,
        data_yaml=args.data_yaml,
        epochs=args.epochs,
        imgsz=args.imgsz,
        batch=args.batch,
        device=args.device,
        seed=seed,
        deterministic=not args.non_deterministic,
        from_scratch=args.from_scratch,
        project=args.project,
        name=run_name,
    )

    row: dict[str, Any] = {
        "method": args.method,
        "dataset": args.dataset,
        "seed": seed,
        "from_scratch": args.from_scratch,
        "model": train_summary["model"],
        "requested_model": train_summary["requested_model"],
        "run_dir": train_summary["run_dir"],
    }
    results_csv = latest_results_csv(train_summary["run_dir"])
    if results_csv:
        row["results_csv"] = str(results_csv)
        row.update(parse_ultralytics_metrics(results_csv))

    weight = best_weight(train_summary["run_dir"])
    if weight:
        row["best_weight"] = str(weight)
        eval_summary = eval_yolo(
            model=str(weight),
            data_yaml=args.data_yaml,
            imgsz=args.imgsz,
            device=args.device,
            roc_auc=args.roc_auc,
            roc_auc_split=args.roc_auc_split,
            roc_auc_max_images=args.roc_auc_max_images,
            project=args.project,
            name=f"eval_{run_name}",
        )
        row["eval_run_dir"] = eval_summary["run_dir"]
        eval_metrics = eval_summary.get("metrics", {}) or {}
        for key in ("AP", "AP50", "AP75", "precision", "recall"):
            if key in eval_metrics:
                row[key] = eval_metrics[key]
        roc_auc = eval_summary.get("roc_auc", {}) or {}
        if roc_auc:
            row["ROC-AUC"] = roc_auc.get("macro")
            row["roc_auc_valid_class_count"] = roc_auc.get("valid_class_count")
    return row


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Train YOLO detector across seeds for p-value-ready statistics.")
    parser.add_argument("--model", default="yolo11n.pt")
    parser.add_argument("--method", default="YOLOv11n")
    parser.add_argument("--dataset", default="VisDrone2019-DET")
    parser.add_argument("--dataset-slug", default="visdrone")
    parser.add_argument("--data-yaml", default="configs/detector/visdrone_yolo_data.yaml")
    parser.add_argument("--epochs", type=int, default=100)
    parser.add_argument("--imgsz", type=int, default=1280)
    parser.add_argument("--batch", type=int, default=8)
    parser.add_argument("--device", default=None)
    parser.add_argument("--seeds", type=parse_seeds, default=DEFAULT_SEEDS)
    parser.add_argument("--pretrained", action="store_true", help="Use pretrained .pt weights instead of scratch model YAML.")
    parser.add_argument("--non-deterministic", action="store_true")
    parser.add_argument("--roc-auc", action="store_true", default=True)
    parser.add_argument("--no-roc-auc", action="store_false", dest="roc_auc")
    parser.add_argument("--roc-auc-split", default="val")
    parser.add_argument("--roc-auc-max-images", type=int, default=None)
    parser.add_argument("--project", default="outputs/detectors")
    parser.add_argument("--out-dir", default="outputs/experiments/multiseed")
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    args.from_scratch = not args.pretrained
    args.data_yaml = str(resolve_path(args.data_yaml))

    rows = [run_seed(args, seed) for seed in args.seeds]
    out_dir = resolve_path(args.out_dir)
    run_slug = f"{Path(args.model).stem}_{args.dataset_slug}_{'scratch' if args.from_scratch else 'pretrained'}_{len(args.seeds)}seed"
    csv_path = out_dir / f"{run_slug}_seed_metrics.csv"
    json_path = out_dir / f"{run_slug}_summary.json"
    write_csv(csv_path, rows)
    summary = {
        "method": args.method,
        "dataset": args.dataset,
        "model": args.model,
        "from_scratch": args.from_scratch,
        "seeds": args.seeds,
        "seed_metrics_csv": str(csv_path),
        "metrics": summarize_rows(rows, ["AP", "AP50", "AP75", "precision", "recall", "ROC-AUC"]),
    }
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
