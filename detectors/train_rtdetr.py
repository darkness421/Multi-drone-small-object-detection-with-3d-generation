"""RT-DETR baseline entrypoint through the Ultralytics runner.

Ultralytics commonly ships RT-DETR weights such as rtdetr-l.pt. If an R18
checkpoint is added later, pass it through --model without changing this file.
"""

from __future__ import annotations

import argparse
import json

try:
    from .ultralytics_runner import eval_yolo, train_yolo
except ImportError:
    from ultralytics_runner import eval_yolo, train_yolo


def main() -> None:
    parser = argparse.ArgumentParser(description="Train or evaluate an RT-DETR baseline.")
    parser.add_argument("mode", choices=["train", "eval"], nargs="?", default="train")
    parser.add_argument("--model", default="rtdetr-l.pt")
    parser.add_argument("--data-yaml", default="configs/detector/visdrone_yolo_data.yaml")
    parser.add_argument("--epochs", type=int, default=100)
    parser.add_argument("--imgsz", type=int, default=1280)
    parser.add_argument("--batch", type=int, default=4)
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
            project=args.project,
            name=args.name,
        )
    else:
        result = eval_yolo(
            model=args.model,
            data_yaml=args.data_yaml,
            imgsz=args.imgsz,
            project=args.project,
            name=args.name,
        )
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
