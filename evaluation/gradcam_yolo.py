"""Grad-CAM/feature visualization entrypoint for YOLO-style detectors.

This is a prepared scaffold: it records the selected cases and checks runtime
dependencies without pretending that all detector heads expose identical
Grad-CAM targets. RT-DETR attention visualization is tracked separately in the
Grad-CAM plan document.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

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


def write_plan(weights: list[str], images: list[str], out_dir: str | Path, target_layer: str) -> Path:
    out_root = resolve_path(out_dir)
    out_root.mkdir(parents=True, exist_ok=True)
    payload = {
        "status": "prepared",
        "weights": weights,
        "images": images,
        "target_layer": target_layer,
        "dependency_status": dependency_status(),
        "notes": [
            "YOLO Grad-CAM should target the final neck feature map or a detection-head pre-logit feature.",
            "Use identical images across models: correct, false positive, false negative, and class confusion cases.",
            "RT-DETR attention/feature visualization is a separate TODO because decoder attention differs from YOLO heads.",
        ],
    }
    path = out_root / "gradcam_run_plan.json"
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return path


def main() -> None:
    parser = argparse.ArgumentParser(description="Prepare YOLO Grad-CAM analysis inputs.")
    parser.add_argument("--weights", nargs="+", required=True)
    parser.add_argument("--images", nargs="+", required=True)
    parser.add_argument("--out-dir", default="outputs/qualitative/gradcam")
    parser.add_argument("--target-layer", default="auto-neck-last")
    args = parser.parse_args()
    print(write_plan(args.weights, args.images, args.out_dir, args.target_layer))


if __name__ == "__main__":
    main()
