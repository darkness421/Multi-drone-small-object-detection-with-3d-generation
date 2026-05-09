"""YOLO inference entrypoint that writes EvidenceToken JSONL."""

from __future__ import annotations

import argparse
from pathlib import Path

try:
    from .wrappers import UltralyticsWrapper
except ImportError:
    from wrappers import UltralyticsWrapper


def main() -> None:
    parser = argparse.ArgumentParser(description="Run YOLO inference and export EvidenceToken JSONL.")
    parser.add_argument("--weights", default="yolo11n.pt")
    parser.add_argument("--images", default="data/sample_images")
    parser.add_argument("--out-jsonl", default="outputs/evidence/tokens.jsonl")
    parser.add_argument("--crop-dir", default="outputs/crops")
    args = parser.parse_args()

    wrapper = UltralyticsWrapper(args.weights)
    tokens = wrapper.infer_folder_to_jsonl(Path(args.images), Path(args.out_jsonl), crop_dir=args.crop_dir)
    print(f"Wrote {len(tokens)} evidence tokens to {args.out_jsonl}")


if __name__ == "__main__":
    main()
