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
from data.converters.common import write_json
from data.converters.uavdt_to_coco import convert_uavdt
from data.converters.visdrone_to_coco import convert_visdrone


def resolve(path: str | Path) -> Path:
    path = Path(path)
    return path if path.is_absolute() else ROOT / path


def maybe_convert_visdrone(cfg: dict[str, str]) -> None:
    images = resolve(cfg["images"])
    annotations = resolve(cfg["annotations"])
    output = resolve(cfg["output"])
    if not images.exists() or not annotations.exists():
        print(f"[skip] VisDrone missing: images={images.exists()} annotations={annotations.exists()}")
        return
    write_json(convert_visdrone(images, annotations), output)
    print(f"[ok] VisDrone -> {output}")


def maybe_convert_uavdt(cfg: dict[str, str]) -> None:
    sequence_dir = resolve(cfg["sequence_dir"])
    annotations = resolve(cfg["annotations"])
    output = resolve(cfg["output"])
    if not sequence_dir.exists() or not annotations.exists():
        print(f"[skip] UAVDT missing: sequence_dir={sequence_dir.exists()} annotations={annotations.exists()}")
        return
    write_json(convert_uavdt(sequence_dir, annotations), output)
    print(f"[ok] UAVDT -> {output}")


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
