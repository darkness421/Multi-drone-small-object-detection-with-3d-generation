"""Feature activation visualization entrypoint for YOLO-style detectors.

The paper needs a qualitative heatmap for the final detector comparison, but
YOLO detection heads do not expose a single classifier logit that is comparable
across every variant. This script therefore produces a conservative
Grad-CAM-style feature activation map: it hooks the last non-detection module,
averages the absolute activation response, overlays it on the input image, and
stores the exact target layer in a manifest. The artifact should be described as
"feature activation heatmap" rather than a class-logit Grad-CAM claim.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image, ImageDraw, ImageFont

from runtime.config import resolve_path


def dependency_status() -> dict[str, bool]:
    status: dict[str, bool] = {}
    for name in ("torch", "cv2", "ultralytics"):
        try:
            __import__(name)
            status[name] = True
        except ImportError:
            status[name] = False
    try:
        __import__("pytorch_grad_cam")
        status["pytorch_grad_cam"] = True
    except ImportError:
        status["pytorch_grad_cam"] = False
    return status


def write_plan(weights: list[str], images: list[str], labels: list[str], out_dir: str | Path, target_layer: str) -> Path:
    out_root = resolve_path(out_dir)
    out_root.mkdir(parents=True, exist_ok=True)
    payload = {
        "status": "prepared",
        "weights": weights,
        "labels": labels,
        "images": images,
        "target_layer": target_layer,
        "dependency_status": dependency_status(),
        "notes": [
            "These are feature activation heatmaps, not class-logit Grad-CAM scores.",
            "The target is the last non-detection module unless --target-layer specifies a module index.",
            "Use identical images across models: correct, false positive, false negative, and class confusion cases.",
            "RT-DETR attention/feature visualization is a separate TODO because decoder attention differs from YOLO heads.",
        ],
    }
    path = out_root / "gradcam_run_plan.json"
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return path


def _font(size: int, bold: bool = False) -> ImageFont.ImageFont:
    names = ["DejaVuSans-Bold.ttf", "DejaVuSans.ttf"] if bold else ["DejaVuSans.ttf"]
    for name in names:
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default()


def _target_module(model: Any, target_layer: str) -> tuple[int, Any]:
    module_seq = getattr(model, "model", model)
    if hasattr(module_seq, "model"):
        module_seq = getattr(module_seq, "model")
    modules = list(module_seq)
    if target_layer.isdigit() or (target_layer.startswith("-") and target_layer[1:].isdigit()):
        idx = int(target_layer)
        return idx, modules[idx]
    for idx in range(len(modules) - 1, -1, -1):
        module = modules[idx]
        if module.__class__.__name__.lower() == "detect":
            continue
        return idx, module
    return len(modules) - 1, modules[-1]


def _activation_tensor(output: Any) -> Any | None:
    import torch

    if torch.is_tensor(output):
        return output
    if isinstance(output, (list, tuple)):
        tensors = [item for item in output if torch.is_tensor(item) and item.ndim == 4]
        if tensors:
            return max(tensors, key=lambda t: int(t.shape[-1]) * int(t.shape[-2]))
    return None


def _normalize_cam(array: np.ndarray) -> np.ndarray:
    array = array.astype(np.float32)
    array -= float(np.nanmin(array))
    denom = float(np.nanmax(array)) or 1.0
    return np.clip(array / denom, 0.0, 1.0)


def _overlay_heatmap(image_path: Path, cam: np.ndarray, out_path: Path, title: str) -> None:
    import cv2

    image = Image.open(image_path).convert("RGB")
    rgb = np.asarray(image)
    cam_resized = cv2.resize(cam, (rgb.shape[1], rgb.shape[0]), interpolation=cv2.INTER_CUBIC)
    heat = cv2.applyColorMap((cam_resized * 255).astype(np.uint8), cv2.COLORMAP_JET)
    heat = cv2.cvtColor(heat, cv2.COLOR_BGR2RGB)
    overlay = np.clip(0.55 * rgb + 0.45 * heat, 0, 255).astype(np.uint8)
    canvas = Image.fromarray(overlay)
    draw = ImageDraw.Draw(canvas)
    font = _font(22, True)
    text_w = draw.textlength(title, font=font)
    draw.rectangle([0, 0, int(text_w) + 28, 38], fill=(15, 23, 42))
    draw.text((12, 7), title, fill="white", font=font)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(out_path)


def _contact_sheet(paths: list[Path], labels: list[str], out_path: Path, title: str, cols: int) -> None:
    thumbs = []
    for path in paths:
        image = Image.open(path).convert("RGB")
        image.thumbnail((420, 300), Image.Resampling.LANCZOS)
        tile = Image.new("RGB", (440, 340), "#f8fafc")
        tile.paste(image, ((440 - image.width) // 2, 12))
        thumbs.append(tile)
    rows = (len(thumbs) + cols - 1) // cols
    header_h = 72 if title else 0
    y_offset = header_h + 20
    canvas = Image.new("RGB", (cols * 460 + 40, rows * 380 + y_offset + 8), "#eef2f7")
    draw = ImageDraw.Draw(canvas)
    if title:
        draw.rectangle([0, 0, canvas.width, header_h], fill="#0f172a")
        draw.text((24, 20), title, fill="white", font=_font(28, True))
    for idx, tile in enumerate(thumbs):
        x = 20 + (idx % cols) * 460
        y = y_offset + (idx // cols) * 380
        canvas.paste(tile, (x, y))
        draw.text((x + 10, y + 318), labels[idx], fill="#334155", font=_font(16))
    out_path.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(out_path)


def render_heatmaps(
    weights: list[str],
    images: list[str],
    labels: list[str],
    out_dir: str | Path,
    target_layer: str,
    imgsz: int,
    device: str,
    conf: float,
) -> Path:
    from ultralytics import YOLO

    out_root = resolve_path(out_dir)
    out_root.mkdir(parents=True, exist_ok=True)
    labels = labels or [Path(weight).stem for weight in weights]
    if len(labels) != len(weights):
        raise ValueError("--labels must match --weights length")

    manifest: dict[str, Any] = {
        "status": "rendered",
        "kind": "feature_activation_heatmap",
        "weights": weights,
        "labels": labels,
        "images": images,
        "target_layer": target_layer,
        "imgsz": imgsz,
        "device": device,
        "conf": conf,
        "dependency_status": dependency_status(),
        "artifacts": [],
        "notes": [
            "Activation is mean(abs(feature)) from the selected target module.",
            "This is a qualitative feature-response visualization for supplementary analysis.",
        ],
    }

    all_paths: list[Path] = []
    all_labels: list[str] = []
    per_image: dict[str, list[Path]] = {}

    for weight, label in zip(weights, labels):
        yolo = YOLO(resolve_path(weight))
        model = yolo.model
        model.eval()
        module_idx, module = _target_module(model, target_layer)
        activation: list[Any] = []

        def hook(_module: Any, _inputs: Any, output: Any) -> None:
            tensor = _activation_tensor(output)
            if tensor is not None:
                activation.append(tensor.detach())

        handle = module.register_forward_hook(hook)
        try:
            for image in images:
                image_path = resolve_path(image)
                activation.clear()
                yolo.predict(str(image_path), imgsz=imgsz, device=device, conf=conf, verbose=False)
                if not activation:
                    continue
                tensor = activation[-1].float().abs().mean(dim=1)[0].cpu().numpy()
                cam = _normalize_cam(tensor)
                stem = image_path.stem
                safe_label = "".join(ch if ch.isalnum() or ch in "-_" else "_" for ch in label)
                out_path = out_root / "heatmaps" / stem / f"{safe_label}_activation_heatmap.png"
                _overlay_heatmap(image_path, cam, out_path, f"{label} | layer {module_idx}:{module.__class__.__name__}")
                all_paths.append(out_path)
                all_labels.append(f"{label} / {stem}")
                per_image.setdefault(stem, []).append(out_path)
                manifest["artifacts"].append(
                    {
                        "label": label,
                        "weight": weight,
                        "image": image,
                        "target_module_index": module_idx,
                        "target_module_type": module.__class__.__name__,
                        "heatmap": str(out_path),
                    }
                )
        finally:
            handle.remove()

    for stem, paths in per_image.items():
        image_labels = [path.stem.replace("_activation_heatmap", "") for path in paths]
        _contact_sheet(paths, image_labels, out_root / "contact_sheets" / f"{stem}_comparison.png", stem, cols=len(weights))
    if all_paths:
        _contact_sheet(all_paths, all_labels, out_root / "feature_activation_contact_sheet.png", "", cols=len(weights))

    manifest_path = out_root / "gradcam_render_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Prepare YOLO Grad-CAM analysis inputs.")
    parser.add_argument("--weights", nargs="+", required=True)
    parser.add_argument("--images", nargs="+", required=True)
    parser.add_argument("--labels", nargs="*", default=None)
    parser.add_argument("--out-dir", default="outputs/qualitative/gradcam")
    parser.add_argument("--target-layer", default="auto-neck-last")
    parser.add_argument("--imgsz", type=int, default=1280)
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--conf", type=float, default=0.25)
    parser.add_argument("--plan-only", action="store_true")
    args = parser.parse_args()
    labels = args.labels or [Path(weight).stem for weight in args.weights]
    plan = write_plan(args.weights, args.images, labels, args.out_dir, args.target_layer)
    if args.plan_only:
        print(plan)
        return
    print(render_heatmaps(args.weights, args.images, labels, args.out_dir, args.target_layer, args.imgsz, args.device, args.conf))


if __name__ == "__main__":
    main()
