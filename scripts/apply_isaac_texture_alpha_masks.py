"""Apply transparent footprint masks to Isaac billboard textures.

The source crops remain VisDrone-derived images. This script only adds an alpha
channel so the cards do not render as opaque rectangular patches over the real
Cesium Marine City terrain.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter


PEDESTRIAN_CLASSES = {"pedestrian", "person", "people"}


def class_name_from_path(path: Path) -> str:
    stem = path.stem.lower()
    return stem.split("_", 1)[0]


def soft_mask(path: Path, size: tuple[int, int], feather: float) -> Image.Image:
    width, height = size
    class_name = class_name_from_path(path)
    mask = Image.new("L", size, 0)
    draw = ImageDraw.Draw(mask)

    if class_name in PEDESTRIAN_CLASSES:
        margin_x = max(1, int(width * 0.18))
        margin_y = max(1, int(height * 0.04))
        draw.ellipse((margin_x, margin_y, width - margin_x, height - margin_y), fill=255)
    else:
        margin_x = max(1, int(width * 0.06))
        margin_y = max(1, int(height * 0.04))
        radius = max(2, int(min(width, height) * 0.16))
        draw.rounded_rectangle(
            (margin_x, margin_y, width - margin_x, height - margin_y),
            radius=radius,
            fill=255,
        )

    blur_radius = max(1.0, min(width, height) * feather)
    return mask.filter(ImageFilter.GaussianBlur(radius=blur_radius))


def apply_mask(path: Path, out_path: Path, feather: float) -> None:
    image = Image.open(path).convert("RGBA")
    mask = soft_mask(path, image.size, feather)
    existing_alpha = image.getchannel("A")
    alpha = Image.eval(Image.blend(existing_alpha, mask, 1.0), lambda value: value)
    image.putalpha(alpha)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    image.save(out_path)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--src-dir", type=Path, default=Path("sim/isaac/assets/visdrone_objects"))
    parser.add_argument("--out-dir", type=Path, default=None)
    parser.add_argument("--feather", type=float, default=0.035)
    parser.add_argument("--in-place", action="store_true")
    args = parser.parse_args()

    out_dir = args.src_dir if args.in_place else args.out_dir
    if out_dir is None:
        raise SystemExit("Use --in-place or provide --out-dir.")

    paths = sorted(args.src_dir.glob("*.png"))
    if not paths:
        raise SystemExit(f"No PNG textures found in {args.src_dir}")

    for path in paths:
        out_path = out_dir / path.name
        apply_mask(path, out_path, args.feather)
        print(out_path)


if __name__ == "__main__":
    main()
