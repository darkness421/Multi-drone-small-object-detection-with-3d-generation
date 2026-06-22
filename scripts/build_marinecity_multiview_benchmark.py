"""Build a Marine City multi-angle benchmark manifest from exported frames."""

from __future__ import annotations

import argparse
import json

from generative3d.benchmark_manifest import build_multiview_benchmark, write_benchmark


def parse_angles(value: str) -> list[str]:
    return [part.strip() for part in value.split(",") if part.strip()]


def main() -> None:
    parser = argparse.ArgumentParser(description="Create Marine City multi-angle benchmark splits.")
    parser.add_argument("--input", required=True, help="Simulation export JSON, frame list JSON, or single-scene view JSON.")
    parser.add_argument("--out", default="outputs/experiments/marinecity_multiview_benchmark.json")
    parser.add_argument("--val-angles", default="side_view")
    parser.add_argument("--test-angles", default="rear_oblique,right_oblique")
    args = parser.parse_args()

    frames = build_multiview_benchmark(
        args.input,
        val_angles=parse_angles(args.val_angles),
        test_angles=parse_angles(args.test_angles),
    )
    payload = write_benchmark(frames, args.out)
    print(json.dumps(payload["summary"], indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
