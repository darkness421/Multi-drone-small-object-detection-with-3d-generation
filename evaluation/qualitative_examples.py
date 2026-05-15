"""Create detector qualitative example contact sheets."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from runtime.config import resolve_path


IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff", ".webp"}


def require_cv2() -> Any:
    try:
        import cv2
    except ImportError as exc:
        raise RuntimeError("opencv-python is required for qualitative examples.") from exc
    return cv2


def iter_images(path: str | Path, limit: int) -> list[Path]:
    root = resolve_path(path)
    images = sorted(child for child in root.rglob("*") if child.suffix.lower() in IMAGE_SUFFIXES)
    return images[:limit]


def draw_yolo_labels(image: Any, label_path: Path, names: list[str] | None = None) -> Any:
    cv2 = require_cv2()
    height, width = image.shape[:2]
    if not label_path.exists():
        return image
    for line in label_path.read_text(encoding="utf-8").splitlines():
        fields = line.split()
        if len(fields) < 5:
            continue
        cls, xc, yc, bw, bh = [float(value) for value in fields[:5]]
        x1 = int((xc - bw / 2.0) * width)
        y1 = int((yc - bh / 2.0) * height)
        x2 = int((xc + bw / 2.0) * width)
        y2 = int((yc + bh / 2.0) * height)
        label = names[int(cls)] if names and 0 <= int(cls) < len(names) else str(int(cls))
        cv2.rectangle(image, (x1, y1), (x2, y2), (80, 200, 120), 2)
        cv2.putText(image, f"GT {label}", (x1, max(14, y1 - 4)), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (80, 200, 120), 1)
    return image


def label_path_for_image(image_path: Path) -> Path:
    parts = list(image_path.parts)
    for idx, part in enumerate(parts):
        if part == "images":
            parts[idx] = "labels"
            return Path(*parts).with_suffix(".txt")
    return image_path.with_suffix(".txt")


def draw_predictions(image: Any, result: Any) -> Any:
    cv2 = require_cv2()
    names = getattr(result, "names", {}) or {}
    boxes = getattr(result, "boxes", None)
    if boxes is None:
        return image
    xyxy = boxes.xyxy.detach().cpu().numpy()
    cls = boxes.cls.detach().cpu().numpy().astype(int)
    conf = boxes.conf.detach().cpu().numpy()
    for box, class_id, score in zip(xyxy, cls, conf):
        x1, y1, x2, y2 = [int(value) for value in box]
        label = names.get(int(class_id), str(int(class_id))) if isinstance(names, dict) else str(int(class_id))
        cv2.rectangle(image, (x1, y1), (x2, y2), (70, 140, 230), 2)
        cv2.putText(image, f"{label} {score:.2f}", (x1, max(14, y1 - 4)), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (70, 140, 230), 1)
    return image


def make_sheet(images: list[Any], out_path: Path, tile_width: int = 640) -> None:
    cv2 = require_cv2()
    import numpy as np

    resized = []
    for image in images:
        height, width = image.shape[:2]
        scale = tile_width / max(1, width)
        resized.append(cv2.resize(image, (tile_width, max(1, int(height * scale)))))
    if not resized:
        return
    max_height = max(image.shape[0] for image in resized)
    padded = []
    for image in resized:
        pad = max_height - image.shape[0]
        padded.append(cv2.copyMakeBorder(image, 0, pad, 0, 0, cv2.BORDER_CONSTANT, value=(245, 245, 245)))
    sheet = np.vstack(padded)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(out_path), sheet)


def build_examples(weights: list[str], images_dir: str | Path, out_dir: str | Path, max_images: int, imgsz: int, device: str | None) -> None:
    cv2 = require_cv2()
    try:
        from ultralytics import YOLO
    except ImportError as exc:
        raise RuntimeError("ultralytics is required for prediction overlays.") from exc

    images = iter_images(images_dir, max_images)
    out_root = resolve_path(out_dir)
    for weight in weights:
        model = YOLO(weight)
        rendered = []
        for image_path in images:
            base = cv2.imread(str(image_path))
            if base is None:
                continue
            gt = draw_yolo_labels(base.copy(), label_path_for_image(image_path))
            kwargs: dict[str, Any] = {"source": str(image_path), "imgsz": imgsz, "verbose": False, "save": False}
            if device:
                kwargs["device"] = device
            pred = draw_predictions(gt, model.predict(**kwargs)[0])
            rendered.append(pred)
            out_image = out_root / Path(weight).stem / f"{image_path.stem}_overlay.jpg"
            out_image.parent.mkdir(parents=True, exist_ok=True)
            cv2.imwrite(str(out_image), pred)
        make_sheet(rendered, out_root / f"{Path(weight).stem}_contact_sheet.jpg")


def main() -> None:
    parser = argparse.ArgumentParser(description="Make GT/prediction qualitative detector examples.")
    parser.add_argument("--weights", nargs="+", required=True)
    parser.add_argument("--images-dir", required=True)
    parser.add_argument("--out-dir", default="outputs/qualitative/detection_examples")
    parser.add_argument("--max-images", type=int, default=12)
    parser.add_argument("--imgsz", type=int, default=1280)
    parser.add_argument("--device", default=None)
    args = parser.parse_args()
    build_examples(args.weights, args.images_dir, args.out_dir, args.max_images, args.imgsz, args.device)


if __name__ == "__main__":
    main()
