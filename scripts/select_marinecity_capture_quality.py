"""Rank real-Cesium MarineCity capture folders for paper-facing visual use."""

from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont


@dataclass
class ImageScore:
    path: Path
    capture_dir: Path
    black_ratio: float
    bright_ratio: float
    mean_luma: float
    score: float


def score_image(path: Path) -> ImageScore:
    image = Image.open(path).convert("RGB")
    arr = np.asarray(image, dtype=np.float32)
    max_channel = arr.max(axis=2)
    luma = 0.2126 * arr[:, :, 0] + 0.7152 * arr[:, :, 1] + 0.0722 * arr[:, :, 2]
    black_ratio = float((max_channel < 10).mean())
    bright_ratio = float((luma > 35).mean())
    mean_luma = float(luma.mean())
    score = (1.0 - black_ratio) * 0.70 + bright_ratio * 0.20 + min(mean_luma / 160.0, 1.0) * 0.10
    return ImageScore(
        path=path,
        capture_dir=path.parents[1],
        black_ratio=black_ratio,
        bright_ratio=bright_ratio,
        mean_luma=mean_luma,
        score=score,
    )


def draw_contact_sheet(groups: list[tuple[Path, list[ImageScore], float]], out: Path, per_group: int = 3) -> None:
    thumb_w, thumb_h = 320, 180
    label_h = 64
    margin = 18
    rows = min(len(groups), 8)
    sheet_w = margin * 2 + per_group * thumb_w
    sheet_h = margin * 2 + rows * (thumb_h + label_h)
    sheet = Image.new("RGB", (sheet_w, sheet_h), "white")
    draw = ImageDraw.Draw(sheet)
    try:
        font = ImageFont.truetype("DejaVuSans.ttf", 16)
        small = ImageFont.truetype("DejaVuSans.ttf", 12)
    except OSError:
        font = ImageFont.load_default()
        small = ImageFont.load_default()

    for row, (capture_dir, images, group_score) in enumerate(groups[:rows]):
        y = margin + row * (thumb_h + label_h)
        label = f"{row + 1}. {capture_dir.name}  score={group_score:.3f}"
        best = images[0]
        metrics = f"black={best.black_ratio:.2%} bright={best.bright_ratio:.2%} luma={best.mean_luma:.1f}"
        draw.text((margin, y), label, fill=(20, 35, 55), font=font)
        draw.text((margin, y + 22), metrics, fill=(70, 80, 95), font=small)
        for col, score in enumerate(images[:per_group]):
            thumb = Image.open(score.path).convert("RGB")
            thumb.thumbnail((thumb_w, thumb_h))
            x = margin + col * thumb_w
            sheet.paste(thumb, (x, y + label_h))
            draw.rectangle((x, y + label_h, x + thumb_w - 1, y + label_h + thumb_h - 1), outline=(210, 218, 228))
    out.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(out)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default="/home/oem/UAV/uav_marinecity/outputs/isaac_exports")
    parser.add_argument("--out-dir", default="outputs/reports/live/marinecity_capture_quality")
    parser.add_argument("--paper-copy-dir", default="paper/figures/results/marinecity_system")
    args = parser.parse_args()

    root = Path(args.root)
    out_dir = Path(args.out_dir)
    paper_dir = Path(args.paper_copy_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    paper_dir.mkdir(parents=True, exist_ok=True)

    paths = sorted(root.glob("*/real_cesium_capture/*_rgb.png"))
    scores = [score_image(path) for path in paths]
    grouped: dict[Path, list[ImageScore]] = defaultdict(list)
    for item in scores:
        grouped[item.capture_dir].append(item)

    rows = []
    group_rows: list[tuple[Path, list[ImageScore], float]] = []
    for capture_dir, images in grouped.items():
        images.sort(key=lambda x: x.score, reverse=True)
        group_score = float(np.mean([img.score for img in images[:3]]))
        group_black = float(np.mean([img.black_ratio for img in images[:3]]))
        summary_path = capture_dir / "real_cesium_capture_summary.json"
        status = ""
        camera_profile = ""
        if summary_path.exists():
            try:
                summary = json.loads(summary_path.read_text(encoding="utf-8"))
                status = str(summary.get("status", ""))
                camera_profile = str(summary.get("camera_profile", {}).get("name", ""))
            except json.JSONDecodeError:
                status = "summary_json_error"
        group_rows.append((capture_dir, images, group_score))
        rows.append(
            {
                "capture_dir": str(capture_dir),
                "capture_name": capture_dir.name,
                "image_count": len(images),
                "mean_top3_score": f"{group_score:.6f}",
                "mean_top3_black_ratio": f"{group_black:.6f}",
                "best_image": str(images[0].path),
                "best_score": f"{images[0].score:.6f}",
                "best_black_ratio": f"{images[0].black_ratio:.6f}",
                "best_bright_ratio": f"{images[0].bright_ratio:.6f}",
                "best_mean_luma": f"{images[0].mean_luma:.3f}",
                "capture_status": status,
                "camera_profile": camera_profile,
            }
        )

    rows.sort(key=lambda row: float(row["mean_top3_score"]), reverse=True)
    group_rows.sort(key=lambda item: item[2], reverse=True)

    csv_path = out_dir / "marinecity_capture_quality_rank.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()) if rows else ["capture_dir"])
        writer.writeheader()
        writer.writerows(rows)

    contact_path = out_dir / "marinecity_capture_quality_top8.png"
    draw_contact_sheet(group_rows, contact_path)

    manifest = {
        "status": "marinecity_capture_quality_ranked",
        "root": str(root),
        "image_count": len(scores),
        "capture_group_count": len(rows),
        "csv": str(csv_path),
        "contact_sheet": str(contact_path),
        "best_capture": rows[0] if rows else None,
        "selection_note": "Ranks existing real-Cesium captures only; no synthetic/fallback city images are generated.",
    }
    manifest_path = out_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")

    if rows:
        paper_contact = paper_dir / "marinecity_capture_quality_top8.png"
        paper_csv = paper_dir / "marinecity_capture_quality_rank.csv"
        paper_contact.write_bytes(contact_path.read_bytes())
        paper_csv.write_bytes(csv_path.read_bytes())

    print(json.dumps(manifest, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
