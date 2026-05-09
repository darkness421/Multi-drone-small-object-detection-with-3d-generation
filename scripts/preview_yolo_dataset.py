"""Render an Ultralytics YOLO dataset split as a visible HTML preview."""

from __future__ import annotations

import argparse
import csv
import html
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from runtime.config import load_config, resolve_path


IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff", ".svg"}


@dataclass(slots=True)
class YoloPreviewResult:
    index_html: Path
    summary_csv: Path
    image_count: int
    box_count: int


@dataclass(slots=True)
class YoloBox:
    class_id: int
    class_name: str
    cx: float
    cy: float
    width: float
    height: float


def _dataset_root(config: dict[str, Any], data_yaml: Path) -> Path:
    root = Path(str(config.get("path", data_yaml.parent)))
    return root if root.is_absolute() else resolve_path(root)


def _split_dir(root: Path, split_value: str | None, split: str) -> Path:
    if split_value:
        split_path = Path(str(split_value))
        return split_path if split_path.is_absolute() else root / split_path
    return root / "images" / split


def _label_dir_for(image_dir: Path) -> Path:
    parts = list(image_dir.parts)
    for idx, part in enumerate(parts):
        if part.lower() == "images":
            parts[idx] = "labels"
            return Path(*parts)
    return image_dir.parent.parent / "labels" / image_dir.name


def _names(config: dict[str, Any]) -> dict[int, str]:
    names = config.get("names", {})
    if isinstance(names, list):
        return {idx: str(name) for idx, name in enumerate(names)}
    if isinstance(names, dict):
        return {int(idx): str(name) for idx, name in names.items()}
    return {}


def _image_files(image_dir: Path) -> list[Path]:
    if not image_dir.exists():
        return []
    return sorted(path for path in image_dir.rglob("*") if path.is_file() and path.suffix.lower() in IMAGE_SUFFIXES)


def _parse_label_file(label_path: Path, names: dict[int, str]) -> list[YoloBox]:
    if not label_path.exists():
        return []
    boxes: list[YoloBox] = []
    for line in label_path.read_text(encoding="utf-8").splitlines():
        parts = line.strip().split()
        if len(parts) < 5:
            continue
        try:
            class_id = int(float(parts[0]))
            cx, cy, width, height = [float(value) for value in parts[1:5]]
        except ValueError:
            continue
        boxes.append(
            YoloBox(
                class_id=class_id,
                class_name=names.get(class_id, f"class_{class_id}"),
                cx=cx,
                cy=cy,
                width=width,
                height=height,
            )
        )
    return boxes


def _box_style(box: YoloBox) -> str:
    left = max(0.0, (box.cx - box.width / 2.0) * 100.0)
    top = max(0.0, (box.cy - box.height / 2.0) * 100.0)
    width = max(0.1, box.width * 100.0)
    height = max(0.1, box.height * 100.0)
    return f"left:{left:.4f}%;top:{top:.4f}%;width:{width:.4f}%;height:{height:.4f}%;"


def _write_summary(rows: list[dict[str, object]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["image_path", "label_path", "class_id", "class_name", "cx", "cy", "width", "height"],
        )
        writer.writeheader()
        writer.writerows(rows)


def render_yolo_dataset_preview(
    data_yaml: str | Path,
    out_dir: str | Path,
    *,
    split: str = "train",
    limit: int = 60,
) -> YoloPreviewResult:
    """Write an HTML preview for one YOLO dataset split."""

    data_yaml = resolve_path(data_yaml)
    config = load_config(data_yaml)
    root = _dataset_root(config, data_yaml)
    image_dir = _split_dir(root, config.get(split), split)
    label_dir = _label_dir_for(image_dir)
    names = _names(config)
    images = _image_files(image_dir)[: max(0, limit)]

    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    cards: list[str] = []
    summary_rows: list[dict[str, object]] = []
    box_count = 0
    for image_path in images:
        label_path = label_dir / f"{image_path.stem}.txt"
        boxes = _parse_label_file(label_path, names)
        box_count += len(boxes)
        box_markup = []
        for box in boxes:
            box_markup.append(
                "\n".join(
                    [
                        f'<div class="box" style="{_box_style(box)}">',
                        f'  <span>{html.escape(box.class_name)}</span>',
                        "</div>",
                    ]
                )
            )
            summary_rows.append(
                {
                    "image_path": str(image_path),
                    "label_path": str(label_path),
                    "class_id": box.class_id,
                    "class_name": box.class_name,
                    "cx": f"{box.cx:.6f}",
                    "cy": f"{box.cy:.6f}",
                    "width": f"{box.width:.6f}",
                    "height": f"{box.height:.6f}",
                }
            )
        cards.append(
            "\n".join(
                [
                    '<section class="card">',
                    f"<h2>{html.escape(image_path.name)}</h2>",
                    '<div class="frame">',
                    f'<img src="{html.escape(image_path.resolve().as_uri())}" alt="{html.escape(image_path.name)}">',
                    *box_markup,
                    "</div>",
                    f"<p>{len(boxes)} boxes | {html.escape(str(label_path))}</p>",
                    "</section>",
                ]
            )
        )

    if not cards:
        cards.append(
            "\n".join(
                [
                    '<section class="card">',
                    "<h2>No images found</h2>",
                    f"<p>Checked image directory: {html.escape(str(image_dir))}</p>",
                    f"<p>Checked label directory: {html.escape(str(label_dir))}</p>",
                    "</section>",
                ]
            )
        )

    summary_csv = out_dir / "summary.csv"
    _write_summary(summary_rows, summary_csv)
    index_html = out_dir / "index.html"
    index_html.write_text(
        "\n".join(
            [
                "<!doctype html>",
                '<html lang="en">',
                "<head>",
                '<meta charset="utf-8">',
                '<meta name="viewport" content="width=device-width, initial-scale=1">',
                "<title>CoM3D-ACE YOLO Dataset Preview</title>",
                "<style>",
                "body{font-family:Segoe UI,Arial,sans-serif;margin:24px;background:#101214;color:#f8fafc}",
                "h1{font-size:24px;margin:0 0 8px}",
                "h2{font-size:14px;margin:0 0 10px;color:#cbd5e1}",
                ".meta,p{color:#94a3b8;font-size:13px}",
                ".grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(360px,1fr));gap:18px}",
                ".card{background:#1b1f26;border:1px solid #334155;border-radius:8px;padding:14px}",
                ".frame{position:relative;width:100%;aspect-ratio:4/3;background:#0f172a;overflow:hidden;border-radius:6px}",
                ".frame img{width:100%;height:100%;object-fit:contain;display:block}",
                ".box{position:absolute;border:2px solid #f59e0b;box-sizing:border-box}",
                ".box span{position:absolute;left:0;top:0;transform:translateY(-100%);background:#f59e0b;color:#111827;font-size:11px;padding:2px 4px;white-space:nowrap}",
                "a{color:#7dd3fc}",
                "</style>",
                "</head>",
                "<body>",
                "<h1>CoM3D-ACE YOLO Dataset Preview</h1>",
                f'<p class="meta">data_yaml={html.escape(str(data_yaml))} | split={html.escape(split)} | images={len(images)} | boxes={box_count} | <a href="summary.csv">summary.csv</a></p>',
                '<main class="grid">',
                *cards,
                "</main>",
                "</body>",
                "</html>",
                "",
            ]
        ),
        encoding="utf-8",
    )
    return YoloPreviewResult(index_html=index_html, summary_csv=summary_csv, image_count=len(images), box_count=box_count)


def main() -> None:
    parser = argparse.ArgumentParser(description="Render YOLO dataset labels as an HTML preview.")
    parser.add_argument("--data-yaml", default="configs/detector/visdrone_yolo_data.yaml")
    parser.add_argument("--split", default="train", choices=["train", "val", "test"])
    parser.add_argument("--limit", type=int, default=60)
    parser.add_argument("--out-dir", default="outputs/preview/yolo_dataset")
    args = parser.parse_args()

    result = render_yolo_dataset_preview(args.data_yaml, args.out_dir, split=args.split, limit=args.limit)
    print(f"Wrote preview: {result.index_html}")
    print(f"Wrote summary: {result.summary_csv}")
    print(f"Images: {result.image_count}, boxes: {result.box_count}")


if __name__ == "__main__":
    main()
