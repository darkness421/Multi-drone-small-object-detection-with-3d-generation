"""Placeholder boundary for external 3D reconstruction toolchains.

The actual NeRF, Instant-NGP, Mip-NeRF 360, and 3DGS training jobs are expected
to run through their upstream repositories or containers. This module records
the normalized command contract used by tmux scripts and experiment manifests.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description="External 3D generator command contract placeholder.")
    parser.add_argument("--method", required=True)
    parser.add_argument("--scene", required=True)
    parser.add_argument("--data", required=True)
    parser.add_argument("--checkpoint", default=None)
    parser.add_argument("--render", action="store_true")
    parser.add_argument("--out", default=None)
    parser.add_argument(
        "--allow-placeholder",
        action="store_true",
        help="Write the placeholder command-contract JSON. Do not use for paper-facing 3D metrics.",
    )
    args = parser.parse_args()
    if not args.allow_placeholder:
        message = (
            "generative3d.external_runner is only a command-contract placeholder. "
            "Install/connect an upstream NeRF/Instant-NGP/Mip-NeRF/3DGS runner, "
            "or rerun with --allow-placeholder for a non-paper smoke artifact."
        )
        print(message, file=sys.stderr)
        raise SystemExit(2)
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
