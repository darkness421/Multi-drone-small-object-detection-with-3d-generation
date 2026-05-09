"""Create a visible HTML preview for EvidenceToken JSONL outputs."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from evidence.visualization import render_preview_from_jsonl


def main() -> None:
    parser = argparse.ArgumentParser(description="Render EvidenceToken JSONL as an HTML preview.")
    parser.add_argument("--tokens", default="outputs/evidence/tokens.jsonl")
    parser.add_argument("--out-dir", default="outputs/preview/evidence_tokens")
    args = parser.parse_args()

    result = render_preview_from_jsonl(args.tokens, args.out_dir)
    print(f"Wrote preview: {result.index_html}")
    print(f"Wrote summary: {result.summary_csv}")
    print(f"Images: {result.image_count}, tokens: {result.token_count}")


if __name__ == "__main__":
    main()
