"""ROC-AUC helpers for detector validation outputs.

The metric here is image-level class-presence ROC-AUC: for each validation
image and each class, the target is whether the class appears in the YOLO label
file, and the score is the detector's maximum confidence for that class.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Iterable

import numpy as np

from runtime.config import resolve_path


IMAGE_SUFFIXES = {".bmp", ".jpg", ".jpeg", ".png", ".tif", ".tiff", ".webp"}


def load_yolo_data_yaml(data_yaml: str | Path) -> dict[str, Any]:
    try:
        import yaml
    except ImportError as exc:
        raise RuntimeError("PyYAML is required to read Ultralytics data YAML files.") from exc
    path = resolve_path(data_yaml)
    payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(payload, dict):
        raise ValueError(f"Data YAML must be a mapping: {path}")
    return payload


def class_names(payload: dict[str, Any]) -> list[str]:
    names = payload.get("names", [])
    if isinstance(names, dict):
        return [str(names[idx]) for idx in sorted(names, key=lambda value: int(value))]
    if isinstance(names, list):
        return [str(name) for name in names]
    raise ValueError("Ultralytics data YAML must define names as a list or mapping.")


def resolve_split_dir(data_yaml: str | Path, split: str) -> Path:
    data_yaml_path = resolve_path(data_yaml)
    payload = load_yolo_data_yaml(data_yaml_path)
    dataset_root = Path(payload.get("path", "."))
    if not dataset_root.is_absolute():
        dataset_root = resolve_path(dataset_root)
    split_value = payload.get(split)
    if split_value is None:
        raise KeyError(f"Split '{split}' is not defined in {data_yaml_path}")
    split_path = Path(split_value)
    if not split_path.is_absolute():
        split_path = dataset_root / split_path
    return split_path.resolve()


def iter_images(image_dir: Path) -> list[Path]:
    if not image_dir.exists():
        raise FileNotFoundError(f"Image split directory not found: {image_dir}")
    return sorted(path for path in image_dir.rglob("*") if path.suffix.lower() in IMAGE_SUFFIXES)


def label_path_for_image(image_path: Path) -> Path:
    parts = list(image_path.parts)
    for idx, part in enumerate(parts):
        if part == "images":
            parts[idx] = "labels"
            return Path(*parts).with_suffix(".txt")
    return image_path.parent.parent / "labels" / image_path.parent.name / f"{image_path.stem}.txt"


def read_present_classes(label_path: Path, num_classes: int) -> list[int]:
    present = [0] * num_classes
    if not label_path.exists():
        return present
    for line in label_path.read_text(encoding="utf-8").splitlines():
        fields = line.strip().split()
        if not fields:
            continue
        try:
            cls = int(float(fields[0]))
        except ValueError:
            continue
        if 0 <= cls < num_classes:
            present[cls] = 1
    return present


def max_confidence_by_class(result: Any, num_classes: int) -> list[float]:
    scores = [0.0] * num_classes
    boxes = getattr(result, "boxes", None)
    if boxes is None or getattr(boxes, "cls", None) is None or getattr(boxes, "conf", None) is None:
        return scores
    classes = boxes.cls.detach().cpu().numpy().astype(int)
    confidences = boxes.conf.detach().cpu().numpy().astype(float)
    for cls, conf in zip(classes, confidences):
        if 0 <= int(cls) < num_classes:
            scores[int(cls)] = max(scores[int(cls)], float(conf))
    return scores


def _macro_roc_auc(y_true: np.ndarray, y_score: np.ndarray, names: Iterable[str]) -> dict[str, Any]:
    try:
        from sklearn.metrics import roc_auc_score
    except ImportError as exc:
        raise RuntimeError("scikit-learn is required for ROC-AUC computation.") from exc
    per_class: dict[str, float | None] = {}
    valid_scores: list[float] = []
    for class_idx, name in enumerate(names):
        labels = y_true[:, class_idx]
        if len(set(labels.astype(int).tolist())) < 2:
            per_class[str(name)] = None
            continue
        auc = float(roc_auc_score(labels, y_score[:, class_idx]))
        per_class[str(name)] = auc
        valid_scores.append(auc)
    return {
        "macro": float(np.mean(valid_scores)) if valid_scores else None,
        "per_class": per_class,
        "valid_class_count": len(valid_scores),
    }


def compute_image_level_roc_auc(
    yolo: Any,
    *,
    data_yaml: str | Path,
    split: str = "val",
    imgsz: int = 1280,
    device: str | None = None,
    max_images: int | None = None,
    conf: float = 0.001,
) -> dict[str, Any]:
    """Run predictions and compute image-level class-presence ROC-AUC."""

    payload = load_yolo_data_yaml(data_yaml)
    names = class_names(payload)
    images = iter_images(resolve_split_dir(data_yaml, split))
    if max_images is not None:
        images = images[:max_images]
    if not images:
        raise ValueError(f"No images found for split '{split}' in {data_yaml}")

    y_true: list[list[int]] = []
    y_score: list[list[float]] = []
    for image_path in images:
        label_path = label_path_for_image(image_path)
        y_true.append(read_present_classes(label_path, len(names)))
        predict_kwargs: dict[str, Any] = {
            "source": str(image_path),
            "imgsz": imgsz,
            "conf": conf,
            "verbose": False,
            "save": False,
        }
        if device:
            predict_kwargs["device"] = device
        result = yolo.predict(**predict_kwargs)[0]
        y_score.append(max_confidence_by_class(result, len(names)))

    auc = _macro_roc_auc(np.asarray(y_true), np.asarray(y_score), names)
    auc.update(
        {
            "metric": "image_level_class_presence_roc_auc",
            "split": split,
            "num_images": len(images),
            "num_classes": len(names),
        }
    )
    return auc
