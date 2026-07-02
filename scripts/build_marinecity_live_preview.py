"""Build a compact live preview sheet for the MarineCity Isaac stage."""

from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


DEFAULT_CAPTURE_DIR = Path("outputs/isaac_exports/marinecity_gpu1_replicator_direct_v5/replicator_direct")
DEFAULT_OUT = Path("outputs/reports/live/marinecity_isaac_preview.png")


def _load_font(size: int) -> ImageFont.ImageFont:
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    for candidate in candidates:
        path = Path(candidate)
        if path.exists():
            return ImageFont.truetype(str(path), size=size)
    return ImageFont.load_default()


def _fit(image: Image.Image, width: int, height: int) -> Image.Image:
    fitted = image.convert("RGB").copy()
    fitted.thumbnail((width, height), Image.Resampling.LANCZOS)
    canvas = Image.new("RGB", (width, height), "#F8FAFC")
    x = (width - fitted.width) // 2
    y = (height - fitted.height) // 2
    canvas.paste(fitted, (x, y))
    return canvas


def _draw_panel(
    canvas: Image.Image,
    draw: ImageDraw.ImageDraw,
    x: int,
    y: int,
    title: str,
    image_path: Path,
    font_title: ImageFont.ImageFont,
    font_small: ImageFont.ImageFont,
) -> None:
    panel_w = 420
    panel_h = 300
    image_h = 232
    draw.rounded_rectangle((x, y, x + panel_w, y + panel_h), radius=10, fill="#FFFFFF", outline="#CBD5E1", width=2)
    draw.text((x + 16, y + 12), title, fill="#0F172A", font=font_title)
    if image_path.exists():
        image = Image.open(image_path)
        fitted = _fit(image, panel_w - 32, image_h)
        canvas.paste(fitted, (x + 16, y + 52))
        draw.text((x + 16, y + panel_h - 24), image_path.name, fill="#64748B", font=font_small)
    else:
        draw.rectangle((x + 16, y + 52, x + panel_w - 16, y + 52 + image_h), fill="#FEE2E2", outline="#EF4444")
        draw.text((x + 28, y + 138), "MISSING", fill="#B91C1C", font=font_title)


def build_preview(capture_dir: Path, out_path: Path) -> Path:
    font_title = _load_font(18)
    font_header = _load_font(26)
    font_small = _load_font(12)
    canvas = Image.new("RGB", (1320, 760), "#EEF2F7")
    draw = ImageDraw.Draw(canvas)

    draw.text((34, 26), "MarineCity Isaac GPU1 Preview", fill="#0F172A", font=font_header)
    draw.text(
        (34, 62),
        "3 UAV views from the real-Cesium MarineCity overlay: RGB, detector-friendly bbox preview, and depth preview.",
        fill="#475569",
        font=font_small,
    )

    rows = [
        ("UAV 01 RGB", "frame_001_uav_01_rgb.png"),
        ("UAV 02 RGB", "frame_002_uav_02_rgb.png"),
        ("UAV 03 RGB", "frame_003_uav_03_rgb.png"),
        ("UAV 01 BBox", "frame_001_uav_01_bbox_preview.png"),
        ("UAV 02 BBox", "frame_002_uav_02_bbox_preview.png"),
        ("UAV 03 BBox", "frame_003_uav_03_bbox_preview.png"),
    ]
    for index, (title, filename) in enumerate(rows):
        col = index % 3
        row = index // 3
        _draw_panel(
            canvas,
            draw,
            34 + col * 430,
            104 + row * 318,
            title,
            capture_dir / filename,
            font_title,
            font_small,
        )

    out_path.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(out_path)
    return out_path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--capture-dir", default=str(DEFAULT_CAPTURE_DIR))
    parser.add_argument("--out", default=str(DEFAULT_OUT))
    args = parser.parse_args()
    out_path = build_preview(Path(args.capture_dir), Path(args.out))
    print(out_path)


if __name__ == "__main__":
    main()
