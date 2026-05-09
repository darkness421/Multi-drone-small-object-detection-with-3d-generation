"""HTML preview generation for EvidenceToken outputs.

The preview is intentionally dependency-light: it writes an HTML page with
positioned bounding boxes over the original images when available, and falls
back to a blank canvas when only token metadata is present.
"""

from __future__ import annotations

import csv
import html
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from .io import load_tokens_jsonl
from .token import EvidenceToken


@dataclass(slots=True)
class PreviewResult:
    index_html: Path
    summary_csv: Path
    image_count: int
    token_count: int


def _image_path_for_token(token: EvidenceToken) -> Path | None:
    candidates = [
        token.metadata.get("image_path"),
        token.metadata.get("source_image"),
        token.metadata.get("frame_path"),
        token.image_id,
    ]
    for value in candidates:
        if not value:
            continue
        path = Path(str(value))
        if path.exists() and path.is_file():
            return path.resolve()
    return None


def _group_key(token: EvidenceToken) -> str:
    image_path = _image_path_for_token(token)
    if image_path is not None:
        return str(image_path)
    return token.image_id


def _infer_canvas_size(tokens: list[EvidenceToken]) -> tuple[int, int]:
    max_x = 640.0
    max_y = 480.0
    for token in tokens:
        x, y, w, h = token.bbox_2d
        max_x = max(max_x, x + w + 16)
        max_y = max(max_y, y + h + 16)
    return int(max_x), int(max_y)


def _try_image_size(image_path: Path | None, fallback_tokens: list[EvidenceToken]) -> tuple[int, int]:
    if image_path is not None:
        try:
            import cv2

            image = cv2.imread(str(image_path))
            if image is not None:
                height, width = image.shape[:2]
                return int(width), int(height)
        except Exception:
            pass
        try:
            from PIL import Image

            with Image.open(image_path) as image:
                return int(image.width), int(image.height)
        except Exception:
            pass
    return _infer_canvas_size(fallback_tokens)


def _class_label(token: EvidenceToken) -> str:
    if token.metadata.get("class_name"):
        return str(token.metadata["class_name"])
    if token.class_id is not None:
        return f"class_{token.class_id}"
    return "object"


def _box_style(token: EvidenceToken, width: int, height: int) -> str:
    x, y, w, h = token.bbox_2d
    left = max(0.0, x / max(width, 1) * 100.0)
    top = max(0.0, y / max(height, 1) * 100.0)
    box_w = max(0.1, w / max(width, 1) * 100.0)
    box_h = max(0.1, h / max(height, 1) * 100.0)
    return f"left:{left:.4f}%;top:{top:.4f}%;width:{box_w:.4f}%;height:{box_h:.4f}%;"


def _write_summary(tokens: list[EvidenceToken], out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "token_id",
                "image_id",
                "uav_id",
                "timestamp",
                "bbox_2d",
                "class_label",
                "confidence",
                "uncertainty",
                "image_path",
                "crop_path",
            ],
        )
        writer.writeheader()
        for token in tokens:
            image_path = _image_path_for_token(token)
            writer.writerow(
                {
                    "token_id": token.token_id,
                    "image_id": token.image_id,
                    "uav_id": token.uav_id,
                    "timestamp": token.timestamp,
                    "bbox_2d": token.bbox_2d,
                    "class_label": _class_label(token),
                    "confidence": f"{token.confidence:.4f}",
                    "uncertainty": f"{token.uncertainty:.4f}",
                    "image_path": str(image_path) if image_path else "",
                    "crop_path": token.metadata.get("crop_path", ""),
                }
            )


def render_preview_html(tokens: Iterable[EvidenceToken], out_dir: str | Path) -> PreviewResult:
    """Write an HTML preview page and CSV summary for evidence tokens."""

    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    tokens = list(tokens)
    grouped: dict[str, list[EvidenceToken]] = defaultdict(list)
    for token in tokens:
        grouped[_group_key(token)].append(token)

    cards: list[str] = []
    for group_key, group_tokens in sorted(grouped.items()):
        image_path = _image_path_for_token(group_tokens[0])
        width, height = _try_image_size(image_path, group_tokens)
        if image_path is not None:
            image_html = f'<img src="{html.escape(image_path.as_uri())}" alt="{html.escape(group_key)}">'
        else:
            image_html = '<div class="blank">source image unavailable</div>'
        boxes = []
        for token in group_tokens:
            label = f"{_class_label(token)} {token.confidence:.2f} / U {token.uncertainty:.2f}"
            boxes.append(
                "\n".join(
                    [
                        f'<div class="box" style="{_box_style(token, width, height)}">',
                        f'  <span>{html.escape(label)}</span>',
                        "</div>",
                    ]
                )
            )
        cards.append(
            "\n".join(
                [
                    '<section class="card">',
                    f"<h2>{html.escape(group_key)}</h2>",
                    f'<div class="frame" style="max-width:{width}px;aspect-ratio:{width}/{height};">',
                    image_html,
                    *boxes,
                    "</div>",
                    f"<p>{len(group_tokens)} evidence tokens</p>",
                    "</section>",
                ]
            )
        )

    if not cards:
        cards.append('<section class="card"><h2>No evidence tokens found</h2></section>')

    summary_csv = out_dir / "summary.csv"
    _write_summary(tokens, summary_csv)
    index_html = out_dir / "index.html"
    index_html.write_text(
        "\n".join(
            [
                "<!doctype html>",
                '<html lang="en">',
                "<head>",
                '<meta charset="utf-8">',
                '<meta name="viewport" content="width=device-width, initial-scale=1">',
                "<title>CoM3D-ACE Evidence Preview</title>",
                "<style>",
                "body{font-family:Segoe UI,Arial,sans-serif;margin:24px;background:#111;color:#eee}",
                "h1{font-size:24px;margin:0 0 8px}",
                "h2{font-size:14px;font-weight:600;margin:0 0 10px;color:#cbd5e1}",
                ".meta{color:#94a3b8;margin:0 0 18px}",
                ".grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(360px,1fr));gap:18px}",
                ".card{background:#1b1d22;border:1px solid #333842;border-radius:8px;padding:14px}",
                ".frame{position:relative;width:100%;background:#0b0d10;overflow:hidden;border-radius:6px}",
                ".frame img{width:100%;height:100%;object-fit:contain;display:block}",
                ".blank{display:flex;align-items:center;justify-content:center;width:100%;height:100%;color:#64748b}",
                ".box{position:absolute;border:2px solid #22c55e;box-sizing:border-box}",
                ".box span{position:absolute;left:0;top:0;transform:translateY(-100%);background:#22c55e;color:#06120a;font-size:11px;padding:2px 4px;white-space:nowrap}",
                "p{color:#94a3b8;margin:10px 0 0;font-size:13px}",
                "a{color:#7dd3fc}",
                "</style>",
                "</head>",
                "<body>",
                "<h1>CoM3D-ACE Evidence Preview</h1>",
                f'<p class="meta">{len(tokens)} tokens across {len(grouped)} images. Summary: <a href="summary.csv">summary.csv</a></p>',
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
    return PreviewResult(index_html=index_html, summary_csv=summary_csv, image_count=len(grouped), token_count=len(tokens))


def render_preview_from_jsonl(tokens_jsonl: str | Path, out_dir: str | Path) -> PreviewResult:
    """Load EvidenceToken JSONL and write the preview artifacts."""

    return render_preview_html(load_tokens_jsonl(tokens_jsonl), out_dir)
