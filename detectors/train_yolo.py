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
    parser.add_argument("--workers", type=int, default=4, help="Dataloader workers. Keep modest on shared servers.")
    parser.add_argument("--device", default=None, help="Ultralytics device string, for example '0' or '0,1'.")
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--non-deterministic", action="store_true")
    parser.add_argument("--from-scratch", action="store_true", help="Train from model YAML instead of pretrained .pt weights.")
    parser.add_argument("--init-weights", default=None, help="Optional pretrained weights to load into a YAML architecture.")
    parser.add_argument("--method", default=None, help="Optional method label written to run summaries.")
    parser.add_argument("--ablation", default=None, help="Optional ablation label written to run summaries.")
    parser.add_argument("--base-model", default=None, help="Optional base model label for proposed ablations.")
    parser.add_argument("--proposed-module", default=None, help="Optional proposed module label.")
    parser.add_argument("--implementation-status", default=None, help="Optional implementation status label.")
    parser.add_argument("--model-patches", default=None, help="Comma-separated runtime patches, e.g. wavelet_stem,cbam_neck.")
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
            workers=args.workers,
            device=args.device,
            seed=args.seed,
            deterministic=not args.non_deterministic,
            from_scratch=args.from_scratch,
            init_weights=args.init_weights,
            method=args.method,
            ablation=args.ablation,
            base_model=args.base_model,
            proposed_module=args.proposed_module,
            implementation_status=args.implementation_status,
            model_patches=args.model_patches,
            project=args.project,
            name=args.name,
        )
    else:
        result = eval_yolo(
            model=args.model,
            data_yaml=args.data_yaml,
            imgsz=args.imgsz,
            workers=args.workers,
            device=args.device,
            roc_auc=args.roc_auc,
            roc_auc_split=args.roc_auc_split,
            roc_auc_max_images=args.roc_auc_max_images,
            method=args.method,
            ablation=args.ablation,
            base_model=args.base_model,
            proposed_module=args.proposed_module,
            implementation_status=args.implementation_status,
            model_patches=args.model_patches,
            project=args.project,
            name=args.name,
        )
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
