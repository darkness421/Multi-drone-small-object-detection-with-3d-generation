"""Convert VisDrone DET annotations to YOLO format."""

from __future__ import annotations

import argparse
import shutil
from dataclasses import dataclass
from pathlib import Path


IMAGE_EXTENSIONS = (".jpg", ".jpeg", ".png", ".bmp")


@dataclass(frozen=True)
class SplitConfig:
    name: str
    source_dir: Path


def find_image_dir(split_dir: Path) -> Path:
    for candidate in ("images", "sequences"):
        path = split_dir / candidate
        if path.exists():
            return path
    return split_dir


def find_annotation_dir(split_dir: Path) -> Path:
    candidate = split_dir / "annotations"
    if candidate.exists():
        return candidate
    return split_dir


def image_size(path: Path) -> tuple[int, int]:
    try:
        from PIL import Image
    except ImportError as exc:
        raise SystemExit(
            "Pillow가 필요합니다. 먼저 `pip install pillow`를 실행하세요."
        ) from exc

    with Image.open(path) as image:
        return image.size


def convert_line(line: str, width: int, height: int) -> str | None:
    parts = [part.strip() for part in line.split(",")]
    if len(parts) < 8:
        return None

    left, top, box_width, box_height = map(float, parts[:4])
    score = int(float(parts[4]))
    category = int(float(parts[5]))

    if score == 0 or category == 0:
        return None
    if box_width <= 0 or box_height <= 0 or width <= 0 or height <= 0:
        return None

    yolo_class = category - 1
    x_center = (left + box_width / 2.0) / width
    y_center = (top + box_height / 2.0) / height
    norm_width = box_width / width
    norm_height = box_height / height

    values = (
        max(0.0, min(1.0, x_center)),
        max(0.0, min(1.0, y_center)),
        max(0.0, min(1.0, norm_width)),
        max(0.0, min(1.0, norm_height)),
    )
    return f"{yolo_class} " + " ".join(f"{value:.6f}" for value in values)


def iter_images(image_dir: Path) -> list[Path]:
    images: list[Path] = []
    for extension in IMAGE_EXTENSIONS:
        images.extend(image_dir.glob(f"*{extension}"))
        images.extend(image_dir.glob(f"*{extension.upper()}"))
    return sorted(images)


def convert_split(split: SplitConfig, output_root: Path, copy_images: bool) -> tuple[int, int]:
    image_dir = find_image_dir(split.source_dir)
    annotation_dir = find_annotation_dir(split.source_dir)
    output_image_dir = output_root / "images" / split.name
    output_label_dir = output_root / "labels" / split.name
    output_image_dir.mkdir(parents=True, exist_ok=True)
    output_label_dir.mkdir(parents=True, exist_ok=True)

    converted_images = 0
    converted_labels = 0
    for image_path in iter_images(image_dir):
        annotation_path = annotation_dir / f"{image_path.stem}.txt"
        if not annotation_path.exists():
            continue

        width, height = image_size(image_path)
        yolo_lines = []
        for raw_line in annotation_path.read_text(encoding="utf-8").splitlines():
            converted = convert_line(raw_line, width, height)
            if converted is not None:
                yolo_lines.append(converted)

        label_path = output_label_dir / f"{image_path.stem}.txt"
        label_path.write_text("\n".join(yolo_lines) + ("\n" if yolo_lines else ""), encoding="utf-8")
        converted_labels += len(yolo_lines)

        if copy_images:
            shutil.copy2(image_path, output_image_dir / image_path.name)
        converted_images += 1

    return converted_images, converted_labels


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Convert VisDrone DET to YOLO format.")
    parser.add_argument(
        "--raw-root",
        type=Path,
        default=Path("data/raw/VisDrone"),
        help="VisDrone raw dataset root.",
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        default=Path("data/processed/visdrone_yolo"),
        help="Output root for YOLO-formatted dataset.",
    )
    parser.add_argument(
        "--copy-images",
        action="store_true",
        help="Copy image files into the processed YOLO dataset.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    splits = (
        SplitConfig("train", args.raw_root / "VisDrone2019-DET-train"),
        SplitConfig("val", args.raw_root / "VisDrone2019-DET-val"),
        SplitConfig("test", args.raw_root / "VisDrone2019-DET-test-dev"),
    )

    for split in splits:
        if not split.source_dir.exists():
            print(f"skip {split.name}: missing {split.source_dir}")
            continue
        images, labels = convert_split(split, args.output_root, args.copy_images)
        print(f"{split.name}: converted {images} images, {labels} labels")


if __name__ == "__main__":
    main()

