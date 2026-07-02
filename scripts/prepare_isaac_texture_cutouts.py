"""Prepare VisDrone crop cutouts for Isaac/Cesium simulation assets."""

from __future__ import annotations

import argparse
import csv
import json
import random
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from PIL import Image, ImageDraw


DEFAULT_CLASSES = ("pedestrian", "people", "car", "van", "truck", "bus", "motor")


@dataclass(frozen=True)
class YoloDataset:
    root: Path
    train: str
    val: str
    test: str | None
    names: dict[int, str]


def parse_simple_yolo_yaml(path: Path) -> YoloDataset:
    lines = path.read_text(encoding="utf-8").splitlines()
    values: dict[str, str] = {}
    names: dict[int, str] = {}
    in_names = False
    for raw in lines:
        line = raw.split("#", 1)[0].rstrip()
        if not line.strip():
            continue
        if line.startswith("names:"):
            in_names = True
            continue
        if in_names and raw.startswith(" "):
            key, _, value = line.strip().partition(":")
            if key and value:
                names[int(key)] = value.strip().strip("\"'")
            continue
        in_names = False
        key, _, value = line.partition(":")
        if key and value:
            values[key.strip()] = value.strip().strip("\"'")
    return YoloDataset(
        root=Path(values["path"]),
        train=values["train"],
        val=values["val"],
        test=values.get("test"),
        names=names,
    )


def image_for_label(label_path: Path, image_dir: Path) -> Path | None:
    for suffix in (".jpg", ".jpeg", ".png", ".JPG", ".JPEG", ".PNG"):
        candidate = image_dir / f"{label_path.stem}{suffix}"
        if candidate.exists():
            return candidate
    return None


def yolo_to_xyxy(row: list[str], width: int, height: int, pad: float) -> tuple[int, int, int, int]:
    _, cx, cy, bw, bh = row[:5]
    cx_f = float(cx) * width
    cy_f = float(cy) * height
    bw_f = float(bw) * width
    bh_f = float(bh) * height
    pad_x = bw_f * pad
    pad_y = bh_f * pad
    x1 = max(0, int(round(cx_f - bw_f / 2 - pad_x)))
    y1 = max(0, int(round(cy_f - bh_f / 2 - pad_y)))
    x2 = min(width, int(round(cx_f + bw_f / 2 + pad_x)))
    y2 = min(height, int(round(cy_f + bh_f / 2 + pad_y)))
    return x1, y1, x2, y2


def iter_label_rows(label_path: Path) -> Iterable[list[str]]:
    for line in label_path.read_text(encoding="utf-8", errors="ignore").splitlines():
        parts = line.strip().split()
        if len(parts) >= 5:
            yield parts


def save_contact_sheet(items: list[dict[str, str]], out_path: Path, thumb: int = 96) -> None:
    if not items:
        return
    cols = 8
    rows = (len(items) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * thumb, rows * (thumb + 18)), "white")
    draw = ImageDraw.Draw(sheet)
    for idx, item in enumerate(items):
        x = (idx % cols) * thumb
        y = (idx // cols) * (thumb + 18)
        image = Image.open(item["cutout_path"]).convert("RGB")
        image.thumbnail((thumb, thumb))
        sheet.paste(image, (x + (thumb - image.width) // 2, y))
        label = item["class_name"][:14]
        draw.text((x + 4, y + thumb + 2), label, fill=(20, 30, 40))
    out_path.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(out_path)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-yaml", type=Path, default=Path("configs/detector/visdrone_yolo_data.yaml"))
    parser.add_argument("--split", default="train", choices=["train", "val", "test"])
    parser.add_argument("--out-dir", type=Path, default=Path("outputs/isaac_assets/visdrone_cutouts"))
    parser.add_argument("--classes", nargs="+", default=list(DEFAULT_CLASSES))
    parser.add_argument("--quota-per-class", type=int, default=16)
    parser.add_argument("--min-size", type=int, default=14)
    parser.add_argument("--pad", type=float, default=0.12)
    parser.add_argument("--seed", type=int, default=2026)
    args = parser.parse_args()

    dataset = parse_simple_yolo_yaml(args.data_yaml)
    split_dir = getattr(dataset, args.split)
    image_dir = dataset.root / split_dir
    label_dir = dataset.root / split_dir.replace("images/", "labels/")
    wanted = set(args.classes)
    rng = random.Random(args.seed)

    label_paths = list(label_dir.glob("*.txt"))
    rng.shuffle(label_paths)
    counts = {name: 0 for name in wanted}
    manifest: list[dict[str, str]] = []
    images_out = args.out_dir / "images"
    images_out.mkdir(parents=True, exist_ok=True)

    for label_path in label_paths:
        if all(count >= args.quota_per_class for count in counts.values()):
            break
        image_path = image_for_label(label_path, image_dir)
        if image_path is None:
            continue
        try:
            image = Image.open(image_path).convert("RGBA")
        except OSError:
            continue
        width, height = image.size
        for box_idx, row in enumerate(iter_label_rows(label_path)):
            class_id = int(float(row[0]))
            class_name = dataset.names.get(class_id, f"class_{class_id}")
            if class_name not in wanted or counts[class_name] >= args.quota_per_class:
                continue
            x1, y1, x2, y2 = yolo_to_xyxy(row, width, height, args.pad)
            if x2 - x1 < args.min_size or y2 - y1 < args.min_size:
                continue
            crop = image.crop((x1, y1, x2, y2))
            class_dir = images_out / class_name
            class_dir.mkdir(parents=True, exist_ok=True)
            out_path = class_dir / f"{label_path.stem}_{box_idx:03d}.png"
            crop.save(out_path)
            counts[class_name] += 1
            manifest.append(
                {
                    "cutout_path": str(out_path),
                    "class_name": class_name,
                    "class_id": str(class_id),
                    "source_image": str(image_path),
                    "source_label": str(label_path),
                    "bbox_xyxy": json.dumps([x1, y1, x2, y2]),
                    "width_px": str(x2 - x1),
                    "height_px": str(y2 - y1),
                    "split": args.split,
                }
            )

    args.out_dir.mkdir(parents=True, exist_ok=True)
    manifest_json = args.out_dir / "manifest.json"
    manifest_csv = args.out_dir / "manifest.csv"
    manifest_json.write_text(json.dumps({"counts": counts, "items": manifest}, indent=2), encoding="utf-8")
    with manifest_csv.open("w", encoding="utf-8", newline="") as handle:
        fieldnames = ["cutout_path", "class_name", "class_id", "source_image", "source_label", "bbox_xyxy", "width_px", "height_px", "split"]
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(manifest)
    save_contact_sheet(manifest[:64], args.out_dir / "contact_sheet.png")

    summary = args.out_dir / "README.md"
    summary.write_text(
        "\n".join(
            [
                "# VisDrone Cutouts For Isaac",
                "",
                f"Source: `{args.data_yaml}` / split `{args.split}`",
                f"Total cutouts: {len(manifest)}",
                "",
                "| Class | Count |",
                "| --- | ---: |",
                *[f"| {name} | {counts[name]} |" for name in sorted(counts)],
                "",
                "Use these crops as actor billboards in the real-Cesium MarineCity overlay before rerunning detector smoke tests.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    print(manifest_json)
    print(manifest_csv)
    print(summary)


if __name__ == "__main__":
    main()
