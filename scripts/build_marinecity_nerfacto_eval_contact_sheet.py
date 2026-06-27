"""Build a compact qualitative sheet for MarineCity Nerfacto eval renders."""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RENDER_DIR = ROOT / "outputs/experiments/3d_generation/nerfstudio_native_runs/marinecity_nerfacto_torch_split067_noapp_2k_20260627_160000_renders"
DEFAULT_EVAL_JSON = ROOT / "outputs/experiments/3d_generation/nerfstudio_native_runs/marinecity_nerfacto_torch_split067_noapp_2k_20260627_160000_ns_eval.json"
DEFAULT_OUT = ROOT / "paper/figures/results/marinecity_system/marinecity_nerfacto_eval_contact_sheet.png"
DEFAULT_MANIFEST = ROOT / "outputs/reports/live/marinecity_nerfacto_eval_contact_sheet.json"


def font(size: int = 22) -> ImageFont.ImageFont:
    for candidate in [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf",
    ]:
        path = Path(candidate)
        if path.exists():
            return ImageFont.truetype(str(path), size=size)
    return ImageFont.load_default()


def fit(image: Image.Image, size: tuple[int, int]) -> Image.Image:
    out = image.copy()
    out.thumbnail(size, Image.Resampling.LANCZOS)
    canvas = Image.new("RGB", size, "white")
    x = (size[0] - out.width) // 2
    y = (size[1] - out.height) // 2
    canvas.paste(out.convert("RGB"), (x, y))
    return canvas


def load_metrics(path: Path) -> dict[str, float]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload.get("results", payload)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--render-dir", type=Path, default=DEFAULT_RENDER_DIR)
    parser.add_argument("--eval-json", type=Path, default=DEFAULT_EVAL_JSON)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    args = parser.parse_args()

    rgb_paths = sorted(args.render_dir.glob("eval_img_*.png"))
    depth_paths = sorted(args.render_dir.glob("eval_depth_*.png"))
    if not rgb_paths:
        raise SystemExit(f"No eval_img_*.png found in {args.render_dir}")

    metrics = load_metrics(args.eval_json)
    title_font = font(28)
    label_font = font(20)
    small_font = font(17)
    tile_w, tile_h = 640, 220
    pad = 24
    header_h = 82
    row_h = tile_h + 70
    rows = len(rgb_paths)
    width = pad * 3 + tile_w * 2
    height = header_h + rows * row_h + pad
    canvas = Image.new("RGB", (width, height), "#f8fafc")
    draw = ImageDraw.Draw(canvas)
    draw.text((pad, 18), "MarineCity Nerfacto held-out render smoke", fill="#111827", font=title_font)
    metric_text = (
        f"PSNR {metrics.get('psnr', 0):.2f} | SSIM {metrics.get('ssim', 0):.3f} | "
        f"LPIPS {metrics.get('lpips', 0):.3f} | FPS {metrics.get('fps', 0):.2f}"
    )
    draw.text((pad, 52), metric_text, fill="#374151", font=small_font)

    y = header_h
    for idx, rgb_path in enumerate(rgb_paths):
        depth_path = depth_paths[idx] if idx < len(depth_paths) else None
        rgb = fit(Image.open(rgb_path), (tile_w, tile_h))
        depth = fit(Image.open(depth_path), (tile_w, tile_h)) if depth_path else Image.new("RGB", (tile_w, tile_h), "white")
        x0 = pad
        x1 = pad * 2 + tile_w
        canvas.paste(rgb, (x0, y + 34))
        canvas.paste(depth, (x1, y + 34))
        draw.text((x0, y), f"Held-out view {idx + 1}: GT/render composite", fill="#1d4ed8", font=label_font)
        draw.text((x1, y), f"Held-out view {idx + 1}: predicted depth", fill="#047857", font=label_font)
        draw.rectangle((x0, y + 34, x0 + tile_w, y + 34 + tile_h), outline="#cbd5e1", width=2)
        draw.rectangle((x1, y + 34, x1 + tile_w, y + 34 + tile_h), outline="#cbd5e1", width=2)
        y += row_h

    args.out.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(args.out)
    args.manifest.parent.mkdir(parents=True, exist_ok=True)
    manifest = {
        "status": "marinecity_nerfacto_eval_contact_sheet_ready",
        "updated_at_kst": datetime.now().strftime("%Y-%m-%d %H:%M:%S KST"),
        "render_dir": str(args.render_dir),
        "eval_json": str(args.eval_json),
        "out": str(args.out),
        "rgb_count": len(rgb_paths),
        "depth_count": len(depth_paths),
        "metrics": metrics,
        "claiming_rule": "Qualitative held-out Nerfacto smoke visualization; not a final multi-method benchmark figure.",
    }
    args.manifest.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({"out": str(args.out), "manifest": str(args.manifest), "rgb_count": len(rgb_paths)}, indent=2))


if __name__ == "__main__":
    main()
