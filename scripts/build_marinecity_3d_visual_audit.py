"""Build a visual audit sheet for MarineCity 3D reconstruction outputs."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT_DIR = ROOT / "outputs/reports/live/marinecity_3d_visual_audit"


ITEMS = [
    (
        "Input real-Cesium UAV views",
        ROOT / "figures/results/marinecity_system/paper_fig04_marinecity_clean_qualitative.png",
        ROOT / "paper/figures/results/marinecity_system/paper_fig04_marinecity_clean_qualitative.png",
    ),
    (
        "Nerfacto held-out render",
        ROOT / "figures/results/marinecity_system/marinecity_nerfacto_eval_contact_sheet.png",
        ROOT / "paper/figures/results/marinecity_system/marinecity_nerfacto_eval_contact_sheet.png",
    ),
    (
        "Instant-NGP held-out render",
        ROOT / "figures/results/marinecity_system/marinecity_instant_ngp_eval_contact_sheet.png",
        ROOT / "paper/figures/results/marinecity_system/marinecity_instant_ngp_eval_contact_sheet.png",
    ),
    (
        "3DGS/Splatfacto held-out render",
        ROOT / "figures/results/marinecity_system/marinecity_splatfacto_eval_contact_sheet.png",
        ROOT / "paper/figures/results/marinecity_system/marinecity_splatfacto_eval_contact_sheet.png",
    ),
    (
        "Depth-backed view consistency",
        ROOT / "figures/results/marinecity_system/marinecity_depth_view_consistency_sanity.png",
        ROOT / "paper/figures/results/marinecity_system/marinecity_depth_view_consistency_sanity.png",
    ),
    (
        "Nerfacto iteration sweep",
        ROOT / "figures/results/marinecity_system/marinecity_nerfacto_iteration_sweep.png",
        ROOT / "paper/figures/results/marinecity_system/marinecity_nerfacto_iteration_sweep.png",
    ),
]


def font(size: int, bold: bool = False) -> ImageFont.ImageFont:
    names = ["DejaVuSans-Bold.ttf", "DejaVuSans.ttf"] if bold else ["DejaVuSans.ttf"]
    for name in names:
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default()


FONT_TITLE = font(34, True)
FONT_H = font(22, True)
FONT_BODY = font(16)


def resolve_path(primary: Path, fallback: Path) -> Path | None:
    if primary.exists():
        return primary
    if fallback.exists():
        return fallback
    return None


def fit(path: Path | None, size: tuple[int, int]) -> Image.Image:
    if path is None:
        canvas = Image.new("RGB", size, "#f8fafc")
        draw = ImageDraw.Draw(canvas)
        draw.rectangle([0, 0, size[0] - 1, size[1] - 1], outline="#cbd5e1", width=2)
        draw.text((20, size[1] // 2), "missing artifact", fill="#b91c1c", font=FONT_BODY)
        return canvas
    image = Image.open(path).convert("RGB")
    image.thumbnail(size, Image.Resampling.LANCZOS)
    canvas = Image.new("RGB", size, "white")
    canvas.paste(image, ((size[0] - image.width) // 2, (size[1] - image.height) // 2))
    return canvas


def build_sheet(items: list[dict[str, Any]], out_path: Path) -> None:
    cell_w, cell_h = 720, 430
    gap = 24
    margin = 36
    header_h = 82
    cols = 2
    rows = (len(items) + cols - 1) // cols
    width = margin * 2 + cols * cell_w + (cols - 1) * gap
    height = header_h + margin + rows * cell_h + (rows - 1) * gap + margin
    canvas = Image.new("RGB", (width, height), "#f1f5f9")
    draw = ImageDraw.Draw(canvas)
    draw.rectangle([0, 0, width, header_h], fill="#0f172a")
    draw.text((margin, 22), "MarineCity 3D Visual Audit", fill="white", font=FONT_TITLE)
    for idx, item in enumerate(items):
        col = idx % cols
        row = idx // cols
        x = margin + col * (cell_w + gap)
        y = header_h + margin + row * (cell_h + gap)
        draw.rounded_rectangle([x, y, x + cell_w, y + cell_h], radius=8, fill="white", outline="#cbd5e1", width=2)
        draw.text((x + 18, y + 14), item["title"], fill="#0f172a", font=FONT_H)
        image = fit(item["path"], (cell_w - 36, cell_h - 82))
        canvas.paste(image, (x + 18, y + 58))
        if item["path"]:
            draw.text((x + 18, y + cell_h - 20), str(item["path"].relative_to(ROOT))[:92], fill="#475569", font=FONT_BODY)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(out_path)


def main() -> None:
    parser = argparse.ArgumentParser(description="Build MarineCity 3D visual audit sheet.")
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    args = parser.parse_args()
    items = []
    for title, primary, fallback in ITEMS:
        path = resolve_path(primary, fallback)
        items.append({"title": title, "path": path})
    out_png = args.out_dir / "marinecity_3d_visual_audit_sheet.png"
    out_json = args.out_dir / "marinecity_3d_visual_audit_manifest.json"
    build_sheet(items, out_png)
    out_json.write_text(
        json.dumps(
            {
                "status": "marinecity_3d_visual_audit_complete",
                "sheet": str(out_png.relative_to(ROOT)),
                "items": [
                    {"title": item["title"], "path": str(item["path"].relative_to(ROOT)) if item["path"] else None}
                    for item in items
                ],
            },
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    print(json.dumps({"sheet": str(out_png.relative_to(ROOT)), "manifest": str(out_json.relative_to(ROOT))}, indent=2))


if __name__ == "__main__":
    main()
