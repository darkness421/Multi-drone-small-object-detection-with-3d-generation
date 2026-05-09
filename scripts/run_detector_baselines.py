"""Safe Windows runner for detector baseline plans.

This script does not crash when datasets or Ultralytics are missing. It writes a
baseline plan and marks each run as ready/skipped, so Phase 1 remains
reproducible before raw datasets are copied into data/raw/.
"""

from __future__ import annotations

import argparse
import csv
import importlib.util
from pathlib import Path

from runtime.config import load_config, resolve_path


BASELINE_MODELS = [
    ("YOLOv8n", "yolov8n.pt"),
    ("YOLOv11n", "yolo11n.pt"),
    ("YOLOv8n+P2", "yolov8n.pt"),
    ("RT-DETR-R18", "rtdetr-l.pt"),
]


def ultralytics_available() -> bool:
    return importlib.util.find_spec("ultralytics") is not None


def dataset_ready(data_yaml: Path) -> bool:
    if not data_yaml.exists():
        return False
    config = load_config(data_yaml)
    root = resolve_path(config.get("path", "."))
    train = root / config.get("train", "")
    val = root / config.get("val", "")
    return train.exists() and val.exists()


def write_plan(out_path: str | Path, data_yaml: str | Path) -> list[dict[str, str]]:
    out_path = resolve_path(out_path)
    data_yaml = resolve_path(data_yaml)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    has_ultralytics = ultralytics_available()
    has_dataset = dataset_ready(data_yaml)
    rows = []
    for method, weights in BASELINE_MODELS:
        status = "ready" if has_ultralytics and has_dataset else "skipped"
        reason = "" if status == "ready" else f"ultralytics={has_ultralytics}, dataset={has_dataset}"
        rows.append({"method": method, "weights": weights, "data_yaml": str(data_yaml), "status": status, "reason": reason})
    with out_path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["method", "weights", "data_yaml", "status", "reason"])
        writer.writeheader()
        writer.writerows(rows)
    return rows


def main() -> None:
    parser = argparse.ArgumentParser(description="Create a safe detector baseline run plan.")
    parser.add_argument("--data-yaml", default="configs/detector/visdrone_yolo_data.yaml")
    parser.add_argument("--out", default="outputs/detectors/detector_baseline_plan.csv")
    args = parser.parse_args()
    rows = write_plan(args.out, args.data_yaml)
    for row in rows:
        print(f"{row['method']}: {row['status']} {row['reason']}")
    print(f"Wrote {args.out}")


if __name__ == "__main__":
    main()

