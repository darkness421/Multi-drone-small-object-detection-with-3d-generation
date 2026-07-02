"""Train CSFPR-RTDETR under the paper consistency protocol.

This is intentionally separate from the external checkpoint eval script. The
checkpoint eval is useful as a sanity row, while this script is for fairer
same-data, same-resolution, multi-seed reproduction attempts.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", default="external/CSFPR-RTDETR")
    parser.add_argument("--data", default="external/CSFPR-RTDETR/dataset/visdrone_local.yaml")
    parser.add_argument("--cfg", default="external/CSFPR-RTDETR/ultralytics/cfg/modelY/CSFPR-RTDETR.yaml")
    parser.add_argument("--project", default="outputs/detectors/related_work_consistency/csfpr_rtdetr")
    parser.add_argument("--name", default="csfpr_rtdetr_1280_seed42")
    parser.add_argument("--imgsz", type=int, default=1280)
    parser.add_argument("--epochs", type=int, default=100)
    parser.add_argument("--batch", type=int, default=1)
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--device", default="0")
    parser.add_argument("--patience", type=int, default=5)
    parser.add_argument("--seed", type=int, default=42)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    repo = Path(args.repo).resolve()
    cfg = Path(args.cfg).resolve()
    data = Path(args.data).resolve()
    project = Path(args.project).resolve()

    if not repo.exists():
        raise SystemExit(f"Missing CSFPR repo: {repo}")
    if not cfg.exists():
        raise SystemExit(f"Missing CSFPR config: {cfg}")
    if not data.exists():
        raise SystemExit(f"Missing CSFPR data yaml: {data}")

    sys.path.insert(0, str(repo))
    from ultralytics import RTDETR  # noqa: PLC0415

    model = RTDETR(str(cfg))
    model.train(
        data=str(data),
        imgsz=args.imgsz,
        epochs=args.epochs,
        batch=args.batch,
        workers=args.workers,
        device=args.device,
        project=str(project),
        name=args.name,
        patience=args.patience,
        seed=args.seed,
        exist_ok=True,
        pretrained=False,
    )


if __name__ == "__main__":
    main()
