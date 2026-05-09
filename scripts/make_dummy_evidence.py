"""Create deterministic dummy EvidenceToken JSONL for pipeline smoke runs."""

from __future__ import annotations

import argparse
from pathlib import Path

from evidence import EvidenceToken, save_tokens_jsonl
from evidence.uncertainty import uncertainty_score


def make_dummy_tokens() -> list[EvidenceToken]:
    return [
        EvidenceToken(
            token_id="scene001_uav01_obj001",
            image_id="scene001_uav01_t000",
            uav_id="uav_01",
            timestamp=0.0,
            bbox_2d=[100.0, 120.0, 26.0, 18.0],
            class_logits=[2.5, 1.2, 0.1],
            confidence=0.72,
            uncertainty=uncertainty_score([2.5, 1.2, 0.1]),
            crop_feature=[0.10, 0.20, 0.30],
            resolution_level="p3",
            uav_pose=[0.0, 0.0, 80.0],
            depth_value=80.0,
            metadata={"center_3d": [0.0, 0.0, 0.0], "visibility_score": 0.7},
        ),
        EvidenceToken(
            token_id="scene001_uav02_obj001",
            image_id="scene001_uav02_t000",
            uav_id="uav_02",
            timestamp=0.0,
            bbox_2d=[132.0, 122.0, 22.0, 16.0],
            class_logits=[2.2, 1.4, 0.2],
            confidence=0.68,
            uncertainty=uncertainty_score([2.2, 1.4, 0.2]),
            crop_feature=[0.11, 0.19, 0.31],
            resolution_level="p3",
            uav_pose=[10.0, 0.0, 85.0],
            depth_value=82.0,
            metadata={"center_3d": [0.2, 0.0, 0.1], "visibility_score": 0.6},
        ),
        EvidenceToken(
            token_id="scene001_uav03_obj002",
            image_id="scene001_uav03_t000",
            uav_id="uav_03",
            timestamp=0.0,
            bbox_2d=[420.0, 300.0, 12.0, 9.0],
            class_logits=[1.0, 1.1, 1.0],
            confidence=0.38,
            uncertainty=uncertainty_score([1.0, 1.1, 1.0]),
            crop_feature=[0.80, 0.20, 0.10],
            resolution_level="p4",
            uav_pose=[-10.0, 4.0, 100.0],
            depth_value=120.0,
            metadata={"center_3d": [18.0, 4.0, 0.0], "visibility_score": 0.3, "low_resolution_score": 0.8},
        ),
    ]


def main() -> None:
    parser = argparse.ArgumentParser(description="Create dummy EvidenceToken JSONL.")
    parser.add_argument("--out", default="outputs/evidence/dummy_tokens.jsonl")
    args = parser.parse_args()
    save_tokens_jsonl(make_dummy_tokens(), Path(args.out))
    print(f"Wrote dummy evidence tokens to {args.out}")


if __name__ == "__main__":
    main()

