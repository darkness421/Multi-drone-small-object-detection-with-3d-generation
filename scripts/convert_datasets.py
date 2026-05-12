"""Run configured dataset converters from a Windows-friendly entrypoint."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from data.converters.aitod_to_coco import normalize_aitod
from data.converters.coco_to_yolo import convert_coco_splits_to_yolo, convert_coco_to_yolo
from data.converters.common import write_json
from data.converters.uavdt_to_coco import convert_uavdt
from data.converters.visdrone_to_coco import convert_visdrone


def resolve(path: str | Path) -> Path:
    path = Path(path)
    return path if path.is_absolute() else ROOT / path


def maybe_convert_visdrone(cfg: dict[str, str]) -> None:
    if "train_images" in cfg:
        split_outputs: dict[str, Path] = {}
        split_specs = {
            "train": ("train_images", "train_annotations", "train_output"),
            "val": ("val_images", "val_annotations", "val_output"),
            "test": ("test_images", "test_annotations", "test_output"),
        }
        for split, (images_key, annotations_key, output_key) in split_specs.items():
            images = resolve(cfg.get(images_key, ""))
            annotations = resolve(cfg.get(annotations_key, ""))
            output = resolve(cfg.get(output_key, f"data/processed/visdrone_{split}_coco.json"))
            if not images.exists() or not annotations.exists():
                print(f"[skip] VisDrone {split} missing: images={images.exists()} annotations={annotations.exists()}")
                continue
            write_json(convert_visdrone(images, annotations), output)
            split_outputs[split] = output
            print(f"[ok] VisDrone {split} -> {output}")

        if "train" in split_outputs and "val" in split_outputs:
            yolo_output = resolve(cfg.get("yolo_output", "data/processed/visdrone_yolo"))
            data_yaml = convert_coco_splits_to_yolo(split_outputs, yolo_output, copy_images=True)
            print(f"[ok] VisDrone YOLO explicit splits -> {data_yaml}")
        else:
            print("[skip] VisDrone YOLO: train and val splits are required")
        return

    images = resolve(cfg["images"])
    annotations = resolve(cfg["annotations"])
    output = resolve(cfg["output"])
    if not images.exists() or not annotations.exists():
        print(f"[skip] VisDrone missing: images={images.exists()} annotations={annotations.exists()}")
        return
    write_json(convert_visdrone(images, annotations), output)
    print(f"[ok] VisDrone -> {output}")
    yolo_output = resolve(cfg.get("yolo_output", "data/processed/visdrone_yolo"))
    data_yaml = convert_coco_to_yolo(output, yolo_output, copy_images=True)
    print(f"[ok] VisDrone YOLO -> {data_yaml}")


def maybe_convert_uavdt(cfg: dict[str, str]) -> None:
    sequence_dir = resolve(cfg["sequence_dir"])
    annotations = resolve(cfg["annotations"])
    output = resolve(cfg["output"])
    if not sequence_dir.exists() or not annotations.exists():
        print(f"[skip] UAVDT missing: sequence_dir={sequence_dir.exists()} annotations={annotations.exists()}")
        return
    write_json(convert_uavdt(sequence_dir, annotations), output)
    print(f"[ok] UAVDT -> {output}")
    yolo_output = resolve(cfg.get("yolo_output", "data/processed/uavdt_yolo"))
    data_yaml = convert_coco_to_yolo(output, yolo_output, copy_images=True)
    print(f"[ok] UAVDT YOLO -> {data_yaml}")


def maybe_convert_aitod(cfg: dict[str, str]) -> None:
    annotations = resolve(cfg["annotations"])
    output = resolve(cfg["output"])
    if not annotations.exists():
        print(f"[skip] AI-TOD missing: annotations={annotations.exists()}")
        return
    write_json(normalize_aitod(annotations), output)
    print(f"[ok] AI-TOD -> {output}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Convert configured UAV datasets to COCO JSON.")
    parser.add_argument("--config", default="configs/dataset_roots.yaml")
    args = parser.parse_args()

    config_path = resolve(args.config)
    payload = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    datasets = payload.get("datasets", {})
    if "visdrone" in datasets:
        maybe_convert_visdrone(datasets["visdrone"])
    if "uavdt" in datasets:
        maybe_convert_uavdt(datasets["uavdt"])
    if "aitod" in datasets:
        maybe_convert_aitod(datasets["aitod"])


if __name__ == "__main__":
    main()
