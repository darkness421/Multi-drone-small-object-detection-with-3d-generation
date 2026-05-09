"""Windows-friendly Ultralytics train/eval wrappers."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from runtime import prepare_run_dir, setup_logging
from runtime.config import resolve_path


def require_ultralytics() -> Any:
    try:
        from ultralytics import YOLO
    except ImportError as exc:
        raise RuntimeError(
            "Ultralytics is not installed. Install with `pip install ultralytics opencv-python`, "
            "or create the conda env from environment.yml."
        ) from exc
    return YOLO


def train_yolo(
    *,
    model: str,
    data_yaml: str | Path,
    epochs: int = 100,
    imgsz: int = 1280,
    batch: int = 8,
    project: str | Path = "outputs/detectors",
    name: str | None = None,
) -> dict[str, Any]:
    YOLO = require_ultralytics()
    data_yaml = resolve_path(data_yaml)
    if not data_yaml.exists():
        raise FileNotFoundError(f"Ultralytics data YAML not found: {data_yaml}")
    run_name = name or f"train_{Path(model).stem}"
    run_dir = prepare_run_dir(run_name, output_root=project)
    logger = setup_logging(run_dir / "logs" / "train.log")
    logger.info("Training %s on %s", model, data_yaml)
    yolo = YOLO(model)
    result = yolo.train(data=str(data_yaml), epochs=epochs, imgsz=imgsz, batch=batch, project=str(run_dir), name="ultralytics")
    summary = {"model": model, "data": str(data_yaml), "epochs": epochs, "imgsz": imgsz, "batch": batch, "run_dir": str(run_dir)}
    (run_dir / "metrics" / "train_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return summary


def eval_yolo(
    *,
    model: str,
    data_yaml: str | Path,
    imgsz: int = 1280,
    project: str | Path = "outputs/detectors",
    name: str | None = None,
) -> dict[str, Any]:
    YOLO = require_ultralytics()
    data_yaml = resolve_path(data_yaml)
    if not data_yaml.exists():
        raise FileNotFoundError(f"Ultralytics data YAML not found: {data_yaml}")
    run_name = name or f"eval_{Path(model).stem}"
    run_dir = prepare_run_dir(run_name, output_root=project)
    logger = setup_logging(run_dir / "logs" / "eval.log")
    logger.info("Evaluating %s on %s", model, data_yaml)
    yolo = YOLO(model)
    metrics = yolo.val(data=str(data_yaml), imgsz=imgsz, project=str(run_dir), name="ultralytics")
    summary = {
        "model": model,
        "data": str(data_yaml),
        "imgsz": imgsz,
        "run_dir": str(run_dir),
        "metrics_repr": str(metrics),
    }
    (run_dir / "metrics" / "eval_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Train/evaluate Ultralytics detector baselines.")
    parser.add_argument("mode", choices=["train", "eval"])
    parser.add_argument("--model", default="yolo11n.pt")
    parser.add_argument("--data-yaml", required=True)
    parser.add_argument("--epochs", type=int, default=100)
    parser.add_argument("--imgsz", type=int, default=1280)
    parser.add_argument("--batch", type=int, default=8)
    parser.add_argument("--project", default="outputs/detectors")
    parser.add_argument("--name", default=None)
    args = parser.parse_args()

    payload = vars(args).copy()
    payload.pop("mode")
    if args.mode == "train":
        print(json.dumps(train_yolo(**payload), indent=2))
    else:
        payload.pop("epochs")
        payload.pop("batch")
        print(json.dumps(eval_yolo(**payload), indent=2))



if __name__ == "__main__":
    main()
