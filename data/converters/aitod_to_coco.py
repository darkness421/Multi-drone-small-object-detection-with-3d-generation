"""Normalize AI-TOD COCO-style annotations for CoM3D-ACE.

AI-TOD is already distributed in a COCO-like format in common releases. This
module keeps the schema explicit and ensures optional CoM3D fields exist.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

try:
    from .common import write_json
except ImportError:
    from common import write_json


def normalize_aitod(coco_json: str | Path) -> dict[str, object]:
    payload = json.loads(Path(coco_json).read_text(encoding="utf-8"))
    for image in payload.get("images", []):
        image.setdefault("metadata", {})
    for annotation in payload.get("annotations", []):
        annotation.setdefault("object_id", None)
        annotation.setdefault("camera_pose", None)
        annotation.setdefault("depth_path", None)
        annotation.setdefault("metadata", {})
    return payload


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    write_json(normalize_aitod(args.input), args.out)


if __name__ == "__main__":
    main()
