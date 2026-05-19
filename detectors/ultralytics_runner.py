"""Windows-friendly Ultralytics train/eval wrappers."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from runtime import prepare_run_dir, setup_logging
from runtime.config import resolve_path

try:
    from .roc_auc import compute_image_level_roc_auc
except ImportError:
    from roc_auc import compute_image_level_roc_auc


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
    device: str | None = None,
    seed: int | None = None,
    deterministic: bool = True,
    from_scratch: bool = False,
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
    train_model = scratch_model_name(model) if from_scratch else model
    logger.info("Training %s on %s", train_model, data_yaml)
    yolo = YOLO(train_model)
    train_kwargs: dict[str, Any] = {
        "data": str(data_yaml),
        "epochs": epochs,
        "imgsz": imgsz,
        "batch": batch,
        "project": str(run_dir),
        "name": "ultralytics",
        "pretrained": not from_scratch,
        "deterministic": deterministic,
    }
    if device:
        train_kwargs["device"] = device
    if seed is not None:
        train_kwargs["seed"] = seed
    result = yolo.train(**train_kwargs)
    summary = {
        "model": train_model,
        "requested_model": model,
        "dataset": infer_dataset_name(data_yaml),
        "from_scratch": from_scratch,
        "data": str(data_yaml),
        "epochs": epochs,
        "imgsz": imgsz,
        "batch": batch,
        "device": device or "auto",
        "seed": seed,
        "deterministic": deterministic,
        "run_dir": str(run_dir),
    }
    (run_dir / "metrics" / "train_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return summary


def eval_yolo(
    *,
    model: str,
    data_yaml: str | Path,
    imgsz: int = 1280,
    device: str | None = None,
    roc_auc: bool = False,
    roc_auc_split: str = "val",
    roc_auc_max_images: int | None = None,
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
    val_kwargs: dict[str, Any] = {"data": str(data_yaml), "imgsz": imgsz, "project": str(run_dir), "name": "ultralytics"}
    if device:
        val_kwargs["device"] = device
    metrics = yolo.val(**val_kwargs)
    metric_values = extract_ultralytics_val_metrics(metrics)
    roc_auc_payload: dict[str, Any] = {}
    if roc_auc:
        roc_auc_payload = compute_image_level_roc_auc(
            yolo,
            data_yaml=data_yaml,
            split=roc_auc_split,
            imgsz=imgsz,
            device=device,
            max_images=roc_auc_max_images,
        )
        if roc_auc_payload.get("macro") is not None:
            metric_values["ROC-AUC"] = float(roc_auc_payload["macro"])
    summary = {
        "model": model,
        "dataset": infer_dataset_name(data_yaml),
        "data": str(data_yaml),
        "imgsz": imgsz,
        "device": device or "auto",
        "run_dir": str(run_dir),
        "metrics": metric_values,
        "metrics_repr": str(metrics),
        "roc_auc": roc_auc_payload,
    }
    (run_dir / "metrics" / "eval_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    mirror_eval_summary_to_training_run(model, summary)
    return summary


def scratch_model_name(model: str) -> str:
    """Map an Ultralytics weight name to the matching model YAML for scratch training."""

    path = Path(model)
    if path.suffix.lower() == ".pt":
        return str(path.with_suffix(".yaml"))
    return model


def infer_dataset_name(data_yaml: str | Path) -> str:
    """Infer a readable dataset label from the detector data YAML path."""

    value = str(data_yaml).lower()
    if "uavdt" in value:
        return "UAVDT"
    if "visdrone" in value:
        return "VisDrone2019-DET"
    if "marine" in value or "com3d" in value:
        return "CoM3D-MarineCity"
    return Path(data_yaml).stem


def mirror_eval_summary_to_training_run(model: str, summary: dict[str, Any]) -> None:
    """Attach eval metrics next to the training summary when evaluating best.pt."""

    model_path = Path(model)
    if model_path.name != "best.pt" or model_path.parent.name != "weights":
        return
    ultralytics_dir = model_path.parent.parent
    if ultralytics_dir.name != "ultralytics":
        return
    train_run_dir = ultralytics_dir.parent
    metrics_dir = train_run_dir / "metrics"
    if metrics_dir.exists():
        (metrics_dir / "eval_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")


def extract_ultralytics_val_metrics(metrics: Any) -> dict[str, float]:
    """Extract common scalar detector metrics from Ultralytics validation objects."""

    box = getattr(metrics, "box", None)
    if box is None:
        return {}
    mapping = {
        "precision": "mp",
        "recall": "mr",
        "AP50": "map50",
        "AP75": "map75",
        "AP": "map",
    }
    payload: dict[str, float] = {}
    for out_key, attr in mapping.items():
        value = getattr(box, attr, None)
        if value is None:
            continue
        try:
            payload[out_key] = float(value)
        except (TypeError, ValueError):
            continue
    return payload


def main() -> None:
    parser = argparse.ArgumentParser(description="Train/evaluate Ultralytics detector baselines.")
    parser.add_argument("mode", choices=["train", "eval"])
    parser.add_argument("--model", default="yolo11n.pt")
    parser.add_argument("--data-yaml", required=True)
    parser.add_argument("--epochs", type=int, default=100)
    parser.add_argument("--imgsz", type=int, default=1280)
    parser.add_argument("--batch", type=int, default=8)
    parser.add_argument("--device", default=None, help="Ultralytics device string, for example '0' or '0,1'.")
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--non-deterministic", action="store_true")
    parser.add_argument("--from-scratch", action="store_true", help="Use model YAML and disable pretrained weights.")
    parser.add_argument("--roc-auc", action="store_true", help="During eval, also compute image-level ROC-AUC.")
    parser.add_argument("--roc-auc-split", default="val")
    parser.add_argument("--roc-auc-max-images", type=int, default=None)
    parser.add_argument("--project", default="outputs/detectors")
    parser.add_argument("--name", default=None)
    args = parser.parse_args()

    payload = vars(args).copy()
    payload.pop("mode")
    payload["deterministic"] = not payload.pop("non_deterministic")
    if args.mode == "train":
        payload.pop("roc_auc")
        payload.pop("roc_auc_split")
        payload.pop("roc_auc_max_images")
        print(json.dumps(train_yolo(**payload), indent=2))
    else:
        payload.pop("epochs")
        payload.pop("batch")
        payload.pop("seed")
        payload.pop("deterministic")
        payload.pop("from_scratch")
        print(json.dumps(eval_yolo(**payload), indent=2))



if __name__ == "__main__":
    main()
