"""Placeholder boundary for external 3D reconstruction toolchains.

The actual NeRF, Instant-NGP, Mip-NeRF 360, and 3DGS training jobs are expected
to run through their upstream repositories or containers. This module records
the normalized command contract used by tmux scripts and experiment manifests.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description="External 3D generator command contract placeholder.")
    parser.add_argument("--method", required=True)
    parser.add_argument("--scene", required=True)
    parser.add_argument("--data", required=True)
    parser.add_argument("--checkpoint", default=None)
    parser.add_argument("--render", action="store_true")
    parser.add_argument("--out", default=None)
    args = parser.parse_args()
    payload = {
        "status": "placeholder",
        "method": args.method,
        "scene": args.scene,
        "data": args.data,
        "checkpoint": args.checkpoint,
        "mode": "render" if args.render else "train",
        "next": "replace this placeholder with the upstream method command in scripts/ubuntu/train_3d_generators_tmux.sh",
    }
    text = json.dumps(payload, indent=2)
    if args.out:
        out = Path(args.out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text, encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
