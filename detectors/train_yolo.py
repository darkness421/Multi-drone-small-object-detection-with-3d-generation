"""YOLO training entrypoint for Windows and VS Code workflows."""

from __future__ import annotations

import argparse
import json

try:
    from .ultralytics_runner import eval_yolo, train_yolo
except ImportError:
    from ultralytics_runner import eval_yolo, train_yolo


def main() -> None:
    parser = argparse.ArgumentParser(description="Train or evaluate YOLOv8/YOLOv11 baselines.")
    parser.add_argument("mode", choices=["train", "eval"], nargs="?", default="train")
    parser.add_argument("--model", default="yolo11n.pt", help="Example: yolo11n.pt or yolov8n.pt")
    parser.add_argument("--data-yaml", default="configs/detector/visdrone_yolo_data.yaml")
    parser.add_argument("--epochs", type=int, default=100)
    parser.add_argument("--imgsz", type=int, default=1280)
    parser.add_argument("--batch", type=int, default=8)
    parser.add_argument("--device", default=None, help="Ultralytics device string, for example '0' or '0,1'.")
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--non-deterministic", action="store_true")
    parser.add_argument("--from-scratch", action="store_true", help="Train from model YAML instead of pretrained .pt weights.")
    parser.add_argument("--roc-auc", action="store_true", help="During eval, also compute image-level ROC-AUC.")
    parser.add_argument("--roc-auc-split", default="val")
    parser.add_argument("--roc-auc-max-images", type=int, default=None)
    parser.add_argument("--project", default="outputs/detectors")
    parser.add_argument("--name", default=None)
    args = parser.parse_args()

    if args.mode == "train":
        result = train_yolo(
            model=args.model,
            data_yaml=args.data_yaml,
            epochs=args.epochs,
            imgsz=args.imgsz,
            batch=args.batch,
            device=args.device,
            seed=args.seed,
            deterministic=not args.non_deterministic,
            from_scratch=args.from_scratch,
            project=args.project,
            name=args.name,
        )
    else:
        result = eval_yolo(
            model=args.model,
            data_yaml=args.data_yaml,
            imgsz=args.imgsz,
            device=args.device,
            roc_auc=args.roc_auc,
            roc_auc_split=args.roc_auc_split,
            roc_auc_max_images=args.roc_auc_max_images,
            project=args.project,
            name=args.name,
        )
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
