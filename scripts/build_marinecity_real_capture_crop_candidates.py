"""Build cropped qualitative candidates from real Cesium MarineCity captures.

The script does not synthesize or replace city content. It searches existing
real-Cesium RGB captures for 16:9 crops that minimize black/void tile boundary
area while preserving as much visible city/object content as possible.
"""

from __future__ import annotations

import argparse
import csv
import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont


@dataclass
class CropCandidate:
    source: Path
    capture_name: str
    crop_box: tuple[int, int, int, int]
    crop_path: Path
    black_ratio: float
    bright_ratio: float
    mean_luma: float
    area_ratio: float
    score: float


def metrics(arr: np.ndarray) -> tuple[float, float, float]:
    max_channel = arr.max(axis=2)
    luma = 0.2126 * arr[:, :, 0] + 0.7152 * arr[:, :, 1] + 0.0722 * arr[:, :, 2]
    black_ratio = float((max_channel < 10).mean())
    bright_ratio = float((luma > 35).mean())
    mean_luma = float(luma.mean())
    return black_ratio, bright_ratio, mean_luma


def integral_image(arr: np.ndarray) -> np.ndarray:
    return np.pad(arr.cumsum(axis=0).cumsum(axis=1), ((1, 0), (1, 0)), mode="constant")


def rect_sum(integral: np.ndarray, x0: int, y0: int, x1: int, y1: int) -> float:
    return float(integral[y1, x1] - integral[y0, x1] - integral[y1, x0] + integral[y0, x0])


def best_crop_box(image: Image.Image, aspect: float = 16 / 9) -> tuple[tuple[int, int, int, int], dict[str, float]]:
    arr = np.asarray(image.convert("RGB"), dtype=np.float32)
    h, w = arr.shape[:2]
    max_channel = arr.max(axis=2)
    luma_map = 0.2126 * arr[:, :, 0] + 0.7152 * arr[:, :, 1] + 0.0722 * arr[:, :, 2]
    black_integral = integral_image((max_channel < 10).astype(np.float32))
    bright_integral = integral_image((luma_map > 35).astype(np.float32))
    luma_integral = integral_image(luma_map.astype(np.float32))
    best: tuple[int, int, int, int] | None = None
    best_stats: dict[str, float] = {}
    best_score = -1.0

    scales = [0.95, 0.85, 0.75, 0.65, 0.55, 0.45, 0.38]
    for scale in scales:
        crop_w = int(w * scale)
        crop_h = int(crop_w / aspect)
        if crop_h > h:
            crop_h = int(h * scale)
            crop_w = int(crop_h * aspect)
        crop_w = max(32, min(crop_w, w))
        crop_h = max(32, min(crop_h, h))
        if crop_w > w or crop_h > h:
            continue

        step_x = max(24, crop_w // 7)
        step_y = max(24, crop_h // 7)
        xs = list(range(0, max(1, w - crop_w + 1), step_x))
        ys = list(range(0, max(1, h - crop_h + 1), step_y))
        if not xs or xs[-1] != w - crop_w:
            xs.append(w - crop_w)
        if not ys or ys[-1] != h - crop_h:
            ys.append(h - crop_h)

        for y in ys:
            for x in xs:
                x1 = x + crop_w
                y1 = y + crop_h
                area = float(crop_w * crop_h)
                black = rect_sum(black_integral, x, y, x1, y1) / area
                bright = rect_sum(bright_integral, x, y, x1, y1) / area
                luma = rect_sum(luma_integral, x, y, x1, y1) / area
                area_ratio = (crop_w * crop_h) / (w * h)
                visible = 1.0 - black
                score = visible * 0.74 + bright * 0.12 + min(luma / 160.0, 1.0) * 0.04 + area_ratio * 0.10
                # Strongly prefer crops that get under 25% void even if smaller.
                if black < 0.25:
                    score += 0.08
                if black < 0.10:
                    score += 0.05
                if score > best_score:
                    best_score = score
                    best = (x, y, x + crop_w, y + crop_h)
                    best_stats = {
                        "black_ratio": black,
                        "bright_ratio": bright,
                        "mean_luma": luma,
                        "area_ratio": area_ratio,
                        "score": score,
                    }

    if best is None:
        black, bright, luma = metrics(arr)
        best = (0, 0, w, h)
        best_stats = {
            "black_ratio": black,
            "bright_ratio": bright,
            "mean_luma": luma,
            "area_ratio": 1.0,
            "score": (1.0 - black) * 0.8 + bright * 0.1 + min(luma / 160.0, 1.0) * 0.1,
        }
    return best, best_stats


def discover_images(root: Path) -> list[Path]:
    return sorted(root.glob("*/real_cesium_capture/*_rgb.png"))


def draw_contact(candidates: list[CropCandidate], out: Path, limit: int) -> None:
    thumb_w, thumb_h = 360, 202
    label_h = 62
    cols = 3
    rows = max(1, int(np.ceil(min(len(candidates), limit) / cols)))
    margin = 18
    sheet = Image.new("RGB", (margin * 2 + cols * thumb_w, margin * 2 + rows * (thumb_h + label_h)), "white")
    draw = ImageDraw.Draw(sheet)
    try:
        font = ImageFont.truetype("DejaVuSans.ttf", 14)
        small = ImageFont.truetype("DejaVuSans.ttf", 11)
    except OSError:
        font = ImageFont.load_default()
        small = ImageFont.load_default()

    for idx, cand in enumerate(candidates[:limit]):
        row, col = divmod(idx, cols)
        x = margin + col * thumb_w
        y = margin + row * (thumb_h + label_h)
        title = f"{idx + 1}. {cand.capture_name}"
        stats = f"black={cand.black_ratio:.1%} area={cand.area_ratio:.1%} score={cand.score:.3f}"
        draw.text((x, y), title[:44], fill=(18, 32, 50), font=font)
        draw.text((x, y + 20), stats, fill=(65, 74, 88), font=small)
        thumb = Image.open(cand.crop_path).convert("RGB")
        thumb.thumbnail((thumb_w, thumb_h))
        sheet.paste(thumb, (x, y + label_h))
        draw.rectangle((x, y + label_h, x + thumb_w - 1, y + label_h + thumb_h - 1), outline=(205, 214, 224))
    out.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(out)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default="/home/oem/UAV/uav_marinecity/outputs/isaac_exports")
    parser.add_argument("--out-dir", default="outputs/reports/live/marinecity_real_capture_crops")
    parser.add_argument("--paper-copy-dir", default="paper/figures/results/marinecity_system")
    parser.add_argument("--limit", type=int, default=12)
    args = parser.parse_args()

    root = Path(args.root)
    out_dir = Path(args.out_dir)
    crop_dir = out_dir / "crops"
    paper_dir = Path(args.paper_copy_dir)
    crop_dir.mkdir(parents=True, exist_ok=True)
    paper_dir.mkdir(parents=True, exist_ok=True)

    candidates: list[CropCandidate] = []
    for image_path in discover_images(root):
        image = Image.open(image_path).convert("RGB")
        box, stats = best_crop_box(image)
        capture_name = image_path.parents[1].name
        crop_name = f"{capture_name}_{image_path.stem}_crop.png"
        crop_path = crop_dir / crop_name
        image.crop(box).save(crop_path)
        candidates.append(
            CropCandidate(
                source=image_path,
                capture_name=capture_name,
                crop_box=box,
                crop_path=crop_path,
                black_ratio=stats["black_ratio"],
                bright_ratio=stats["bright_ratio"],
                mean_luma=stats["mean_luma"],
                area_ratio=stats["area_ratio"],
                score=stats["score"],
            )
        )

    candidates.sort(key=lambda item: item.score, reverse=True)
    csv_path = out_dir / "marinecity_real_capture_crop_candidates.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "rank",
                "capture_name",
                "source",
                "crop_path",
                "crop_box",
                "black_ratio",
                "bright_ratio",
                "mean_luma",
                "area_ratio",
                "score",
            ],
        )
        writer.writeheader()
        for rank, cand in enumerate(candidates, start=1):
            writer.writerow(
                {
                    "rank": rank,
                    "capture_name": cand.capture_name,
                    "source": str(cand.source),
                    "crop_path": str(cand.crop_path),
                    "crop_box": json.dumps(cand.crop_box),
                    "black_ratio": f"{cand.black_ratio:.6f}",
                    "bright_ratio": f"{cand.bright_ratio:.6f}",
                    "mean_luma": f"{cand.mean_luma:.3f}",
                    "area_ratio": f"{cand.area_ratio:.6f}",
                    "score": f"{cand.score:.6f}",
                }
            )

    contact = out_dir / "marinecity_real_capture_crop_top12.png"
    draw_contact(candidates, contact, args.limit)
    manifest = {
        "status": "marinecity_real_capture_crops_complete",
        "root": str(root),
        "image_count": len(candidates),
        "crop_count": len(candidates),
        "csv": str(csv_path),
        "contact_sheet": str(contact),
        "best": {
            "capture_name": candidates[0].capture_name,
            "source": str(candidates[0].source),
            "crop_path": str(candidates[0].crop_path),
            "black_ratio": candidates[0].black_ratio,
            "area_ratio": candidates[0].area_ratio,
            "score": candidates[0].score,
        }
        if candidates
        else None,
        "note": "Crops are from real Cesium captures only; no synthetic/fallback geometry is generated.",
    }
    manifest_path = out_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")

    paper_contact = paper_dir / "marinecity_real_capture_crop_top12.png"
    paper_csv = paper_dir / "marinecity_real_capture_crop_candidates.csv"
    paper_manifest = paper_dir / "marinecity_real_capture_crop_manifest.json"
    paper_contact.write_bytes(contact.read_bytes())
    paper_csv.write_bytes(csv_path.read_bytes())
    paper_manifest.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(manifest, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
